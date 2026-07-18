from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import tempfile
import unicodedata
import urllib.request
import zipfile
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd

from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, acquire

TAX_CURRENT_PAGE = "https://www.argentina.gob.ar/economia/ingresospublicos/dniaf/recaudacion"
TAX_HISTORY_PAGE = "https://www.argentina.gob.ar/economia/ingresospublicos/pormes"
FISCAL_PAGE = "https://www.argentina.gob.ar/economia/sechacienda/infoestadistica"
REAL_BASE_PERIOD = "2025-12"

NOMINAL_SERIES = {
    "mecon_tax_revenue_total_nominal_monthly",
    "mecon_fiscal_primary_nominal_monthly",
    "mecon_fiscal_financial_nominal_monthly",
}

MONTHS = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12,
}


class _SectionLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.year: int | None = None
        self.pending_h4 = False
        self.links: dict[int, list[str]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "h4":
            self.pending_h4 = True
            return
        if tag != "a" or self.year is None:
            return
        href = dict(attrs).get("href")
        if href and re.search(r"\.(?:xls|xlsx|zip|rar)(?:\?.*)?$", href, re.I):
            self.links.setdefault(self.year, []).append(urljoin(FISCAL_PAGE, href))

    def handle_endtag(self, tag: str) -> None:
        if tag == "h4":
            self.pending_h4 = False

    def handle_data(self, data: str) -> None:
        if self.pending_h4 and re.fullmatch(r"\s*20\d{2}\s*", data):
            self.year = int(data.strip())


class _ExcelLinks(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href and re.search(r"\.xlsx?(?:\?.*)?$", href, re.I):
            self.links.append(urljoin(self.base_url, href))


def _html(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "argentina-economic-data/0.2"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read().decode("utf-8", errors="replace")
    except Exception as exc:
        raise PipelineError(f"finanzas públicas: no se pudo consultar {url}: {exc}") from exc


def discover_tax_urls(refresh_history: bool) -> list[str]:
    current = _ExcelLinks(TAX_CURRENT_PAGE)
    current.feed(_html(TAX_CURRENT_PAGE))
    if not current.links:
        raise PipelineError("recaudación: no se encontró la planilla vigente")
    urls = [current.links[-1]]
    if refresh_history:
        history = _ExcelLinks(TAX_HISTORY_PAGE)
        history.feed(_html(TAX_HISTORY_PAGE))
        urls = [url for url in history.links if (_year_from_url(url) or 0) >= 2017] + urls
    return list(dict.fromkeys(urls))


def discover_fiscal_urls(refresh_history: bool) -> list[str]:
    parser = _SectionLinks()
    parser.feed(_html(FISCAL_PAGE))
    current_year = max(parser.links, default=0)
    supported_current = [url for url in parser.links.get(current_year, []) if not url.lower().endswith(".rar")]
    if not supported_current:
        raise PipelineError("resultado fiscal: no se encontró una planilla vigente compatible")
    urls = [supported_current[-1]]
    if refresh_history:
        for year in range(2017, current_year):
            urls.extend(url for url in parser.links.get(year, []) if not url.lower().endswith(".rar"))
    return list(dict.fromkeys(urls))


def _year_from_url(url: str) -> int | None:
    matches = re.findall(r"(?:19|20)\d{2}", url)
    return int(matches[-1]) if matches else None


def _artifact_for_local(path: Path, source_id: str, source_url: str) -> Artifact:
    if not path.exists() or path.stat().st_size < 100:
        raise PipelineError(f"finanzas públicas: archivo local inválido: {path}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    retrieved = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return Artifact(source_id, source_url, path, digest, path.stat().st_size, retrieved)


def _download_many(urls: list[str], root: Path, prefix: str) -> list[Artifact]:
    artifacts: list[Artifact] = []
    for index, url in enumerate(urls):
        source_id = f"mecon_{prefix}_{index:03d}"
        artifacts.append(acquire(source_id, url, root / "data" / "raw", None))
    return artifacts


def _expand(artifact: Artifact) -> list[Artifact]:
    if artifact.path.suffix.lower() != ".zip":
        return [artifact]
    target = artifact.path.parent / "expanded"
    target.mkdir(exist_ok=True)
    try:
        with zipfile.ZipFile(artifact.path) as archive:
            archive.extractall(target)
    except (OSError, zipfile.BadZipFile) as exc:
        raise PipelineError(f"resultado fiscal: ZIP ilegible: {exc}") from exc
    files = [path for path in target.rglob("*") if path.suffix.lower() in {".xls", ".xlsx"}]
    if not files:
        raise PipelineError("resultado fiscal: el ZIP no contiene planillas")
    return [replace(artifact, path=path, size=path.stat().st_size) for path in files]


def _normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode().upper()
    return re.sub(r"\s+", " ", text).strip()


def _number(value: object, context: str) -> Decimal | None:
    if value is None or pd.isna(value) or str(value).strip() in {"", "-"}:
        return None
    try:
        number = Decimal(str(value).replace(".", "").replace(",", ".")) if isinstance(value, str) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise PipelineError(f"finanzas públicas: valor inválido en {context}: {value!r}") from exc
    return number


def _record(series_id: str, period: str, frequency: str, value: Decimal, unit: str,
            status: str, source_id: str, source_url: str, source_sha256: str,
            retrieved_at: str) -> dict[str, str]:
    return {
        "series_id": series_id, "period": period, "frequency": frequency,
        "value": format(value.quantize(Decimal("0.000001")), "f"), "unit": unit,
        "status": status, "source_id": source_id, "source_url": source_url,
        "source_sha256": source_sha256, "retrieved_at": retrieved_at,
    }


def extract_tax(artifact: Artifact) -> list[dict[str, str]]:
    try:
        workbook = pd.ExcelFile(artifact.path)
        sheet_name = "Internet" if "Internet" in workbook.sheet_names else workbook.sheet_names[0]
        sheet = pd.read_excel(artifact.path, sheet_name=sheet_name, header=None)
    except Exception as exc:
        raise PipelineError(f"recaudación: planilla ilegible {artifact.path.name}: {exc}") from exc
    year = None
    for value in sheet.iloc[:10].to_numpy().ravel():
        match = re.search(r"RECURSOS TRIBUTARIOS.*?((?:19|20)\d{2})", _normalize(value))
        if match:
            year = int(match.group(1))
            break
    if year is None:
        raise PipelineError(f"recaudación: no se encontró el año en {artifact.path.name}")
    total_rows = [i for i, row in sheet.iterrows() if any(_normalize(v) == "TOTAL REC. TRIBUTARIOS" for v in row if not pd.isna(v))]
    if len(total_rows) != 1:
        raise PipelineError(f"recaudación: fila total inesperada en {artifact.path.name}")
    header_row = None
    month_columns: dict[int, int] = {}
    for i, row in sheet.iloc[:15].iterrows():
        found = {MONTHS.get(_normalize(value).lower()[:3]): column for column, value in row.items() if not pd.isna(value)}
        found = {month: column for month, column in found.items() if month}
        if len(found) >= 6:
            header_row, month_columns = i, found
            break
    if header_row is None:
        raise PipelineError(f"recaudación: encabezado mensual ausente en {artifact.path.name}")
    records: list[dict[str, str]] = []
    for month, column in sorted(month_columns.items()):
        value = _number(sheet.iat[total_rows[0], column], f"recaudación/{year}-{month:02d}")
        if value is None:
            continue
        if value <= 0:
            raise PipelineError(f"recaudación: total no positivo en {year}-{month:02d}")
        records.append(_record(
            "mecon_tax_revenue_total_nominal_monthly", f"{year:04d}-{month:02d}", "monthly",
            value, "million_ars_current", "official", "mecon_tax_revenue", TAX_HISTORY_PAGE,
            artifact.sha256, artifact.retrieved_at,
        ))
    if not records:
        raise PipelineError(f"recaudación: planilla sin observaciones en {artifact.path.name}")
    return records


def _date_columns(sheet: pd.DataFrame) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in range(min(12, sheet.shape[0])):
        for column, value in sheet.iloc[row].items():
            if isinstance(value, (pd.Timestamp, datetime)):
                result.setdefault(value.strftime("%Y-%m"), int(column))
    return result


def _result_row(sheet: pd.DataFrame, label: str) -> int | None:
    candidates: list[tuple[int, int]] = []
    for index, row in sheet.iterrows():
        for value in row.iloc[:7]:
            normalized = _normalize(value)
            if normalized.startswith(label) and "SEGUN PROGRAMA" not in normalized:
                candidates.append((len(normalized), int(index)))
    return min(candidates)[1] if candidates else None


def extract_fiscal(artifact: Artifact) -> list[dict[str, str]]:
    try:
        workbook = pd.ExcelFile(artifact.path)
    except Exception as exc:
        raise PipelineError(f"resultado fiscal: planilla ilegible {artifact.path.name}: {exc}") from exc
    names = workbook.sheet_names
    # "VarMensual" es una hoja auxiliar con fórmulas históricas y no el cuadro
    # oficial del mes. Solo "Mensualización" contiene una serie mensual completa.
    monthly_names = [name for name in names if "MENSUALIZACION" in _normalize(name)]
    candidate_names = monthly_names or [name for name in names if "IMIG" in _normalize(name)] or names
    records: list[dict[str, str]] = []
    for name in candidate_names:
        sheet = pd.read_excel(artifact.path, sheet_name=name, header=None)
        dates = _date_columns(sheet)
        if not dates:
            continue
        rows = {
            "mecon_fiscal_primary_nominal_monthly": _result_row(sheet, "RESULTADO PRIMARIO"),
            "mecon_fiscal_financial_nominal_monthly": _result_row(sheet, "RESULTADO FINANCIERO"),
        }
        if any(row is None for row in rows.values()):
            continue
        for period, column in dates.items():
            if period < "2017-01":
                continue
            for series_id, row in rows.items():
                value = _number(sheet.iat[row, column], f"{series_id}/{period}")
                if value is None:
                    continue
                records.append(_record(
                    series_id, period, "monthly", value, "million_ars_current", "official",
                    "mecon_spn_cash_basis", FISCAL_PAGE, artifact.sha256, artifact.retrieved_at,
                ))
        if records:
            break
    return records


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_index(path: Path, series_id: str) -> dict[str, Decimal]:
    return {row["period"]: Decimal(row["value"]) for row in _read_rows(path) if row["series_id"] == series_id}


def calculate(nominal: list[dict[str, str]], inflation_path: Path, gdp_path: Path) -> list[dict[str, str]]:
    cpi = _load_index(inflation_path, "indec_ipc_general_index")
    if REAL_BASE_PERIOD not in cpi:
        raise PipelineError(f"finanzas públicas: falta IPC de {REAL_BASE_PERIOD}")
    gdp = _load_index(gdp_path, "indec_gdp_current_annual")
    result = list(nominal)
    real_by_series: dict[str, dict[str, Decimal]] = {}
    mappings = {
        "mecon_tax_revenue_total_nominal_monthly": "mecon_tax_revenue_total_real_monthly",
        "mecon_fiscal_primary_nominal_monthly": "mecon_fiscal_primary_real_monthly",
        "mecon_fiscal_financial_nominal_monthly": "mecon_fiscal_financial_real_monthly",
    }
    for row in nominal:
        period = row["period"]
        if period not in cpi:
            continue
        real_id = mappings[row["series_id"]]
        real = Decimal(row["value"]) * cpi[REAL_BASE_PERIOD] / cpi[period]
        real_by_series.setdefault(real_id, {})[period] = real
        result.append(_record(
            real_id, period, "monthly", real, "million_ars_dec_2025", "calculated",
            "datarg_mecon_public_finance", row["source_url"], row["source_sha256"], row["retrieved_at"],
        ))
    tax_real = real_by_series.get("mecon_tax_revenue_total_real_monthly", {})
    for period, value in tax_real.items():
        previous = f"{int(period[:4]) - 1:04d}{period[4:]}"
        if previous in tax_real:
            yoy = (value / tax_real[previous] - Decimal(1)) * Decimal(100)
            result.append(_calculated_record(
                "mecon_tax_revenue_total_real_yoy", period, "monthly", yoy, "percent_change", TAX_HISTORY_PAGE,
            ))
    annual_real: dict[str, dict[str, Decimal]] = {}
    for monthly_id, periods in real_by_series.items():
        annual_id = monthly_id.replace("_monthly", "_annual")
        by_year: dict[str, list[Decimal]] = {}
        for period, value in periods.items():
            by_year.setdefault(period[:4], []).append(value)
        for year, values in by_year.items():
            if len(values) == 12:
                total = sum(values, Decimal(0))
                annual_real.setdefault(annual_id, {})[year] = total
                source_url = TAX_HISTORY_PAGE if annual_id.startswith("mecon_tax_") else FISCAL_PAGE
                result.append(_calculated_record(annual_id, year, "annual", total, "million_ars_dec_2025", source_url))
    tax_annual = annual_real.get("mecon_tax_revenue_total_real_annual", {})
    for year, value in tax_annual.items():
        previous = str(int(year) - 1)
        if previous in tax_annual:
            yoy = (value / tax_annual[previous] - Decimal(1)) * Decimal(100)
            result.append(_calculated_record(
                "mecon_tax_revenue_total_real_annual_yoy", year, "annual", yoy, "percent_change", TAX_HISTORY_PAGE,
            ))
    nominal_by_series = {series_id: {} for series_id in NOMINAL_SERIES}
    for row in nominal:
        nominal_by_series[row["series_id"]][row["period"]] = Decimal(row["value"])
    for nominal_id, gdp_id in (
        ("mecon_fiscal_primary_nominal_monthly", "mecon_fiscal_primary_annual_gdp"),
        ("mecon_fiscal_financial_nominal_monthly", "mecon_fiscal_financial_annual_gdp"),
    ):
        by_year: dict[str, list[Decimal]] = {}
        for period, value in nominal_by_series[nominal_id].items():
            by_year.setdefault(period[:4], []).append(value)
        for year, values in by_year.items():
            if len(values) == 12 and year in gdp:
                ratio = sum(values, Decimal(0)) / gdp[year] * Decimal(100)
                result.append(_calculated_record(gdp_id, year, "annual", ratio, "percent_gdp"))
    return result


def _calculated_record(series_id: str, period: str, frequency: str, value: Decimal, unit: str,
                       source_url: str = FISCAL_PAGE) -> dict[str, str]:
    return _record(
        series_id, period, frequency, value, unit, "calculated", "datarg_mecon_public_finance",
        source_url, "calculated", datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    records.sort(key=lambda row: (row["series_id"], row["period"]))
    keys = [(row["series_id"], row["period"]) for row in records]
    if not records or len(keys) != len(set(keys)):
        raise PipelineError("finanzas públicas: salida vacía o con claves duplicadas")
    target_dir = root / "data" / "processed"
    log_dir = root / "data" / "logs" / "fiscal"
    target_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "fiscal.csv"
    old_rows = _read_rows(target)
    old = {(row["series_id"], row["period"]): row["value"] for row in old_rows}
    new = {(row["series_id"], row["period"]): row["value"] for row in records}
    report = {
        "run_id": run_id, "rows": len(records), "series": len({row["series_id"] for row in records}),
        "min_period": min(row["period"] for row in records), "max_period": max(row["period"] for row in records),
        "created": len(new.keys() - old.keys()), "deleted": len(old.keys() - new.keys()),
        "modified": sum(old[key] != new[key] for key in old.keys() & new.keys()),
    }
    fd, temporary = tempfile.mkstemp(prefix="fiscal-", suffix=".csv", dir=target_dir)
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
    (log_dir / f"{run_id}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def run(root: Path, tax_files: list[Path] | None = None, fiscal_files: list[Path] | None = None,
        refresh_history: bool = False) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if tax_files:
        tax_artifacts = [_artifact_for_local(path, f"mecon_tax_local_{i}", TAX_HISTORY_PAGE) for i, path in enumerate(tax_files)]
    else:
        tax_artifacts = _download_many(discover_tax_urls(refresh_history), root, "tax_revenue")
    if fiscal_files:
        fiscal_artifacts = [_artifact_for_local(path, f"mecon_fiscal_local_{i}", FISCAL_PAGE) for i, path in enumerate(fiscal_files)]
    else:
        fiscal_artifacts = _download_many(discover_fiscal_urls(refresh_history), root, "fiscal_result")
    existing = [row for row in _read_rows(root / "data" / "processed" / "fiscal.csv") if row["series_id"] in NOMINAL_SERIES]
    nominal = {(row["series_id"], row["period"]): row for row in existing}
    for artifact in tax_artifacts:
        for row in extract_tax(artifact):
            nominal[(row["series_id"], row["period"])] = row
    for outer in fiscal_artifacts:
        for artifact in _expand(outer):
            for row in extract_fiscal(artifact):
                nominal[(row["series_id"], row["period"])] = row
    present = {series_id for series_id, _ in nominal}
    if present != NOMINAL_SERIES:
        raise PipelineError(f"finanzas públicas: faltan series nominales: {sorted(NOMINAL_SERIES - present)}")
    records = calculate(
        list(nominal.values()), root / "data" / "processed" / "inflation.csv",
        root / "data" / "processed" / "gdp.csv",
    )
    return promote(records, root, run_id)
