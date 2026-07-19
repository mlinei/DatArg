from __future__ import annotations

import csv
import json
import os
import re
import tempfile
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd

from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, acquire

PORTAL_URL = "https://www.argentina.gob.ar/jefatura/presupuestaria/inversion-publica/portal-de-datos-de-inversion-publica"
DEFAULT_RESOURCE_URL = "https://www.argentina.gob.ar/sites/default/files/mayo_2026_-series_de_inversion_publica_y_gastos_de_capital_actualizado_para_web.xlsx"

PUBLIC_FUNCTIONS = {
    "TRANSPORTE": "transport",
    "ENERGIA, COMBUSTIBLES Y MINERIA": "energy_mining",
    "AGUA POTABLE Y ALCANTARILLADO": "water_sanitation",
    "VIVIENDA Y URBANISMO": "housing_urbanism",
    "CIENCIA Y TECNICA": "science_technology",
    "EDUCACION Y CULTURA": "education_culture",
    "SALUD": "health",
    "DEFENSA": "defense",
    "RESTO": "other",
}

CAPITAL_FUNCTIONS = {
    "ENERGIA": "energy",
    "TRANSPORTE": "transport",
    "EDUCACION": "education",
    "VIVIENDA": "housing",
    "AGUA": "water",
    "OTROS Y FFS": "other",
}


class _Links(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(urljoin(self.base_url, href))


def _html(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "argentina-economic-data/0.2"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read().decode("utf-8", errors="replace")
    except Exception as exc:
        raise PipelineError(f"inversión pública: no se pudo consultar {url}: {exc}") from exc


def discover_resource_url() -> str:
    portal = _Links(PORTAL_URL)
    portal.feed(_html(PORTAL_URL))
    landing = next((url for url in portal.links if "/files/" in url and "inversion" in url.lower()), None)
    if landing is None:
        raise PipelineError("inversión pública: no se encontró el enlace a las series")
    if re.search(r"\.xlsx(?:\?.*)?$", landing, re.I) and "/sites/default/files/" in landing:
        return landing
    resource = _Links(landing)
    resource.feed(_html(landing))
    direct = next((url for url in resource.links if re.search(r"\.xlsx(?:\?.*)?$", url, re.I)), None)
    if direct is None:
        raise PipelineError("inversión pública: la página del recurso no contiene una planilla XLSX")
    return direct


def _normalized(value: object) -> str:
    import unicodedata

    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode().upper()
    return re.sub(r"\s+", " ", text).strip()


def _decimal(value: object, context: str) -> Decimal:
    if pd.isna(value):
        raise PipelineError(f"inversión pública: valor ausente en {context}")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise PipelineError(f"inversión pública: valor inválido en {context}: {value!r}") from exc
    if result < 0:
        raise PipelineError(f"inversión pública: valor negativo en {context}")
    return result


def _record(series_id: str, period: str, value: Decimal, unit: str, artifact: Artifact) -> dict[str, str]:
    return {
        "series_id": series_id, "period": period, "frequency": "annual",
        "value": format(value.quantize(Decimal("0.000001")), "f"), "unit": unit,
        "status": "official", "source_id": "jgm_public_investment_series",
        "source_url": PORTAL_URL, "source_sha256": artifact.sha256,
        "retrieved_at": artifact.retrieved_at,
    }


def _year(raw: object) -> int | None:
    text = str(raw).strip()
    if "*" in text:
        return None
    try:
        year = int(float(text))
    except (TypeError, ValueError):
        return None
    return year if 1900 <= year <= 2100 else None


def _read_sheet(artifact: Artifact, name: str) -> pd.DataFrame:
    try:
        sheet = pd.read_excel(artifact.path, sheet_name=name, header=None)
    except Exception as exc:
        raise PipelineError(f"inversión pública: no se pudo leer {name}: {exc}") from exc
    if sheet.shape[0] < 7 or sheet.shape[1] < 10:
        raise PipelineError(f"inversión pública: dimensiones inesperadas en {name}: {sheet.shape}")
    return sheet


def _total_series(artifact: Artifact, sheet_name: str, series_id: str, unit: str,
                  first_year: int, label: str) -> tuple[list[dict[str, str]], dict[str, Decimal]]:
    sheet = _read_sheet(artifact, sheet_name)
    if label not in _normalized(sheet.iat[2, 0]):
        raise PipelineError(f"inversión pública: título inesperado en {sheet_name}")
    records: list[dict[str, str]] = []
    values: dict[str, Decimal] = {}
    for column in range(1, sheet.shape[1]):
        year = _year(sheet.iat[5, column])
        if year is None or pd.isna(sheet.iat[6, column]):
            continue
        period = str(year)
        value = _decimal(sheet.iat[6, column], f"{series_id}/{period}")
        if period in values:
            raise PipelineError(f"inversión pública: período duplicado en {series_id}/{period}")
        values[period] = value
        records.append(_record(series_id, period, value, unit, artifact))
    if not values or min(values) != str(first_year) or max(values) < "2025":
        raise PipelineError(f"inversión pública: cobertura inesperada en {series_id}")
    return records, values


def _function_series(artifact: Artifact, sheet_name: str, prefix: str, unit: str,
                     functions: dict[str, str], first_year: int) -> tuple[list[dict[str, str]], dict[tuple[str, str], Decimal]]:
    sheet = _read_sheet(artifact, sheet_name)
    rows: dict[str, int] = {}
    for row in range(6, sheet.shape[0]):
        key = _normalized(sheet.iat[row, 0])
        if key in functions:
            rows[functions[key]] = row
    expected = set(functions.values())
    if set(rows) != expected:
        raise PipelineError(f"inversión pública: funciones incompletas en {sheet_name}: {sorted(expected - set(rows))}")
    records: list[dict[str, str]] = []
    values: dict[tuple[str, str], Decimal] = {}
    for column in range(1, sheet.shape[1]):
        year = _year(sheet.iat[5, column])
        if year is None:
            continue
        period = str(year)
        for function, row in rows.items():
            value = _decimal(sheet.iat[row, column], f"{prefix}_{function}/{period}")
            series_id = f"{prefix}_{function}"
            values[(function, period)] = value
            records.append(_record(series_id, period, value, unit, artifact))
    periods = {period for _, period in values}
    if not periods or min(periods) != str(first_year) or max(periods) < "2025":
        raise PipelineError(f"inversión pública: cobertura de funciones inesperada en {sheet_name}")
    return records, values


def extract(artifact: Artifact) -> list[dict[str, str]]:
    public_index_records, public_index = _total_series(
        artifact, "serie 2", "jgm_public_investment_real_index", "index_2019_100", 1995,
        "INVERSION PUBLICA TOTAL",
    )
    public_gdp_records, public_gdp = _total_series(
        artifact, "serie 3", "jgm_public_investment_gdp_ratio", "percent_gdp", 1995,
        "INVERSION PUBLICA TOTAL",
    )
    function_gdp_records, function_gdp = _function_series(
        artifact, "serie 4", "jgm_public_investment_function_gdp_ratio", "percent_gdp",
        PUBLIC_FUNCTIONS, 1995,
    )
    function_index_records, _ = _function_series(
        artifact, "serie 6", "jgm_public_investment_function_real_index", "index_2019_100",
        {key: value for key, value in PUBLIC_FUNCTIONS.items() if value != "other"}, 1995,
    )
    capital_gdp_records, capital_gdp = _total_series(
        artifact, "serie 7", "jgm_capital_expenditure_gdp_ratio", "percent_gdp", 1997,
        "GASTOS DE CAPITAL",
    )
    capital_index_records, capital_index = _total_series(
        artifact, "serie 9", "jgm_capital_expenditure_real_index", "index_2019_100", 1997,
        "GASTOS DE CAPITAL",
    )
    capital_function_gdp_records, _ = _function_series(
        artifact, "serie 10", "jgm_capital_expenditure_function_gdp_ratio", "percent_gdp",
        CAPITAL_FUNCTIONS, 2016,
    )
    capital_function_index_records, _ = _function_series(
        artifact, "serie 12", "jgm_capital_expenditure_function_real_index", "index_2019_100",
        CAPITAL_FUNCTIONS, 2016,
    )
    if public_index.get("2019") != Decimal(100) or capital_index.get("2019") != Decimal(100):
        raise PipelineError("inversión pública: base 2019 distinta de 100")
    for period, total in public_gdp.items():
        component_sum = sum(
            (value for (function, year), value in function_gdp.items() if year == period), Decimal(0)
        )
        if abs(total - component_sum) > Decimal("0.000001"):
            raise PipelineError(f"inversión pública: componentes no suman el total en {period}")
    if public_gdp["2025"] >= public_gdp["2023"] or capital_gdp["2025"] >= capital_gdp["2023"]:
        raise PipelineError("inversión pública: control de tendencia reciente inesperado")
    return (
        public_index_records + public_gdp_records + function_gdp_records + function_index_records
        + capital_gdp_records + capital_index_records + capital_function_gdp_records
        + capital_function_index_records
    )


def _existing(path: Path) -> dict[tuple[str, str], str]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        return {(row["series_id"], row["period"]): row["value"] for row in csv.DictReader(handle)}


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    records.sort(key=lambda row: (row["series_id"], row["period"]))
    keys = [(row["series_id"], row["period"]) for row in records]
    if not records or len(keys) != len(set(keys)):
        raise PipelineError("inversión pública: salida vacía o con claves duplicadas")
    target_dir = root / "data" / "processed"
    log_dir = root / "data" / "logs" / "public_investment"
    target_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "public_investment.csv"
    old = _existing(target)
    new = {(row["series_id"], row["period"]): row["value"] for row in records}
    report = {
        "run_id": run_id, "rows": len(records), "series": len({row["series_id"] for row in records}),
        "min_period": min(row["period"] for row in records), "max_period": max(row["period"] for row in records),
        "created": len(new.keys() - old.keys()), "deleted": len(old.keys() - new.keys()),
        "modified": sum(old[key] != new[key] for key in old.keys() & new.keys()),
    }
    if old and report["deleted"]:
        raise PipelineError(f"inversión pública: la nueva fuente elimina {report['deleted']} observaciones")
    fd, temporary = tempfile.mkstemp(prefix="public-investment-", suffix=".csv", dir=target_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(records)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    (log_dir / f"{run_id}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def run(root: Path, source_file: Path | None = None) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    resource_url = DEFAULT_RESOURCE_URL if source_file else discover_resource_url()
    artifact = acquire("jgm_public_investment_series", resource_url, root / "data" / "raw", source_file)
    return promote(extract(artifact), root, run_id)
