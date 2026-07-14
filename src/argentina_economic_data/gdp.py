from __future__ import annotations

import csv
import json
import os
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd

from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, acquire

GDP_ORIGINAL_URL = "https://www.indec.gob.ar/ftp/cuadros/economia/sh_oferta_demanda_06_26.xls"
GDP_SA_URL = "https://www.indec.gob.ar/ftp/cuadros/economia/sh_oferta_demanda_desest_06_26.xls"
QUARTERS = {"1º trimestre": 1, "2º trimestre": 2, "3º trimestre": 3, "4º trimestre": 4}
ROMAN_QUARTERS = {"I": 1, "II": 2, "III": 3, "IV": 4}


def _record(series_id: str, period: str, frequency: str, value: Decimal, unit: str, artifact: Artifact) -> dict[str, str]:
    return {
        "series_id": series_id, "period": period, "frequency": frequency,
        "value": format(value.quantize(Decimal("0.000001")), "f"), "unit": unit,
        "status": "official", "source_id": artifact.source_id, "source_url": artifact.url,
        "source_sha256": artifact.sha256, "retrieved_at": artifact.retrieved_at,
    }


def _decimal(value: object, context: str) -> Decimal:
    if pd.isna(value):
        raise PipelineError(f"PIB: valor ausente en {context}")
    try:
        return Decimal(str(value))
    except Exception as exc:
        raise PipelineError(f"PIB: valor inválido en {context}: {value!r}") from exc


def _matrix(sheet: pd.DataFrame, series_id: str, unit: str, artifact: Artifact) -> tuple[list[dict[str, str]], dict[str, Decimal]]:
    if sheet.shape[1] < 120 or sheet.shape[0] < 7:
        raise PipelineError(f"PIB: dimensiones inesperadas en {series_id}: {sheet.shape}")
    if str(sheet.iat[6, 0]).strip() != "B1b" or "Producto Interno Bruto" not in str(sheet.iat[6, 1]):
        raise PipelineError(f"PIB: fila B1b ausente en {series_id}")
    years = sheet.iloc[3].ffill()
    records: list[dict[str, str]] = []
    values: dict[str, Decimal] = {}
    for column in range(2, sheet.shape[1]):
        label = str(sheet.iat[4, column]).strip()
        if label not in {*QUARTERS, "Total"} or pd.isna(sheet.iat[6, column]):
            continue
        try:
            year = int(str(years.iat[column]).split()[0])
        except (TypeError, ValueError):
            continue
        period = str(year) if label == "Total" else f"{year:04d}-Q{QUARTERS[label]}"
        if period in values:
            raise PipelineError(f"PIB: período duplicado en {series_id}/{period}")
        value = _decimal(sheet.iat[6, column], f"{series_id}/{period}")
        values[period] = value
        frequency = "annual" if label == "Total" else "quarterly"
        records.append(_record(f"{series_id}_{frequency}", period, frequency, value, unit, artifact))
    return records, values


def extract_original(artifact: Artifact) -> tuple[list[dict[str, str]], dict[str, Decimal]]:
    try:
        constant = pd.read_excel(artifact.path, sheet_name="cuadro 1", header=None)
        growth = pd.read_excel(artifact.path, sheet_name="cuadro 2", header=None)
        current = pd.read_excel(artifact.path, sheet_name="cuadro 8", header=None)
    except Exception as exc:
        raise PipelineError(f"PIB: hojas originales ausentes: {exc}") from exc
    constant_records, constant_values = _matrix(constant, "indec_gdp_constant_2004", "million_ars_2004", artifact)
    growth_records, growth_values = _matrix(growth, "indec_gdp_growth", "percent_change", artifact)
    current_records, current_values = _matrix(current, "indec_gdp_current", "million_ars_current", artifact)
    if min(constant_values) != "2004" or "2026-Q1" not in constant_values or "2025" not in constant_values:
        raise PipelineError("PIB: cobertura original inesperada")
    if set(constant_values) != set(current_values):
        raise PipelineError("PIB: cobertura distinta entre precios constantes y corrientes")
    for period, official in growth_values.items():
        if "-Q" in period:
            year, quarter = period.split("-Q")
            prior = f"{int(year)-1:04d}-Q{quarter}"
        else:
            prior = str(int(period) - 1)
        if period in constant_values and prior in constant_values:
            calculated = (constant_values[period] / constant_values[prior] - 1) * 100
            if abs(calculated - official) > Decimal("0.0001"):
                raise PipelineError(f"PIB: crecimiento inconsistente en {period}")
    return constant_records + growth_records + current_records, constant_values


def _sa_sheet(sheet: pd.DataFrame, series_id: str, unit: str, artifact: Artifact) -> tuple[list[dict[str, str]], dict[str, Decimal]]:
    if sheet.shape[1] != 8 or "PIB" not in str(sheet.iat[3, 2]):
        raise PipelineError(f"PIB: esquema desestacionalizado inesperado en {series_id}")
    year: int | None = None
    records: list[dict[str, str]] = []
    values: dict[str, Decimal] = {}
    for row in range(6, sheet.shape[0]):
        if not pd.isna(sheet.iat[row, 0]):
            try: year = int(float(sheet.iat[row, 0]))
            except (TypeError, ValueError): continue
        quarter = str(sheet.iat[row, 1]).strip()
        if year is None or quarter not in ROMAN_QUARTERS or pd.isna(sheet.iat[row, 2]):
            continue
        period = f"{year:04d}-Q{ROMAN_QUARTERS[quarter]}"
        value = _decimal(sheet.iat[row, 2], f"{series_id}/{period}")
        if period in values: raise PipelineError(f"PIB: período duplicado en {series_id}/{period}")
        values[period] = value
        records.append(_record(series_id, period, "quarterly", value, unit, artifact))
    return records, values


def extract_sa(artifact: Artifact) -> list[dict[str, str]]:
    try:
        levels = pd.read_excel(artifact.path, sheet_name="desestacionalizado n", header=None)
        changes = pd.read_excel(artifact.path, sheet_name="desestacionalizado v", header=None)
    except Exception as exc:
        raise PipelineError(f"PIB: hojas desestacionalizadas ausentes: {exc}") from exc
    level_records, level_values = _sa_sheet(levels, "indec_gdp_sa_constant_2004", "million_ars_2004", artifact)
    change_records, change_values = _sa_sheet(changes, "indec_gdp_sa_qoq", "percent_change", artifact)
    periods = list(level_values)
    if periods[0] != "2004-Q1" or periods[-1] != "2026-Q1":
        raise PipelineError("PIB: cobertura desestacionalizada inesperada")
    for index, period in enumerate(periods[1:], 1):
        official = change_values.get(period)
        if official is None: raise PipelineError(f"PIB: variación desestacionalizada ausente en {period}")
        calculated = (level_values[period] / level_values[periods[index-1]] - 1) * 100
        if abs(calculated - official) > Decimal("0.0001"):
            raise PipelineError(f"PIB: variación trimestral inconsistente en {period}")
    return level_records + change_records


def _existing(path: Path) -> dict[tuple[str, str], str]:
    if not path.exists(): return {}
    with path.open(encoding="utf-8", newline="") as handle:
        return {(r["series_id"], r["period"]): r["value"] for r in csv.DictReader(handle)}


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    records.sort(key=lambda row: (row["series_id"], row["period"]))
    target_dir, log_dir = root / "data" / "processed", root / "data" / "logs" / "gdp"
    target_dir.mkdir(parents=True, exist_ok=True); log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "gdp.csv"; old = _existing(target)
    new = {(r["series_id"], r["period"]): r["value"] for r in records}
    report = {"run_id": run_id, "created": len(new.keys()-old.keys()), "deleted": len(old.keys()-new.keys()),
              "modified": sum(old[k] != new[k] for k in old.keys() & new.keys()), "rows": len(records),
              "series": len({r["series_id"] for r in records}),
              "quarterly_through": max(r["period"] for r in records if r["frequency"] == "quarterly"),
              "annual_through": max(r["period"] for r in records if r["frequency"] == "annual")}
    legacy_ids = {"indec_gdp_constant_2004", "indec_gdp_growth", "indec_gdp_current"}
    schema_migration = bool(old) and {key[0] for key in old if key[0] in legacy_ids} == legacy_ids
    if old and report["deleted"] and not schema_migration:
        raise PipelineError(f"PIB: la nueva versión elimina {report['deleted']} observaciones")
    if schema_migration:
        report["schema_migration"] = "separación de identificadores trimestrales y anuales"
    fd, temporary = tempfile.mkstemp(prefix="gdp-", suffix=".csv", dir=target_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer=csv.DictWriter(handle,fieldnames=OUTPUT_COLUMNS); writer.writeheader(); writer.writerows(records); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary,target)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    (log_dir/f"{run_id}.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report


def run(root: Path, original_file: Path | None = None, sa_file: Path | None = None) -> dict[str, object]:
    run_id=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); raw=root/"data"/"raw"
    original=acquire("indec_gdp_original",GDP_ORIGINAL_URL,raw,original_file)
    sa=acquire("indec_gdp_seasonally_adjusted",GDP_SA_URL,raw,sa_file)
    original_records,_=extract_original(original)
    return promote(original_records+extract_sa(sa),root,run_id)
