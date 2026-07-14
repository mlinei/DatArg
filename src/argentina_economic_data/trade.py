from __future__ import annotations

import csv
import json
import os
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, acquire

TRADE_URL = "https://www.indec.gob.ar/ftp/ica_digital/ica_d_06_26DD4A27ECEA/data/plots/plot_agregado.json"

MONTHS = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sept": 9, "oct": 10, "nov": 11, "dic": 12,
}
SERIES = {
    "Exportaciones": "indec_trade_exports",
    "Importaciones": "indec_trade_imports",
    "Saldo": "indec_trade_balance",
}


def _period(label: str) -> str:
    try:
        month, short_year = label.lower().split("-")
        year_number = int(short_year)
        year = 1900 + year_number if year_number >= 80 else 2000 + year_number
        return f"{year:04d}-{MONTHS[month]:02d}"
    except (ValueError, KeyError) as exc:
        raise PipelineError(f"comercio exterior: período desconocido {label!r}") from exc


def _record(series_id: str, period: str, value: Decimal, artifact: Artifact) -> dict[str, str]:
    return {
        "series_id": series_id, "period": period, "frequency": "monthly",
        "value": format(value.quantize(Decimal("0.000001")), "f"), "unit": "million_usd",
        "status": "official", "source_id": artifact.source_id, "source_url": artifact.url,
        "source_sha256": artifact.sha256, "retrieved_at": artifact.retrieved_at,
    }


def extract(artifact: Artifact) -> list[dict[str, str]]:
    try:
        payload = json.loads(artifact.path.read_text(encoding="utf-8"))
        traces = payload["plot"]["data"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise PipelineError(f"comercio exterior: JSON o esquema inválido: {exc}") from exc
    if len(traces) != 3 or {trace.get("name") for trace in traces} != set(SERIES):
        raise PipelineError("comercio exterior: se esperaban exportaciones, importaciones y saldo")
    values: dict[str, dict[str, Decimal]] = {}
    records: list[dict[str, str]] = []
    for trace in traces:
        name = trace["name"]
        labels, observations = trace.get("x"), trace.get("y")
        if not isinstance(labels, list) or not isinstance(observations, list) or len(labels) != len(observations):
            raise PipelineError(f"comercio exterior: longitudes inválidas en {name}")
        series_values: dict[str, Decimal] = {}
        for label, raw in zip(labels, observations, strict=True):
            period = _period(str(label))
            if period in series_values:
                raise PipelineError(f"comercio exterior: período duplicado en {name}/{period}")
            try:
                value = Decimal(str(raw))
            except Exception as exc:
                raise PipelineError(f"comercio exterior: valor inválido en {name}/{period}") from exc
            if name != "Saldo" and value < 0:
                raise PipelineError(f"comercio exterior: flujo negativo en {name}/{period}")
            series_values[period] = value
            records.append(_record(SERIES[name], period, value, artifact))
        values[name] = series_values
    periods = list(values["Exportaciones"])
    if periods[0] != "1986-01" or len(periods) < 480:
        raise PipelineError("comercio exterior: cobertura histórica inesperada")
    if any(list(values[name]) != periods for name in SERIES):
        raise PipelineError("comercio exterior: panel mensual incompleto")
    for period in periods:
        calculated = values["Exportaciones"][period] - values["Importaciones"][period]
        if abs(calculated - values["Saldo"][period]) > Decimal("0.000001"):
            raise PipelineError(f"comercio exterior: saldo inconsistente en {period}")
    return records


def _existing(path: Path) -> dict[tuple[str, str], str]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        return {(r["series_id"], r["period"]): r["value"] for r in csv.DictReader(handle)}


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    records.sort(key=lambda row: (row["series_id"], row["period"]))
    target_dir, log_dir = root / "data" / "processed", root / "data" / "logs" / "trade"
    target_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "trade.csv"
    old = _existing(target)
    new = {(r["series_id"], r["period"]): r["value"] for r in records}
    report = {
        "run_id": run_id, "created": len(new.keys() - old.keys()),
        "deleted": len(old.keys() - new.keys()),
        "modified": sum(old[k] != new[k] for k in old.keys() & new.keys()),
        "rows": len(records), "series": len({r["series_id"] for r in records}),
        "min_period": min(r["period"] for r in records), "max_period": max(r["period"] for r in records),
    }
    if old and report["deleted"]:
        raise PipelineError(f"comercio exterior: la nueva versión elimina {report['deleted']} observaciones")
    fd, temporary = tempfile.mkstemp(prefix="trade-", suffix=".csv", dir=target_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader(); writer.writerows(records); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    (log_dir / f"{run_id}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def run(root: Path, source_file: Path | None = None) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifact = acquire("indec_trade_balance", TRADE_URL, root / "data" / "raw", source_file)
    return promote(extract(artifact), root, run_id)

