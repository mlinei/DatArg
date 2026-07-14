from __future__ import annotations

import csv
import json
import os
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, acquire

START_TIMESTAMP = 1546300800  # 2019-01-01 UTC


def source_url() -> str:
    end = int(datetime.now(timezone.utc).timestamp()) + 86400
    return ("https://query2.finance.yahoo.com/v8/finance/chart/%5EMERV"
            f"?period1={START_TIMESTAMP}&period2={end}&interval=1d&events=history")


def extract_ars(artifact: Artifact) -> dict[str, Decimal]:
    try:
        payload = json.loads(artifact.path.read_text(encoding="utf-8"))
        chart = payload["chart"]["result"][0]
        timestamps = chart["timestamp"]
        closes = chart["indicators"]["quote"][0]["close"]
    except Exception as exc:
        raise PipelineError(f"Merval: respuesta histórica inválida: {exc}") from exc
    if chart.get("meta", {}).get("symbol") != "^MERV" or len(timestamps) != len(closes):
        raise PipelineError("Merval: metadatos o dimensiones inesperadas")
    result: dict[str, Decimal] = {}
    for timestamp, close in zip(timestamps, closes):
        if close is None: continue
        period = datetime.fromtimestamp(timestamp, timezone.utc).date().isoformat()
        value = Decimal(str(close))
        if value <= 0: raise PipelineError(f"Merval: cierre inválido en {period}")
        result[period] = value
    return result


def extract_mep(path: Path) -> dict[str, Decimal]:
    if not path.exists():
        raise PipelineError("Merval: falta data/processed/exchange_rates.csv")
    with path.open(encoding="utf-8", newline="") as handle:
        result = {row["period"]: Decimal(row["value"]) for row in csv.DictReader(handle)
                  if row["series_id"] == "argentinadatos_usd_mep_sell"}
    if not result: raise PipelineError("Merval: serie MEP ausente")
    return result


def calculate(ars: dict[str, Decimal], mep: dict[str, Decimal], artifact: Artifact) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for period in sorted(ars.keys() & mep.keys()):
        if period < "2019-01-11": continue
        if mep[period] <= 0: raise PipelineError(f"Merval: MEP inválido en {period}")
        value = ars[period] / mep[period]
        if value < Decimal(10) or value > Decimal(100000):
            raise PipelineError(f"Merval: nivel USD fuera de rango en {period}")
        records.append({
            "series_id": "datarg_sp_merval_mep_usd", "period": period, "frequency": "daily",
            "value": format(value.quantize(Decimal("0.000001")), "f"), "unit": "usd_index_points",
            "status": "calculated", "source_id": "yahoo_sp_merval_divided_by_argentinadatos_mep",
            "source_url": artifact.url, "source_sha256": artifact.sha256,
            "retrieved_at": artifact.retrieved_at,
        })
    if not records or records[0]["period"] > "2019-01-15":
        raise PipelineError("Merval: cobertura inicial inesperada")
    return records


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    keys = [row["period"] for row in records]
    if len(keys) != len(set(keys)): raise PipelineError("Merval: fechas duplicadas")
    target_dir = root / "data" / "processed"; log_dir = root / "data" / "logs" / "markets"
    target_dir.mkdir(parents=True, exist_ok=True); log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "markets.csv"; old: dict[str, str] = {}
    if target.exists():
        with target.open(encoding="utf-8", newline="") as handle:
            old = {row["period"]: row["value"] for row in csv.DictReader(handle)}
    new = {row["period"]: row["value"] for row in records}
    report = {"run_id": run_id, "rows": len(records), "series": 1, "min_period": keys[0],
              "max_period": keys[-1], "created": len(new.keys() - old.keys()),
              "deleted": len(old.keys() - new.keys()),
              "modified": sum(old[key] != new[key] for key in old.keys() & new.keys())}
    if old and report["deleted"]: raise PipelineError("Merval: la fuente eliminó observaciones")
    fd, temporary = tempfile.mkstemp(prefix="markets-", suffix=".csv", dir=target_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS); writer.writeheader(); writer.writerows(records)
            handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    (log_dir / f"{run_id}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def run(root: Path, source_file: Path | None = None) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifact = acquire("yahoo_sp_merval", source_url(), root / "data" / "raw", source_file)
    records = calculate(extract_ars(artifact), extract_mep(root / "data" / "processed" / "exchange_rates.csv"), artifact)
    return promote(records, root, run_id)
