from __future__ import annotations

import csv
import json
import os
import tempfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, acquire

SOURCE_ID = "bcra_average_reserve_requirements"
SOURCE_URL = "https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/din1_ser.txt"
LANDING_URL = "https://www.bcra.gob.ar/consulta-de-series-estadisticas-en-formato-txt/"
FIRST_PERIOD = "1985-04"
SERIES = {
    "1554": ("bcra_reserve_requirement_total", "Total"),
    "1555": ("bcra_reserve_requirement_ars", "Pesos"),
    "1556": ("bcra_reserve_requirement_fx", "Moneda extranjera"),
}


def extract(artifact: Artifact) -> list[dict[str, str]]:
    values: dict[str, dict[str, Decimal]] = {code: {} for code in SERIES}
    try:
        with artifact.path.open(encoding="latin-1", errors="replace") as handle:
            for line_number, line in enumerate(handle, start=1):
                parts = line.strip().split(";")
                if len(parts) != 3 or parts[0] not in SERIES:
                    continue
                code, raw_date, raw_value = parts
                try:
                    period = datetime.strptime(raw_date, "%d/%m/%Y").strftime("%Y-%m")
                    value = Decimal(raw_value.replace(",", "."))
                except (ValueError, InvalidOperation) as exc:
                    raise PipelineError(
                        f"encajes BCRA: observación inválida en línea {line_number}"
                    ) from exc
                if period in values[code]:
                    raise PipelineError(f"encajes BCRA: período duplicado {code}/{period}")
                if value < 0 or value > 100:
                    raise PipelineError(f"encajes BCRA: valor fuera de rango {code}/{period}")
                values[code][period] = value
    except OSError as exc:
        raise PipelineError(f"encajes BCRA: no se pudo leer el TXT: {exc}") from exc

    period_sets = {code: set(rows) for code, rows in values.items()}
    if any(not periods for periods in period_sets.values()):
        raise PipelineError("encajes BCRA: faltan una o más series oficiales")
    if len({frozenset(periods) for periods in period_sets.values()}) != 1:
        raise PipelineError("encajes BCRA: el panel Total/Pesos/Moneda extranjera está incompleto")

    periods = sorted(next(iter(period_sets.values())))
    while periods and all(values[code][periods[-1]] == 0 for code in SERIES):
        periods.pop()
    if not periods:
        raise PipelineError("encajes BCRA: la fuente sólo contiene observaciones provisionales")

    records: list[dict[str, str]] = []
    for code, (series_id, _label) in SERIES.items():
        for period in periods:
            records.append({
                "series_id": series_id,
                "period": period,
                "frequency": "monthly",
                "value": format(values[code][period].quantize(Decimal("0.000001")), "f"),
                "unit": "percent",
                "status": "official",
                "source_id": SOURCE_ID,
                "source_url": artifact.url,
                "source_sha256": artifact.sha256,
                "retrieved_at": artifact.retrieved_at,
            })
    return records


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    records.sort(key=lambda row: (row["series_id"], row["period"]))
    keys = [(row["series_id"], row["period"]) for row in records]
    if len(keys) != len(set(keys)):
        raise PipelineError("encajes BCRA: claves duplicadas")

    by_series = {
        series_id: [row for row in records if row["series_id"] == series_id]
        for series_id, _label in SERIES.values()
    }
    if any(len(rows) < 450 or rows[0]["period"] != FIRST_PERIOD for rows in by_series.values()):
        raise PipelineError("encajes BCRA: cobertura histórica inesperada")
    panels = [{row["period"] for row in rows} for rows in by_series.values()]
    if len({frozenset(panel) for panel in panels}) != 1:
        raise PipelineError("encajes BCRA: cobertura desigual entre series")

    target_dir = root / "data" / "processed"
    log_dir = root / "data" / "logs" / "reserve_requirements"
    target_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "reserve_requirements.csv"

    old: dict[tuple[str, str], str] = {}
    if target.exists():
        with target.open(encoding="utf-8", newline="") as handle:
            old = {(row["series_id"], row["period"]): row["value"] for row in csv.DictReader(handle)}
    new = {(row["series_id"], row["period"]): row["value"] for row in records}
    if old.keys() - new.keys():
        raise PipelineError("encajes BCRA: la fuente eliminó observaciones existentes")

    report = {
        "run_id": run_id,
        "rows": len(records),
        "series": len(by_series),
        "min_period": min(row["period"] for row in records),
        "max_period": max(row["period"] for row in records),
        "created": len(new.keys() - old.keys()),
        "deleted": len(old.keys() - new.keys()),
        "modified": sum(old[key] != new[key] for key in old.keys() & new.keys()),
    }

    fd, temporary = tempfile.mkstemp(prefix="reserve-requirements-", suffix=".csv", dir=target_dir)
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

    (log_dir / f"{run_id}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def run(root: Path, source_file: Path | None = None) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifact = acquire(SOURCE_ID, SOURCE_URL, root / "data" / "raw", source_file)
    return promote(extract(artifact), root, run_id)
