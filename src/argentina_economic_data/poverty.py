from __future__ import annotations

import csv
import json
import os
import re
import tempfile
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd

from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, acquire

POVERTY_URL = "https://www.indec.gob.ar/ftp/cuadros/sociedad/cuadros_informe_pobreza_03_26.xls"

GEOGRAPHIES = {
    "total 31 aglomerados urbanos": "total_31_agglomerates",
    "gran buenos aires": "greater_buenos_aires",
    "cuyo": "cuyo",
    "noreste": "northeast",
    "noroeste": "northwest",
    "pampeana": "pampean",
    "patagonia": "patagonia",
}


def _clean_label(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode().lower()
    text = re.sub(r"\s*\([^)]*\)", "", text)
    return " ".join(text.split())


def _period(value: object) -> str:
    text = _clean_label(value)
    match = re.search(r"([12])(?:er|do|o)?[^a-z0-9]*semestre\s*(20\d{2})", text)
    if not match:
        match = re.search(r"([12])\s*semestre\s*(20\d{2})", text)
    if not match:
        raise PipelineError(f"pobreza: período desconocido {value!r}")
    return f"{match.group(2)}-S{match.group(1)}"


def _number(value: object, context: str) -> Decimal:
    if pd.isna(value):
        raise PipelineError(f"pobreza: valor ausente en {context}")
    try:
        result = Decimal(str(value).strip().replace(",", "."))
    except InvalidOperation as exc:
        raise PipelineError(f"pobreza: valor inválido en {context}: {value!r}") from exc
    if not Decimal("0") <= result <= Decimal("100"):
        raise PipelineError(f"pobreza: porcentaje fuera de rango en {context}")
    return result


def _record(series_id: str, period: str, value: Decimal, artifact: Artifact) -> dict[str, str]:
    return {
        "series_id": series_id,
        "period": period,
        "frequency": "semiannual",
        "value": format(value.quantize(Decimal("0.000001")), "f"),
        "unit": "percent_of_persons",
        "status": "official",
        "source_id": artifact.source_id,
        "source_url": artifact.url,
        "source_sha256": artifact.sha256,
        "retrieved_at": artifact.retrieved_at,
    }


def _table_records(sheet: pd.DataFrame, indicator: str, artifact: Artifact) -> list[dict[str, str]]:
    if sheet.shape[0] < 45 or sheet.shape[1] < 70:
        raise PipelineError(f"pobreza {indicator}: dimensiones inesperadas {sheet.shape}")
    headers: list[tuple[int, str]] = []
    for column in range(1, sheet.shape[1]):
        raw = sheet.iat[2, column]
        if not pd.isna(raw):
            headers.append((column, _period(raw)))
    periods = [period for _, period in headers]
    expected = [f"{year}-S{semester}" for year in range(2016, 2026) for semester in (1, 2) if not (year == 2016 and semester == 1)]
    if periods != expected:
        raise PipelineError(f"pobreza {indicator}: cobertura inesperada {periods}")

    rows: dict[str, int] = {}
    for row in range(6, sheet.shape[0]):
        label = _clean_label(sheet.iat[row, 0])
        for prefix, geography in GEOGRAPHIES.items():
            if label == prefix:
                rows[geography] = row
    if set(rows) != set(GEOGRAPHIES.values()):
        raise PipelineError(f"pobreza {indicator}: faltan geografías {set(GEOGRAPHIES.values()) - set(rows)}")

    result: list[dict[str, str]] = []
    for geography, row in rows.items():
        series_id = f"indec_{indicator}_persons_{geography}"
        for household_column, period in headers:
            persons_column = household_column + 2
            if persons_column >= sheet.shape[1] or str(sheet.iat[3, persons_column]).strip() != "Personas":
                raise PipelineError(f"pobreza {indicator}: columna Personas ausente para {period}")
            value = _number(sheet.iat[row, persons_column], f"{series_id}/{period}")
            result.append(_record(series_id, period, value, artifact))
    return result


def extract(artifact: Artifact) -> list[dict[str, str]]:
    try:
        poverty = pd.read_excel(artifact.path, sheet_name="Cuadro 4.3", header=None)
        indigence = pd.read_excel(artifact.path, sheet_name="Cuadro 4.4", header=None)
    except Exception as exc:
        raise PipelineError(f"pobreza: no se encontraron las hojas históricas: {exc}") from exc
    records = _table_records(poverty, "poverty", artifact) + _table_records(indigence, "indigence", artifact)
    keys = [(record["series_id"], record["period"]) for record in records]
    if len(keys) != len(set(keys)):
        raise PipelineError("pobreza: claves duplicadas")
    return records


def _existing(path: Path) -> dict[tuple[str, str], str]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        return {(r["series_id"], r["period"]): r["value"] for r in csv.DictReader(handle)}


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    records.sort(key=lambda row: (row["series_id"], row["period"]))
    target_dir = root / "data" / "processed"
    log_dir = root / "data" / "logs" / "poverty"
    target_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "poverty.csv"
    old = _existing(target)
    new = {(r["series_id"], r["period"]): r["value"] for r in records}
    report = {
        "run_id": run_id, "created": len(new.keys() - old.keys()),
        "deleted": len(old.keys() - new.keys()),
        "modified": sum(old[k] != new[k] for k in old.keys() & new.keys()),
        "rows": len(records), "series": len({r["series_id"] for r in records}),
        "min_period": min(r["period"] for r in records), "max_period": max(r["period"] for r in records),
        "coverage_warnings": {
            "2019-S2": "No incluye Gran Resistencia.",
            "2020-S2": "No incluye Ushuaia-Río Grande.",
        },
    }
    if old and report["deleted"]:
        raise PipelineError(f"pobreza: la nueva versión elimina {report['deleted']} observaciones")
    fd, temporary = tempfile.mkstemp(prefix="poverty-", suffix=".csv", dir=target_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader()
            writer.writerows(records)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    (log_dir / f"{run_id}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def run(root: Path, source_file: Path | None = None) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifact = acquire("indec_poverty", POVERTY_URL, root / "data" / "raw", source_file)
    return promote(extract(artifact), root, run_id)
