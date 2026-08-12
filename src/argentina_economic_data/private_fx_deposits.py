from __future__ import annotations

import csv
import json
import os
import tempfile
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, acquire

VARIABLE_ID = 108
SOURCE_ID = "bcra_private_nonfinancial_fx_deposits"
SOURCE_URL = f"https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/{VARIABLE_ID}"
FIRST_PERIOD = "2002-12"


def extract(artifact: Artifact) -> list[dict[str, str]]:
    try:
        payload = json.loads(artifact.path.read_text(encoding="utf-8"))
        result = payload["results"][0]
        observations = result["detalle"]
    except Exception as exc:
        raise PipelineError(f"depósitos privados en dólares: esquema inválido: {exc}") from exc
    if payload.get("status") != 200 or result.get("idVariable") != VARIABLE_ID or not observations:
        raise PipelineError("depósitos privados en dólares: respuesta inesperada")

    records: list[dict[str, str]] = []
    for row in observations:
        try:
            period = date.fromisoformat(row["fecha"]).isoformat()
            value = Decimal(str(row["valor"]))
        except (KeyError, ValueError, InvalidOperation) as exc:
            raise PipelineError("depósitos privados en dólares: observación inválida") from exc
        if value <= 0 or value > Decimal("1000000"):
            raise PipelineError(f"depósitos privados en dólares: valor fuera de rango en {period}")
        records.append({
            "series_id": SOURCE_ID,
            "period": period,
            "frequency": "daily",
            "value": format(value.quantize(Decimal("0.000001")), "f"),
            "unit": "million_usd",
            "status": "official_provisional",
            "source_id": "bcra_monetary_variable_108",
            "source_url": artifact.url,
            "source_sha256": artifact.sha256,
            "retrieved_at": artifact.retrieved_at,
        })
    return records


def aggregate_monthly(records: list[dict[str, str]]) -> list[dict[str, str]]:
    """Conserva el último saldo diario disponible de cada mes calendario."""
    latest: dict[str, dict[str, str]] = {}
    for row in records:
        month = row["period"][:7]
        if month not in latest or row["period"] > latest[month]["period"]:
            latest[month] = row
    return [latest[month] | {"period": month, "frequency": "monthly"} for month in sorted(latest)]


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    records = aggregate_monthly(records)
    keys = [row["period"] for row in records]
    if len(keys) != len(set(keys)):
        raise PipelineError("depósitos privados en dólares: meses duplicados")
    if not keys or keys[0] != FIRST_PERIOD:
        raise PipelineError("depósitos privados en dólares: cobertura inicial inesperada")

    target_dir = root / "data" / "processed"
    log_dir = root / "data" / "logs" / "private_fx_deposits"
    target_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "private_fx_deposits.csv"
    old: dict[str, str] = {}
    if target.exists():
        with target.open(encoding="utf-8", newline="") as handle:
            old = {row["period"]: row["value"] for row in csv.DictReader(handle)}
    new = {row["period"]: row["value"] for row in records}
    report = {
        "run_id": run_id,
        "rows": len(records),
        "series": 1,
        "min_period": keys[0],
        "max_period": keys[-1],
        "created": len(new.keys() - old.keys()),
        "deleted": len(old.keys() - new.keys()),
        "modified": sum(old[key] != new[key] for key in old.keys() & new.keys()),
    }
    if old and report["deleted"]:
        raise PipelineError("depósitos privados en dólares: la fuente eliminó observaciones")

    fd, temporary = tempfile.mkstemp(prefix="private-fx-deposits-", suffix=".csv", dir=target_dir)
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
    raw = root / "data" / "raw"
    if source_file:
        artifacts = [acquire("bcra_monetary_variable_108", SOURCE_URL, raw, source_file)]
    else:
        artifacts = []
        offset = 0
        while True:
            url = f"{SOURCE_URL}?offset={offset}&limit=3000"
            artifact = acquire(f"bcra_monetary_variable_108_offset_{offset}", url, raw)
            artifacts.append(artifact)
            count = json.loads(artifact.path.read_text(encoding="utf-8"))["metadata"]["resultset"]["count"]
            offset += 3000
            if offset >= count:
                break
    records: list[dict[str, str]] = []
    for artifact in artifacts:
        records.extend(extract(artifact))
    return promote(records, root, run_id)
