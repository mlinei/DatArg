from __future__ import annotations

import csv
import json
import os
import tempfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, acquire

WAGES_URL = "https://www.indec.gob.ar/ftp/cuadros/sociedad/indice_salarios.csv"
SECTORS = {
    "IS_sector_privado_registrado": "private_registered",
    "IS_sector_publico": "public",
    "IS_total_registrado": "total_registered",
    "IS_sector_no_registrado": "private_unregistered",
    "IS_indice_total": "total",
}


def _decimal(raw: str, context: str) -> Decimal:
    try:
        value = Decimal(raw.strip().replace(".", "").replace(",", "."))
    except (InvalidOperation, AttributeError) as exc:
        raise PipelineError(f"salarios: valor inválido en {context}") from exc
    if value <= 0:
        raise PipelineError(f"salarios: valor fuera de rango en {context}")
    return value


def _record(series_id: str, period: str, value: Decimal, unit: str, status: str,
            source_id: str, artifact: Artifact) -> dict[str, str]:
    return {
        "series_id": series_id, "period": period, "frequency": "monthly",
        "value": format(value.quantize(Decimal("0.000001")), "f"), "unit": unit,
        "status": status, "source_id": source_id, "source_url": artifact.url,
        "source_sha256": artifact.sha256, "retrieved_at": artifact.retrieved_at,
    }


def extract(artifact: Artifact) -> list[dict[str, str]]:
    try:
        with artifact.path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter=";"))
    except (OSError, UnicodeError, csv.Error) as exc:
        raise PipelineError(f"salarios: CSV ilegible: {exc}") from exc
    if not rows or set(rows[0]) != {"periodo", *SECTORS}:
        raise PipelineError("salarios: esquema inesperado")
    records: list[dict[str, str]] = []
    for row in rows:
        try:
            day, month, year = (int(part) for part in row["periodo"].split("/"))
            if day != 1: raise ValueError
            period = f"{year:04d}-{month:02d}"
        except (ValueError, AttributeError) as exc:
            raise PipelineError(f"salarios: período inválido: {row.get('periodo')}") from exc
        for column, sector in SECTORS.items():
            raw = row[column].strip()
            if raw.upper() == "NA":
                continue
            records.append(_record(
                f"indec_wage_{sector}_nominal_index", period, _decimal(raw, f"{sector}/{period}"),
                "index_oct_2016_100", "official", "indec_wage_index", artifact,
            ))
    return records


def add_real_indices(records: list[dict[str, str]], inflation_path: Path, artifact: Artifact) -> list[dict[str, str]]:
    if not inflation_path.exists():
        raise PipelineError("salarios: falta data/processed/inflation.csv para calcular salario real")
    with inflation_path.open(encoding="utf-8", newline="") as handle:
        cpi = {row["period"]: Decimal(row["value"]) for row in csv.DictReader(handle)
               if row["series_id"] == "indec_ipc_general_index"}
    base_period = "2016-12"
    if base_period not in cpi:
        raise PipelineError("salarios: IPC base diciembre de 2016 ausente")
    nominal = {(row["series_id"], row["period"]): Decimal(row["value"]) for row in records}
    result = list(records)
    for sector in SECTORS.values():
        nominal_id = f"indec_wage_{sector}_nominal_index"
        base_key = (nominal_id, base_period)
        if base_key not in nominal:
            continue
        base_ratio = nominal[base_key] / cpi[base_period]
        for (series_id, period), wage in nominal.items():
            if series_id != nominal_id or period not in cpi or period < base_period:
                continue
            real = (wage / cpi[period]) / base_ratio * Decimal(100)
            result.append(_record(
                f"indec_wage_{sector}_real_index", period, real, "index_dec_2016_100",
                "calculated", "indec_wage_index_deflated_by_cpi", artifact,
            ))
    return result


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    records.sort(key=lambda row: (row["series_id"], row["period"]))
    keys = [(row["series_id"], row["period"]) for row in records]
    if len(keys) != len(set(keys)):
        raise PipelineError("salarios: claves duplicadas")
    nominal_periods = [row["period"] for row in records if row["series_id"] == "indec_wage_total_nominal_index"]
    if not nominal_periods or nominal_periods[0] != "2016-10":
        raise PipelineError("salarios: cobertura total inesperada")
    target_dir = root / "data" / "processed"; log_dir = root / "data" / "logs" / "wages"
    target_dir.mkdir(parents=True, exist_ok=True); log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "wages.csv"; old: dict[tuple[str, str], str] = {}
    if target.exists():
        with target.open(encoding="utf-8", newline="") as handle:
            old = {(row["series_id"], row["period"]): row["value"] for row in csv.DictReader(handle)}
    new = {(row["series_id"], row["period"]): row["value"] for row in records}
    report = {"run_id": run_id, "rows": len(records), "series": len({row["series_id"] for row in records}),
              "min_period": min(row["period"] for row in records), "max_period": max(row["period"] for row in records),
              "created": len(new.keys() - old.keys()), "deleted": len(old.keys() - new.keys()),
              "modified": sum(old[key] != new[key] for key in old.keys() & new.keys())}
    if old and report["deleted"]:
        raise PipelineError(f"salarios: la nueva fuente elimina {report['deleted']} observaciones")
    fd, temporary = tempfile.mkstemp(prefix="wages-", suffix=".csv", dir=target_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS); writer.writeheader(); writer.writerows(records)
            handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    (log_dir / f"{run_id}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def run(root: Path, source_file: Path | None = None) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifact = acquire("indec_wage_index", WAGES_URL, root / "data" / "raw", source_file)
    records = add_real_indices(extract(artifact), root / "data" / "processed" / "inflation.csv", artifact)
    return promote(records, root, run_id)
