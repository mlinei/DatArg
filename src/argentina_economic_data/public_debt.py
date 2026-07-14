from __future__ import annotations

import csv
import json
import os
import tempfile
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd

from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, acquire


TREASURY_ID = "mecon_monthly_gross_central_government_debt"
TREASURY_URL = "https://www.argentina.gob.ar/sites/default/files/boletin_mensual_31_05_2026_1.xlsx"
BCRA_BASE = "https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias"
# Pasivos financieros remunerados: letras en ARS y ME, LELIQ/NOTALIQ, pases en ARS
# y pases pasivos con el exterior. El TC mayorista convierte todo a USD.
BCRA_ARS_COMPONENTS = (1258, 1259, 1260, 1262)
BCRA_USD_COMPONENTS = (76,)
BCRA_FX = 5
BCRA_VARIABLES = BCRA_ARS_COMPONENTS + BCRA_USD_COMPONENTS + (BCRA_FX,)


def _record(series_id: str, period: str, value: Decimal, artifact: Artifact) -> dict[str, str]:
    return {
        "series_id": series_id, "period": period, "frequency": "monthly",
        "value": format(value.quantize(Decimal("0.000001")), "f"), "unit": "million_usd",
        "status": "official" if series_id.startswith("mecon_") else "calculated",
        "source_id": artifact.source_id, "source_url": artifact.url,
        "source_sha256": artifact.sha256, "retrieved_at": artifact.retrieved_at,
    }


def extract_treasury(artifact: Artifact) -> list[dict[str, str]]:
    try:
        sheet = pd.read_excel(artifact.path, sheet_name="A.1", header=None)
    except Exception as exc:
        raise PipelineError(f"deuda Tesoro: libro ilegible: {exc}") from exc
    labels = sheet.iloc[:, 1].astype(str).str.strip()
    hits = labels[labels.str.match(r"^A- DEUDA BRUTA \(", na=False)].index.tolist()
    if len(hits) != 1:
        raise PipelineError(f"deuda Tesoro: se esperaba una fila total y se encontraron {len(hits)}")
    row = hits[0]
    records = []
    seen = set()
    for col in range(2, sheet.shape[1]):
        raw_period, raw_value = sheet.iat[8, col], sheet.iat[row, col]
        if pd.isna(raw_period) or pd.isna(raw_value): continue
        try:
            text_period = str(raw_period).strip().lower().replace(" (*)", "")
            month_map = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
                         "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12}
            if len(text_period) >= 6 and text_period[:3] in month_map and "-" in text_period:
                year = 2000 + int(text_period.split("-")[-1])
                period = f"{year:04d}-{month_map[text_period[:3]]:02d}"
            elif isinstance(raw_period, (datetime, pd.Timestamp)):
                period = pd.Timestamp(raw_period).strftime("%Y-%m")
            else:
                continue
            value = Decimal(str(raw_value))
        except Exception as exc:
            raise PipelineError(f"deuda Tesoro: observación inválida en columna {col}") from exc
        if period in seen or value <= 0: raise PipelineError(f"deuda Tesoro: dato inválido en {period}")
        seen.add(period); records.append(_record("mecon_gross_central_government_debt", period, value, artifact))
    if not records or records[0]["period"] != "2019-01": raise PipelineError("deuda Tesoro: cobertura inicial inesperada")
    return records


def extract_bcra(artifact: Artifact, variable_id: int) -> dict[date, Decimal]:
    try:
        payload = json.loads(artifact.path.read_text(encoding="utf-8"))
        result = payload["results"][0]
        rows = result["detalle"]
    except Exception as exc:
        raise PipelineError(f"pasivos BCRA {variable_id}: esquema inválido: {exc}") from exc
    if payload.get("status") != 200 or result.get("idVariable") != variable_id or not rows:
        raise PipelineError(f"pasivos BCRA {variable_id}: respuesta inesperada")
    values = {}
    for row in rows:
        d = date.fromisoformat(row["fecha"]); value = Decimal(str(row["valor"]))
        if d in values or value < 0: raise PipelineError(f"pasivos BCRA {variable_id}: dato inválido en {d}")
        values[d] = value
    return values


def calculate_bcra_monthly(series: dict[int, dict[date, Decimal]], artifacts: dict[int, Artifact]) -> list[dict[str, str]]:
    # Se toma el último día informado de cada mes para cada serie y se suman sólo
    # componentes ya existentes en esa fecha. No se retro-rellena antes de su inicio.
    monthly: dict[int, dict[str, tuple[date, Decimal]]] = {}
    for variable_id, values in series.items():
        monthly[variable_id] = {}
        for d, value in values.items():
            key = f"{d.year:04d}-{d.month:02d}"
            if key not in monthly[variable_id] or d > monthly[variable_id][key][0]:
                monthly[variable_id][key] = (d, value)
    periods = sorted(set().union(*(set(v) for v in monthly.values())))
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    records = []
    for period in periods:
        if period >= current_month: continue
        fx_item = monthly[BCRA_FX].get(period)
        if not fx_item: continue
        fx = fx_item[1]
        if fx <= 0: raise PipelineError(f"pasivos BCRA: tipo de cambio inválido en {period}")
        ars = sum((monthly[i][period][1] for i in BCRA_ARS_COMPONENTS if period in monthly[i]), Decimal(0))
        usd = sum((monthly[i][period][1] for i in BCRA_USD_COMPONENTS if period in monthly[i]), Decimal(0))
        total = ars / fx + usd
        if total < 0: raise PipelineError(f"pasivos BCRA: total negativo en {period}")
        records.append(_record("bcra_interest_bearing_liabilities", period, total, artifacts[BCRA_FX]))
    if not records: raise PipelineError("pasivos BCRA: no hay meses comunes")
    return records


def _acquire_bcra(root: Path, variable_id: int, local: Path | None) -> tuple[Artifact, dict[date, Decimal]]:
    artifacts = []
    offset = 0
    while True:
        if local:
            artifact = acquire(f"bcra_debt_variable_{variable_id}", f"{BCRA_BASE}/{variable_id}", root, local)
            artifacts.append(artifact); break
        artifact = acquire(f"bcra_debt_variable_{variable_id}_offset_{offset}", f"{BCRA_BASE}/{variable_id}?offset={offset}&limit=3000", root)
        artifacts.append(artifact)
        count = json.loads(artifact.path.read_text(encoding="utf-8"))["metadata"]["resultset"]["count"]
        offset += 3000
        if offset >= count: break
    merged = {}
    for artifact in artifacts:
        page = extract_bcra(artifact, variable_id)
        if merged.keys() & page.keys(): raise PipelineError(f"pasivos BCRA {variable_id}: páginas superpuestas")
        merged.update(page)
    return artifacts[-1], merged


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    records.sort(key=lambda r: (r["series_id"], r["period"]))
    target_dir = root / "data" / "processed"; log_dir = root / "data" / "logs" / "public_debt"
    target_dir.mkdir(parents=True, exist_ok=True); log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "public_debt.csv"
    old = {}
    if target.exists():
        with target.open(encoding="utf-8", newline="") as h: old = {(r["series_id"], r["period"]): r["value"] for r in csv.DictReader(h)}
    new = {(r["series_id"], r["period"]): r["value"] for r in records}
    coverage = {sid: {"from": min(r["period"] for r in records if r["series_id"] == sid), "through": max(r["period"] for r in records if r["series_id"] == sid)} for sid in sorted({r["series_id"] for r in records})}
    report = {"run_id": run_id, "rows": len(records), "series": 2, "coverage": coverage, "created": len(new.keys()-old.keys()), "deleted": len(old.keys()-new.keys()), "modified": sum(old[k] != new[k] for k in old.keys() & new.keys())}
    deleted_keys = old.keys() - new.keys()
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    if old and any(period != current_month for _series, period in deleted_keys):
        raise PipelineError("deuda pública: la nueva versión elimina observaciones cerradas")
    fd, tmp = tempfile.mkstemp(prefix="public-debt-", suffix=".csv", dir=target_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as h:
            w = csv.DictWriter(h, fieldnames=OUTPUT_COLUMNS); w.writeheader(); w.writerows(records); h.flush(); os.fsync(h.fileno())
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
    (log_dir/f"{run_id}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return report


def run(root: Path, treasury_file: Path | None = None, bcra_files: dict[int, Path | None] | None = None) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); raw = root/"data"/"raw"
    treasury = acquire(TREASURY_ID, TREASURY_URL, raw, treasury_file)
    artifacts = {}; series = {}; bcra_files = bcra_files or {}
    for variable_id in BCRA_VARIABLES:
        artifacts[variable_id], series[variable_id] = _acquire_bcra(raw, variable_id, bcra_files.get(variable_id))
    return promote(extract_treasury(treasury) + calculate_bcra_monthly(series, artifacts), root, run_id)
