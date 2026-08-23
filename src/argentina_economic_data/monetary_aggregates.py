from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import xlrd

from .credit import _gdp_denominators
from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, acquire

HISTORY_URL = "https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/panhis.xls"
SOURCE_PAGE = "https://www.bcra.gob.ar/balances-y-agregados-monetarios/"
API_ROOT = "https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias"
API_VARIABLES = {
    15: "bcra_monetary_base_daily",
    16: "bcra_currency_circulation_daily",
    17: "bcra_currency_public_daily",
    18: "bcra_cash_financial_institutions_daily",
    19: "bcra_bank_current_accounts_daily",
}
MONTHLY_SERIES = {
    "M0": "bcra_monetary_base_monthly",
    "M1": "bcra_m1_total_monthly",
    "M2": "bcra_m2_total_monthly",
    "M3": "bcra_m3_resident_monthly",
    "M3_total": "bcra_m3_total_monthly",
}
REAL_BASE_PERIOD = "2023-12"
MONTHS = {name: index for index, name in enumerate(
    ("Ene.", "Feb.", "Mar.", "Abr.", "May.", "Jun.", "Jul.", "Ago.", "Set.", "Oct.", "Nov.", "Dic."), 1
)}


def extract_api(artifact: Artifact, variable_id: int) -> list[dict[str, str]]:
    try:
        payload = json.loads(artifact.path.read_text(encoding="utf-8"))
        result = payload["results"][0]
        rows = result["detalle"]
    except Exception as exc:
        raise PipelineError(f"agregados monetarios: respuesta API inválida: {exc}") from exc
    if payload.get("status") != 200 or result.get("idVariable") != variable_id:
        raise PipelineError(f"agregados monetarios: respuesta inesperada para variable {variable_id}")
    records = []
    for row in rows:
        try:
            period = date.fromisoformat(row["fecha"]).isoformat()
            value = Decimal(str(row["valor"]))
        except (KeyError, ValueError, InvalidOperation) as exc:
            raise PipelineError(f"agregados monetarios: observación inválida en variable {variable_id}") from exc
        if value < 0:
            raise PipelineError(f"agregados monetarios: valor negativo en {variable_id}/{period}")
        records.append({
            "series_id": API_VARIABLES[variable_id], "period": period, "frequency": "daily",
            "value": format(value.quantize(Decimal("0.000001")), "f"), "unit": "million_ars",
            "status": "official_provisional", "source_id": f"bcra_monetary_variable_{variable_id}",
            "source_url": artifact.url, "source_sha256": artifact.sha256,
            "retrieved_at": artifact.retrieved_at,
        })
    return records


def extract_history(artifact: Artifact) -> list[dict[str, str]]:
    try:
        workbook = xlrd.open_workbook(artifact.path)
    except Exception as exc:
        raise PipelineError(f"agregados monetarios: no se pudo leer el libro histórico: {exc}") from exc
    records: list[dict[str, str]] = []
    for sheet_name, series_id in MONTHLY_SERIES.items():
        sheet = workbook.sheet_by_name(sheet_name)
        for row in range(26, sheet.nrows):
            month_name = str(sheet.cell_value(row, 1)).strip()
            if month_name not in MONTHS:
                continue
            try:
                year = int(float(sheet.cell_value(row, 0)))
                raw = Decimal(str(sheet.cell_value(row, 6)))
            except (TypeError, ValueError, InvalidOperation):
                continue
            if year < 1992 or raw <= 0 or str(sheet.cell_value(row, 3)).strip() != "Pesos":
                continue
            period = f"{year:04d}-{MONTHS[month_name]:02d}"
            value = raw / Decimal(1000)  # el libro expresa los saldos en miles de pesos
            records.append({
                "series_id": series_id, "period": period, "frequency": "monthly",
                "value": format(value.quantize(Decimal("0.000001")), "f"), "unit": "million_ars",
                "status": "official", "source_id": "bcra_historical_monetary_aggregates",
                "source_url": SOURCE_PAGE, "source_sha256": artifact.sha256,
                "retrieved_at": artifact.retrieved_at,
            })
    return records


def _load(path: Path, series_id: str) -> tuple[dict[str, Decimal], str]:
    if not path.exists():
        raise PipelineError(f"agregados monetarios: falta el insumo {path}")
    content = path.read_bytes()
    with path.open(encoding="utf-8", newline="") as handle:
        values = {row["period"]: Decimal(row["value"]) for row in csv.DictReader(handle) if row["series_id"] == series_id}
    if not values:
        raise PipelineError(f"agregados monetarios: falta la serie {series_id}")
    return values, hashlib.sha256(content).hexdigest()


def calculate_derived(records: list[dict[str, str]], inflation_path: Path, gdp_path: Path) -> list[dict[str, str]]:
    cpi, inflation_hash = _load(inflation_path, "indec_ipc_general_index")
    gdp, gdp_hash = _load(gdp_path, "indec_gdp_current_quarterly")
    if REAL_BASE_PERIOD not in cpi:
        raise PipelineError(f"agregados monetarios: falta IPC de {REAL_BASE_PERIOD}")
    levels = {(row["series_id"], row["period"]): Decimal(row["value"]) for row in records if row["series_id"] in MONTHLY_SERIES.values()}
    bases = {series: levels.get((series, REAL_BASE_PERIOD)) for series in MONTHLY_SERIES.values()}
    if any(value is None for value in bases.values()):
        raise PipelineError(f"agregados monetarios: faltan saldos base de {REAL_BASE_PERIOD}")
    denominators = _gdp_denominators(gdp)
    available_quarters = sorted(denominators)
    derived: list[dict[str, str]] = []
    for row in records:
        series_id, period = row["series_id"], row["period"]
        if series_id not in MONTHLY_SERIES.values():
            continue
        current = Decimal(row["value"])
        if period in cpi:
            base = bases[series_id]
            assert base is not None
            real = (current / cpi[period]) / (base / cpi[REAL_BASE_PERIOD]) * Decimal(100)
            derived.append(row | {
                "series_id": f"{series_id}_real_index", "value": format(real.quantize(Decimal("0.000001")), "f"),
                "unit": "index_dec_2023_100", "status": "calculated",
                "source_id": "datarg_bcra_money_deflated_by_indec_cpi",
                "source_sha256": hashlib.sha256(f"{row['source_sha256']}|{inflation_hash}".encode()).hexdigest(),
            })
        year, month = map(int, period.split("-"))
        quarter = year * 4 + (month - 1) // 3
        usable = [item for item in available_quarters if item <= quarter]
        if usable:
            ratio = current / denominators[usable[-1]] * Decimal(100)
            derived.append(row | {
                "series_id": f"{series_id}_gdp_ratio", "value": format(ratio.quantize(Decimal("0.000001")), "f"),
                "unit": "percent_gdp", "status": "calculated",
                "source_id": "datarg_bcra_money_over_indec_gdp",
                "source_sha256": hashlib.sha256(f"{row['source_sha256']}|{gdp_hash}".encode()).hexdigest(),
            })
    return derived


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    records.sort(key=lambda row: (row["series_id"], row["period"]))
    keys = [(row["series_id"], row["period"]) for row in records]
    if len(keys) != len(set(keys)):
        raise PipelineError("agregados monetarios: claves duplicadas")
    monthly = [row for row in records if row["series_id"] == "bcra_monetary_base_monthly"]
    if not monthly or monthly[0]["period"] != "1992-01":
        raise PipelineError("agregados monetarios: cobertura histórica inesperada")
    target_dir = root / "data" / "processed"
    log_dir = root / "data" / "logs" / "monetary_aggregates"
    target_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "monetary_aggregates.csv"
    old = {}
    if target.exists():
        with target.open(encoding="utf-8", newline="") as handle:
            old = {(row["series_id"], row["period"]): row["value"] for row in csv.DictReader(handle)}
    new = {(row["series_id"], row["period"]): row["value"] for row in records}
    report = {"run_id": run_id, "rows": len(records), "series": len({row["series_id"] for row in records}),
              "min_period": min(row["period"] for row in records), "max_period": max(row["period"] for row in records),
              "created": len(new.keys() - old.keys()), "deleted": len(old.keys() - new.keys()),
              "modified": sum(old[key] != new[key] for key in old.keys() & new.keys())}
    if old.keys() - new.keys():
        raise PipelineError("agregados monetarios: la fuente eliminó observaciones existentes")
    fd, temporary = tempfile.mkstemp(prefix="monetary-aggregates-", suffix=".csv", dir=target_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader(); writer.writerows(records); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    (log_dir / f"{run_id}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def run(root: Path, history_file: Path | None = None, variable_files: dict[int, Path | None] | None = None) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw = root / "data" / "raw"
    history = acquire("bcra_historical_monetary_aggregates", HISTORY_URL, raw, history_file)
    records = extract_history(history)
    variable_files = variable_files or {}
    for variable_id in API_VARIABLES:
        if variable_files.get(variable_id):
            artifacts = [acquire(f"bcra_monetary_variable_{variable_id}", f"{API_ROOT}/{variable_id}", raw, variable_files[variable_id])]
        else:
            artifacts, offset = [], 0
            while True:
                url = f"{API_ROOT}/{variable_id}?offset={offset}&limit=3000"
                artifact = acquire(f"bcra_monetary_variable_{variable_id}_offset_{offset}", url, raw)
                artifacts.append(artifact)
                count = json.loads(artifact.path.read_text(encoding="utf-8"))["metadata"]["resultset"]["count"]
                offset += 3000
                if offset >= count: break
        for artifact in artifacts:
            records.extend(extract_api(artifact, variable_id))
    records.extend(calculate_derived(records, root / "data" / "processed" / "inflation.csv", root / "data" / "processed" / "gdp.csv"))
    return promote(records, root, run_id)
