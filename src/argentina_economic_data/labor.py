from __future__ import annotations

import csv
import json
import os
import re
import tempfile
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd

from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, acquire

LABOR_URL = "https://www.indec.gob.ar/ftp/cuadros/sociedad/cuadros_eph_informe_06_26.xls"
TABLES = {"Cuadro 1.6": "activity", "Cuadro 1.7": "employment", "Cuadro 1.8": "unemployment"}
GEOGRAPHIES = {
    "total 31 aglomerados urbanos": "total_31_agglomerates",
    "gran buenos aires": "greater_buenos_aires",
    "cuyo": "cuyo", "noreste": "northeast", "noroeste": "northwest",
    "pampeana": "pampean", "patagonia": "patagonia",
}


def _clean(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode().lower()
    return " ".join(text.split())


def _record(series_id: str, period: str, value: Decimal, artifact: Artifact) -> dict[str, str]:
    return {"series_id": series_id, "period": period, "frequency": "quarterly",
            "value": format(value.quantize(Decimal("0.000001")), "f"), "unit": "percent",
            "status": "official", "source_id": artifact.source_id, "source_url": artifact.url,
            "source_sha256": artifact.sha256, "retrieved_at": artifact.retrieved_at}


def _columns(sheet: pd.DataFrame) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    year: int | None = None
    for column in range(1, sheet.shape[1]):
        raw_year = sheet.iat[2, column]
        if not pd.isna(raw_year):
            match = re.search(r"20\d{2}", str(raw_year))
            if match: year = int(match.group())
        quarter_match = re.search(r"([1-4])", str(sheet.iat[4, column]))
        if year is not None and quarter_match:
            result.append((column, f"{year:04d}-Q{quarter_match.group(1)}"))
    periods = [period for _, period in result]
    expected = [f"{year}-Q{quarter}" for year in range(2016, 2027) for quarter in range(1, 5)
                if (year > 2016 or quarter >= 2) and (year < 2026 or quarter == 1)]
    if periods != expected:
        raise PipelineError(f"mercado laboral: cobertura inesperada {periods}")
    return result


def _table(sheet: pd.DataFrame, indicator: str, artifact: Artifact) -> list[dict[str, str]]:
    if sheet.shape != (55, 51):
        raise PipelineError(f"mercado laboral: dimensiones inesperadas para {indicator}: {sheet.shape}")
    columns = _columns(sheet)
    rows = {_clean(sheet.iat[row, 0]): row for row in range(6, 49)}
    result: list[dict[str, str]] = []
    for label, geography in GEOGRAPHIES.items():
        if label not in rows:
            raise PipelineError(f"mercado laboral: geografía ausente: {label}")
        series_id = f"indec_labor_{indicator}_{geography}"
        for column, period in columns:
            raw = sheet.iat[rows[label], column]
            if pd.isna(raw): raise PipelineError(f"mercado laboral: valor ausente en {series_id}/{period}")
            try: value = Decimal(str(raw))
            except Exception as exc: raise PipelineError(f"mercado laboral: valor inválido en {series_id}/{period}") from exc
            if not Decimal(0) <= value <= Decimal(100):
                raise PipelineError(f"mercado laboral: tasa fuera de rango en {series_id}/{period}")
            result.append(_record(series_id, period, value, artifact))
    return result


def extract(artifact: Artifact) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    try:
        for sheet_name, indicator in TABLES.items():
            sheet = pd.read_excel(artifact.path, sheet_name=sheet_name, header=None)
            records.extend(_table(sheet, indicator, artifact))
    except ValueError as exc:
        raise PipelineError(f"mercado laboral: hojas históricas ausentes: {exc}") from exc
    values = {(r["series_id"], r["period"]): Decimal(r["value"]) for r in records}
    for geography in GEOGRAPHIES.values():
        periods = {r["period"] for r in records if r["series_id"] == f"indec_labor_activity_{geography}"}
        for period in periods:
            activity = values[(f"indec_labor_activity_{geography}", period)]
            employment = values[(f"indec_labor_employment_{geography}", period)]
            unemployment = values[(f"indec_labor_unemployment_{geography}", period)]
            implied = activity * (Decimal(1) - unemployment / 100)
            if abs(implied - employment) > Decimal("0.11"):
                raise PipelineError(f"mercado laboral: identidad de tasas inconsistente en {geography}/{period}")
    return records


def _existing(path: Path) -> dict[tuple[str, str], str]:
    if not path.exists(): return {}
    with path.open(encoding="utf-8",newline="") as handle:
        return {(r["series_id"],r["period"]):r["value"] for r in csv.DictReader(handle)}


def promote(records: list[dict[str,str]], root: Path, run_id: str) -> dict[str,object]:
    records.sort(key=lambda r:(r["series_id"],r["period"])); target_dir=root/"data"/"processed"; log_dir=root/"data"/"logs"/"labor"
    target_dir.mkdir(parents=True,exist_ok=True); log_dir.mkdir(parents=True,exist_ok=True); target=target_dir/"labor.csv"
    old=_existing(target); new={(r["series_id"],r["period"]):r["value"] for r in records}
    report={"run_id":run_id,"created":len(new.keys()-old.keys()),"deleted":len(old.keys()-new.keys()),
            "modified":sum(old[k]!=new[k] for k in old.keys()&new.keys()),"rows":len(records),
            "series":len({r["series_id"] for r in records}),"min_period":min(r["period"] for r in records),
            "max_period":max(r["period"] for r in records),"coverage_warnings":{
                "2019-Q3":"No incluye Gran Resistencia.","2020-Q3":"No incluye Ushuaia-Río Grande."}}
    if old and report["deleted"]: raise PipelineError(f"mercado laboral: la nueva versión elimina {report['deleted']} observaciones")
    fd,temporary=tempfile.mkstemp(prefix="labor-",suffix=".csv",dir=target_dir)
    try:
        with os.fdopen(fd,"w",encoding="utf-8",newline="") as handle:
            writer=csv.DictWriter(handle,fieldnames=OUTPUT_COLUMNS);writer.writeheader();writer.writerows(records);handle.flush();os.fsync(handle.fileno())
        os.replace(temporary,target)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)
    (log_dir/f"{run_id}.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report


def run(root: Path, source_file: Path|None=None)->dict[str,object]:
    run_id=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifact=acquire("indec_labor_market",LABOR_URL,root/"data"/"raw",source_file)
    return promote(extract(artifact),root,run_id)

