from __future__ import annotations

import csv
import json
import os
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd

from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, _record, acquire

EMAE_GENERAL_URL = "https://www.indec.gob.ar/ftp/cuadros/economia/sh_emae_mensual_base2004.xls"
EMAE_SECTOR_URL = "https://www.indec.gob.ar/ftp/cuadros/economia/sh_emae_actividad_base2004.xls"

MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

SECTORS = {
    "A": "agriculture_forestry",
    "B": "fishing",
    "C": "mining_quarrying",
    "D": "manufacturing",
    "E": "electricity_gas_water",
    "F": "construction",
    "G": "wholesale_retail_repairs",
    "H": "hotels_restaurants",
    "I": "transport_communications",
    "J": "financial_intermediation",
    "K": "real_estate_business_rental",
    "L": "public_administration_defense",
    "M": "education",
    "N": "health_social_services",
    "O": "community_social_personal_services",
    "TAX": "taxes_net_subsidies",
}


def _period_rows(sheet: pd.DataFrame, start: int) -> list[tuple[int, str]]:
    year: int | None = None
    result: list[tuple[int, str]] = []
    for row in range(start, sheet.shape[0]):
        raw_year, raw_month = sheet.iat[row, 0], sheet.iat[row, 1]
        if not pd.isna(raw_year):
            try:
                year = int(float(raw_year))
            except (TypeError, ValueError):
                continue
        month = str(raw_month).strip().lower()
        if year is None or month not in MONTHS:
            continue
        result.append((row, f"{year:04d}-{MONTHS[month]:02d}"))
    if not result:
        raise PipelineError("EMAE: no se encontraron períodos")
    periods = [period for _, period in result]
    if len(periods) != len(set(periods)):
        raise PipelineError("EMAE: períodos duplicados")
    return result


def _number(value: object, context: str) -> Decimal:
    if pd.isna(value):
        raise PipelineError(f"EMAE: valor ausente en {context}")
    try:
        return Decimal(str(value))
    except Exception as exc:
        raise PipelineError(f"EMAE: valor inválido en {context}: {value!r}") from exc


def _check_change(current: Decimal, previous: Decimal, official: Decimal, context: str) -> None:
    calculated = (current / previous - 1) * 100
    if abs(calculated - official) > Decimal("0.0001"):
        raise PipelineError(f"EMAE: variación inconsistente en {context}")


def extract_general(artifact: Artifact) -> list[dict[str, str]]:
    try:
        sheet = pd.read_excel(artifact.path, sheet_name="EMAE", header=None)
    except Exception as exc:
        raise PipelineError(f"EMAE general: no se pudo leer la hoja EMAE: {exc}") from exc
    if sheet.shape[1] != 8 or sheet.shape[0] < 200:
        raise PipelineError(f"EMAE general: dimensiones inesperadas {sheet.shape}")
    headers = " ".join(str(value) for value in sheet.iloc[2].tolist())
    for expected in ["Serie Original", "Desestacionalizada", "Tendencia-Ciclo"]:
        if expected not in headers:
            raise PipelineError(f"EMAE general: falta encabezado {expected}")
    periods = _period_rows(sheet, 4)
    if periods[0][1] != "2004-01" or len(periods) < 240:
        raise PipelineError("EMAE general: cobertura inesperada")
    specs = [
        (2, "indec_emae_original_index", "index_2004_100"),
        (3, "indec_emae_original_yoy", "percent_change"),
        (4, "indec_emae_sa_index", "index_2004_100"),
        (5, "indec_emae_sa_mom", "percent_change"),
        (6, "indec_emae_trend_cycle_index", "index_2004_100"),
        (7, "indec_emae_trend_cycle_mom", "percent_change"),
    ]
    result: list[dict[str, str]] = []
    for column, series_id, unit in specs:
        previous: Decimal | None = None
        history: dict[str, Decimal] = {}
        for row, period in periods:
            raw = sheet.iat[row, column]
            if pd.isna(raw):
                # Las variaciones mensuales no se publican para la primera observación.
                if period == "2004-01" and series_id.endswith("_mom"):
                    continue
                raise PipelineError(f"EMAE general: valor ausente en {series_id}/{period}")
            value = _number(raw, f"{series_id}/{period}")
            if unit.startswith("index") and value <= 0:
                raise PipelineError(f"EMAE general: índice no positivo en {series_id}/{period}")
            result.append(_record(series_id, period, value, unit, artifact))
            if series_id.endswith("_index"):
                history[period] = value
            previous = value
    # Contrasta las variaciones publicadas con sus índices sin recalcular la salida.
    values = {(r["series_id"], r["period"]): Decimal(r["value"]) for r in result}
    for _, period in periods:
        year, month = map(int, period.split("-"))
        prior_month = f"{year - 1:04d}-12" if month == 1 else f"{year:04d}-{month - 1:02d}"
        prior_year = f"{year - 1:04d}-{month:02d}"
        for index_id, change_id, prior in [
            ("indec_emae_sa_index", "indec_emae_sa_mom", prior_month),
            ("indec_emae_trend_cycle_index", "indec_emae_trend_cycle_mom", prior_month),
            ("indec_emae_original_index", "indec_emae_original_yoy", prior_year),
        ]:
            keys = ((index_id, period), (index_id, prior), (change_id, period))
            if all(key in values for key in keys):
                _check_change(values[keys[0]], values[keys[1]], values[keys[2]], f"{change_id}/{period}")
    return result


def _sector_headers(sheet: pd.DataFrame) -> list[str]:
    result = []
    for column in range(2, sheet.shape[1]):
        header = str(sheet.iat[2, column]).strip()
        code = header.split("-", 1)[0].strip()
        result.append(code if code in SECTORS else "TAX")
    if result != list(SECTORS):
        raise PipelineError(f"EMAE sectorial: columnas inesperadas {result}")
    return result


def extract_sectors(artifact: Artifact) -> list[dict[str, str]]:
    try:
        indexes = pd.read_excel(artifact.path, sheet_name="Tabla Letras", header=None)
        changes = pd.read_excel(artifact.path, sheet_name="Tabla Var Letras", header=None)
    except Exception as exc:
        raise PipelineError(f"EMAE sectorial: hojas esperadas ausentes: {exc}") from exc
    if indexes.shape[1] != 18 or changes.shape[1] != 18:
        raise PipelineError("EMAE sectorial: cantidad de columnas inesperada")
    index_headers = _sector_headers(indexes)
    if _sector_headers(changes) != index_headers:
        raise PipelineError("EMAE sectorial: columnas distintas entre índice y variación")
    index_periods = _period_rows(indexes, 5)
    change_periods = _period_rows(changes, 5)
    if index_periods[0][1] != "2004-01" or change_periods[0][1] != "2005-01":
        raise PipelineError("EMAE sectorial: inicio de cobertura inesperado")
    index_values: dict[tuple[str, str], Decimal] = {}
    result: list[dict[str, str]] = []
    for column, code in enumerate(index_headers, 2):
        series_id = f"indec_emae_sector_{SECTORS[code]}_index"
        for row, period in index_periods:
            value = _number(indexes.iat[row, column], f"{series_id}/{period}")
            if value <= 0:
                raise PipelineError(f"EMAE sectorial: índice no positivo en {series_id}/{period}")
            index_values[(code, period)] = value
            result.append(_record(series_id, period, value, "index_2004_100", artifact))
    for column, code in enumerate(index_headers, 2):
        series_id = f"indec_emae_sector_{SECTORS[code]}_yoy"
        for row, period in change_periods:
            value = _number(changes.iat[row, column], f"{series_id}/{period}")
            year, month = period.split("-")
            prior = f"{int(year) - 1:04d}-{month}"
            if (code, period) not in index_values or (code, prior) not in index_values:
                raise PipelineError(f"EMAE sectorial: índice faltante para validar {series_id}/{period}")
            _check_change(index_values[(code, period)], index_values[(code, prior)], value, f"{series_id}/{period}")
            result.append(_record(series_id, period, value, "percent_change", artifact))
    return result


def _existing(path: Path) -> dict[tuple[str, str], str]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        return {(r["series_id"], r["period"]): r["value"] for r in csv.DictReader(handle)}


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    records.sort(key=lambda r: (r["series_id"], r["period"]))
    if not records:
        raise PipelineError("EMAE: no se promueve una salida vacía")
    target_dir = root / "data" / "processed"
    log_dir = root / "data" / "logs" / "emae"
    target_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "emae.csv"
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
        raise PipelineError(f"EMAE: la nueva versión elimina {report['deleted']} observaciones")
    fd, temporary = tempfile.mkstemp(prefix="emae-", suffix=".csv", dir=target_dir)
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
    (log_dir / f"{run_id}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def run(root: Path, general_file: Path | None = None, sector_file: Path | None = None) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw = root / "data" / "raw"
    general = acquire("indec_emae_general", EMAE_GENERAL_URL, raw, general_file)
    sectors = acquire("indec_emae_sector", EMAE_SECTOR_URL, raw, sector_file)
    return promote(extract_general(general) + extract_sectors(sectors), root, run_id)

