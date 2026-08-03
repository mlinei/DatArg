from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from .inflation import OUTPUT_COLUMNS, PipelineError

START_PERIOD = "2024-01"
CPI_SERIES = "indec_ipc_general_index"
FX_SERIES = "argentinadatos_usd_official_retail_sell"
SOURCE_ID = "datarg_usd_inflation_indec_argentinadatos"
SOURCE_URL = "https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-31"


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise PipelineError(f"inflación en dólares: falta {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise PipelineError(f"inflación en dólares: {path.name} está vacío")
    return rows


def _previous_month(period: str, months: int = 1) -> str:
    year, month = map(int, period.split("-"))
    offset = year * 12 + month - 1 - months
    return f"{offset // 12:04d}-{offset % 12 + 1:02d}"


def calculate(
    inflation_rows: list[dict[str, str]],
    exchange_rows: list[dict[str, str]],
    *,
    source_sha256: str = "calculated",
) -> list[dict[str, str]]:
    cpi = {
        row["period"]: Decimal(row["value"])
        for row in inflation_rows
        if row["series_id"] == CPI_SERIES
    }
    fx_values: dict[str, list[Decimal]] = defaultdict(list)
    for row in exchange_rows:
        if row["series_id"] == FX_SERIES:
            fx_values[row["period"][:7]].append(Decimal(row["value"]))
    monthly_fx = {
        period: sum(values, Decimal(0)) / Decimal(len(values))
        for period, values in fx_values.items()
        if values
    }
    common = sorted(set(cpi) & set(monthly_fx))
    if START_PERIOD not in common:
        raise PipelineError("inflación en dólares: no existe la base enero de 2024")
    if any(cpi[period] <= 0 or monthly_fx[period] <= 0 for period in common):
        raise PipelineError("inflación en dólares: IPC o tipo de cambio no positivo")

    usd_level = {period: cpi[period] / monthly_fx[period] for period in common}
    base = usd_level[START_PERIOD]
    retrieved_at = max(
        (row.get("retrieved_at", "") for row in inflation_rows + exchange_rows),
        default="",
    ) or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def record(series_id: str, period: str, value: Decimal, unit: str) -> dict[str, str]:
        return {
            "series_id": series_id,
            "period": period,
            "frequency": "monthly",
            "value": format(value.quantize(Decimal("0.000001")), "f"),
            "unit": unit,
            "status": "calculated",
            "source_id": SOURCE_ID,
            "source_url": SOURCE_URL,
            "source_sha256": source_sha256,
            "retrieved_at": retrieved_at,
        }

    records: list[dict[str, str]] = []
    for period in common:
        if period < START_PERIOD:
            continue
        records.append(record(
            "datarg_usd_inflation_index_jan_2024",
            period,
            usd_level[period] / base * 100,
            "index_jan_2024_100",
        ))
        previous = _previous_month(period)
        if previous in usd_level:
            records.append(record(
                "datarg_usd_inflation_mom",
                period,
                (usd_level[period] / usd_level[previous] - 1) * 100,
                "percent_change",
            ))
        previous_year = _previous_month(period, 12)
        if previous_year in usd_level:
            records.append(record(
                "datarg_usd_inflation_yoy",
                period,
                (usd_level[period] / usd_level[previous_year] - 1) * 100,
                "percent_change",
            ))
    if not records:
        raise PipelineError("inflación en dólares: cálculo sin observaciones")
    return sorted(records, key=lambda row: (row["series_id"], row["period"]))


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    target_dir = root / "data" / "processed"
    log_dir = root / "data" / "logs" / "usd_inflation"
    target_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "usd_inflation.csv"
    old_rows = _read_rows(target) if target.exists() else []
    old = {(row["series_id"], row["period"]): row["value"] for row in old_rows}
    new = {(row["series_id"], row["period"]): row["value"] for row in records}
    report = {
        "run_id": run_id,
        "created": len(new.keys() - old.keys()),
        "deleted": len(old.keys() - new.keys()),
        "modified": sum(old[key] != new[key] for key in old.keys() & new.keys()),
        "rows": len(records),
        "series": len({row["series_id"] for row in records}),
        "min_period": min(row["period"] for row in records),
        "max_period": max(row["period"] for row in records),
    }
    if old and report["deleted"]:
        raise PipelineError(
            f"inflación en dólares: la nueva versión elimina {report['deleted']} observaciones"
        )
    fd, temporary = tempfile.mkstemp(prefix="usd-inflation-", suffix=".csv", dir=target_dir)
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
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def run(root: Path) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    inflation_path = root / "data" / "processed" / "inflation.csv"
    exchange_path = root / "data" / "processed" / "exchange_rates.csv"
    digest = hashlib.sha256(inflation_path.read_bytes() + exchange_path.read_bytes()).hexdigest()
    records = calculate(_read_rows(inflation_path), _read_rows(exchange_path), source_sha256=digest)
    return promote(records, root, run_id)
