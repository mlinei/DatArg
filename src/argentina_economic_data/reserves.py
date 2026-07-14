from __future__ import annotations

import csv
import json
import os
import tempfile
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, acquire

VARIABLE_ID = 1
SOURCE_URL = f"https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/{VARIABLE_ID}"


def extract(artifact: Artifact) -> list[dict[str, str]]:
    try:
        payload = json.loads(artifact.path.read_text(encoding="utf-8"))
        result = payload["results"][0]
        rows = result["detalle"]
    except Exception as exc:
        raise PipelineError(f"reservas BCRA: esquema inválido: {exc}") from exc
    if payload.get("status") != 200 or result.get("idVariable") != VARIABLE_ID or not rows:
        raise PipelineError("reservas BCRA: respuesta inesperada")
    records = []
    for row in rows:
        try:
            period = date.fromisoformat(row["fecha"]).isoformat()
            value = Decimal(str(row["valor"]))
        except Exception as exc:
            raise PipelineError("reservas BCRA: observación inválida") from exc
        if value <= 0 or value > Decimal("1000000"):
            raise PipelineError(f"reservas BCRA: valor fuera de rango en {period}")
        records.append({
            "series_id": "bcra_gross_international_reserves", "period": period,
            "frequency": "daily", "value": format(value.quantize(Decimal("0.000001")), "f"),
            "unit": "million_usd", "status": "official_provisional", "source_id": "bcra_monetary_variable_1",
            "source_url": artifact.url, "source_sha256": artifact.sha256, "retrieved_at": artifact.retrieved_at,
        })
    return records


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    records.sort(key=lambda row: row["period"])
    keys = [row["period"] for row in records]
    if len(keys) != len(set(keys)): raise PipelineError("reservas BCRA: fechas duplicadas")
    if not keys or keys[0] != "1996-01-03": raise PipelineError("reservas BCRA: cobertura inicial inesperada")
    target_dir = root/"data"/"processed"; log_dir = root/"data"/"logs"/"reserves"
    target_dir.mkdir(parents=True, exist_ok=True); log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir/"reserves.csv"; old = {}
    if target.exists():
        with target.open(encoding="utf-8", newline="") as handle: old = {r["period"]: r["value"] for r in csv.DictReader(handle)}
    new = {r["period"]: r["value"] for r in records}
    report = {"run_id": run_id, "rows": len(records), "series": 1, "min_period": keys[0], "max_period": keys[-1], "created": len(new.keys()-old.keys()), "deleted": len(old.keys()-new.keys()), "modified": sum(old[k] != new[k] for k in old.keys()&new.keys())}
    if old and report["deleted"]: raise PipelineError("reservas BCRA: la fuente eliminó observaciones")
    fd, tmp = tempfile.mkstemp(prefix="reserves-", suffix=".csv", dir=target_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS); writer.writeheader(); writer.writerows(records); handle.flush(); os.fsync(handle.fileno())
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
    (log_dir/f"{run_id}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return report


def run(root: Path, source_file: Path | None = None) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); raw = root/"data"/"raw"
    if source_file:
        artifacts = [acquire("bcra_monetary_variable_1", SOURCE_URL, raw, source_file)]
    else:
        artifacts = []; offset = 0
        while True:
            artifact = acquire(f"bcra_monetary_variable_1_offset_{offset}", f"{SOURCE_URL}?offset={offset}&limit=3000", raw)
            artifacts.append(artifact)
            count = json.loads(artifact.path.read_text(encoding="utf-8"))["metadata"]["resultset"]["count"]
            offset += 3000
            if offset >= count: break
    records = []
    for artifact in artifacts: records.extend(extract(artifact))
    return promote(records, root, run_id)
