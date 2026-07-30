from __future__ import annotations

import csv
import json
import os
import tempfile
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, acquire

BASE_URL = "https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias"
VARIABLE_ID = 78
SOURCE_ID = "bcra_fx_market_intervention"
FIRST_PERIOD = "2003-01-02"


def extract(artifact: Artifact) -> list[dict[str, str]]:
    try:
        payload = json.loads(artifact.path.read_text(encoding="utf-8"))
        result = payload["results"][0]
        observations = result["detalle"]
    except Exception as exc:
        raise PipelineError(f"intervención BCRA: esquema inválido: {exc}") from exc
    if payload.get("status") != 200 or result.get("idVariable") != VARIABLE_ID:
        raise PipelineError("intervención BCRA: respuesta inesperada")

    records: list[dict[str, str]] = []
    for row in observations:
        try:
            period = date.fromisoformat(row["fecha"]).isoformat()
            value = Decimal(str(row["valor"]))
        except (KeyError, ValueError, InvalidOperation) as exc:
            raise PipelineError("intervención BCRA: observación inválida") from exc
        records.append({
            "series_id": "bcra_fx_intervention_daily",
            "period": period,
            "frequency": "daily",
            "value": format(value.quantize(Decimal("0.000001")), "f"),
            "unit": "million_usd",
            "status": "official",
            "source_id": SOURCE_ID,
            "source_url": artifact.url,
            "source_sha256": artifact.sha256,
            "retrieved_at": artifact.retrieved_at,
        })
    return records


def aggregate(daily: list[dict[str, str]]) -> list[dict[str, str]]:
    totals: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
    for row in daily:
        totals[("monthly", row["period"][:7])] += Decimal(row["value"])
        totals[("annual", row["period"][:4])] += Decimal(row["value"])
    template = daily[-1]
    records = list(daily)
    for (frequency, period), value in sorted(totals.items()):
        records.append(template | {
            "series_id": f"bcra_fx_intervention_{frequency}",
            "period": period,
            "frequency": frequency,
            "value": format(value.quantize(Decimal("0.000001")), "f"),
            "status": "calculated",
        })
    return records


def _promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    records.sort(key=lambda row: (row["series_id"], row["period"]))
    keys = [(row["series_id"], row["period"]) for row in records]
    if len(keys) != len(set(keys)):
        raise PipelineError("intervención BCRA: claves duplicadas")
    daily = [row for row in records if row["series_id"] == "bcra_fx_intervention_daily"]
    if not daily or daily[0]["period"] != FIRST_PERIOD:
        raise PipelineError("intervención BCRA: cobertura histórica inesperada")

    target_dir = root / "data" / "processed"
    log_dir = root / "data" / "logs" / "fx_intervention"
    target_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "fx_intervention.csv"
    old: dict[tuple[str, str], str] = {}
    if target.exists():
        with target.open(encoding="utf-8", newline="") as handle:
            old = {(row["series_id"], row["period"]): row["value"] for row in csv.DictReader(handle)}
    new = {(row["series_id"], row["period"]): row["value"] for row in records}
    report = {
        "run_id": run_id, "rows": len(records), "series": len({row["series_id"] for row in records}),
        "min_period": daily[0]["period"], "max_period": daily[-1]["period"],
        "created": len(new.keys() - old.keys()), "deleted": len(old.keys() - new.keys()),
        "modified": sum(old[key] != new[key] for key in old.keys() & new.keys()),
    }
    # El acumulado del año/mes corriente cambia cada día; las observaciones diarias no deben desaparecer.
    old_daily = {key for key in old if key[0] == "bcra_fx_intervention_daily"}
    new_daily = {key for key in new if key[0] == "bcra_fx_intervention_daily"}
    if old_daily - new_daily:
        raise PipelineError("intervención BCRA: la fuente eliminó observaciones diarias")

    fd, temporary = tempfile.mkstemp(prefix="fx-intervention-", suffix=".csv", dir=target_dir)
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


def run(root: Path, source_file: Path | None = None) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw_root = root / "data" / "raw"
    if source_file:
        artifacts = [acquire(SOURCE_ID, f"{BASE_URL}/{VARIABLE_ID}", raw_root, source_file)]
    else:
        artifacts = []
        offset = 0
        while True:
            artifact = acquire(
                f"{SOURCE_ID}_offset_{offset}",
                f"{BASE_URL}/{VARIABLE_ID}?offset={offset}&limit=1000",
                raw_root,
            )
            artifacts.append(artifact)
            payload = json.loads(artifact.path.read_text(encoding="utf-8"))
            count = payload["metadata"]["resultset"]["count"]
            offset += 1000
            if offset >= count:
                break
    daily: list[dict[str, str]] = []
    for artifact in artifacts:
        daily.extend(extract(artifact))
    daily.sort(key=lambda row: row["period"])
    if len({row["period"] for row in daily}) != len(daily):
        raise PipelineError("intervención BCRA: páginas superpuestas")
    return _promote(aggregate(daily), root, run_id)
