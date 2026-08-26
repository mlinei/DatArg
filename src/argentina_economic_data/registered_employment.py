from __future__ import annotations

import csv
import html
import json
import os
import re
import tempfile
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

import pandas as pd

from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, acquire

LANDING_URL = "https://www.argentina.gob.ar/trabajo/estadisticas/situacion-y-evolucion-del-trabajo-registrado"
FALLBACK_URL = "https://www.argentina.gob.ar/sites/default/files/trabajoregistrado_2605_estadisticas.xlsx"

SECTORS = {
    "agricultura ganaderia caza y silvicultura": ("agriculture", "Agricultura"),
    "pesca": ("fishing", "Pesca"),
    "explotacion de minas y canteras": ("mining", "Minería"),
    "industrias manufactureras": ("manufacturing", "Industria"),
    "suministro de electricidad gas y agua": ("utilities", "Electricidad, gas y agua"),
    "construccion": ("construction", "Construcción"),
    "comercio y reparaciones": ("commerce", "Comercio"),
    "hoteles y restaurantes": ("hotels_restaurants", "Hoteles y restaurantes"),
    "transporte almacenamiento y comunicacion": ("transport_communications", "Transporte y comunicaciones"),
    "intermediacion financiera": ("finance", "Intermediación financiera"),
    "actividades inmobiliarias empresariales y de alquiler": ("business_services", "Servicios empresariales"),
    "ensenanza": ("education", "Enseñanza"),
    "servicios sociales y de salud": ("health", "Salud"),
    "servicios comunitarios sociales y personales": ("community_services", "Servicios comunitarios"),
    "sin especificar": ("unspecified", "Sin especificar"),
    "total": ("total", "Total"),
}

PROVINCES = {
    "buenos aires": ("buenos_aires", "Buenos Aires"),
    "cdad autonoma de buenos aires": ("caba", "CABA"),
    "catamarca 3/": ("catamarca", "Catamarca"),
    "chaco": ("chaco", "Chaco"), "chubut": ("chubut", "Chubut"),
    "cordoba": ("cordoba", "Córdoba"), "corrientes": ("corrientes", "Corrientes"),
    "entre rios": ("entre_rios", "Entre Ríos"), "formosa": ("formosa", "Formosa"),
    "jujuy": ("jujuy", "Jujuy"), "la pampa": ("la_pampa", "La Pampa"),
    "la rioja": ("la_rioja", "La Rioja"), "mendoza": ("mendoza", "Mendoza"),
    "misiones": ("misiones", "Misiones"), "neuquen": ("neuquen", "Neuquén"),
    "rio negro": ("rio_negro", "Río Negro"), "salta": ("salta", "Salta"),
    "san juan": ("san_juan", "San Juan"), "san luis": ("san_luis", "San Luis"),
    "santa cruz": ("santa_cruz", "Santa Cruz"), "santa fe": ("santa_fe", "Santa Fe"),
    "santiago del estero": ("santiago_del_estero", "Santiago del Estero"),
    "tierra del fuego": ("tierra_del_fuego", "Tierra del Fuego"),
    "tucuman": ("tucuman", "Tucumán"),
}

MONTHS = {name: index for index, name in enumerate(
    ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"), 1
)}


def _clean(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode().lower()
    return " ".join(text.replace("\n", " ").replace(",", " ").replace(".", " ").split())


def _source_url() -> str:
    try:
        request = Request(LANDING_URL, headers={"User-Agent": "DatArg/1.0"})
        with urlopen(request, timeout=30) as response:
            page = response.read().decode("utf-8", errors="ignore")
        links = re.findall(r'href=["\']([^"\']*trabajoregistrado_\d{4}_estadisticas\.xlsx[^"\']*)', page, re.I)
        candidates: list[str] = []
        for link in links:
            link = html.unescape(link)
            embedded = re.search(r"https?://[^\s\"']+trabajoregistrado_\d{4}_estadisticas\.xlsx", link, re.I)
            url = embedded.group(0) if embedded else urljoin(LANDING_URL, link)
            parsed = urlparse(url)
            if parsed.scheme in {"http", "https"} and parsed.hostname in {
                "argentina.gob.ar", "www.argentina.gob.ar"
            }:
                candidates.append(url)
        if candidates:
            return max(candidates, key=lambda url: re.search(r"_(\d{4})_", url).group(1))
    except Exception:
        pass
    return FALLBACK_URL


def _period(value: object) -> str | None:
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.strftime("%Y-%m")
    match = re.fullmatch(r"\s*([a-záéíóú]{3})-(\d{2,4})\**\s*", str(value).lower())
    if not match:
        return None
    month = MONTHS.get(_clean(match.group(1)))
    if not month:
        return None
    year = int(match.group(2))
    if year < 100:
        year += 2000
    return f"{year:04d}-{month:02d}"


def _record(series_id: str, period: str, value: Decimal, unit: str, artifact: Artifact) -> dict[str, str]:
    return {
        "series_id": series_id, "period": period, "frequency": "monthly",
        "value": format(value.quantize(Decimal("0.000001")), "f"), "unit": unit,
        "status": "official_provisional", "source_id": artifact.source_id,
        "source_url": artifact.url, "source_sha256": artifact.sha256,
        "retrieved_at": artifact.retrieved_at,
    }


def _sheet_records(sheet: pd.DataFrame, mapping: dict[str, tuple[str, str]], dimension: str,
                   artifact: Artifact) -> tuple[list[dict[str, str]], dict[str, dict[str, Decimal]]]:
    headers = {_clean(sheet.iat[1, column]): column for column in range(1, sheet.shape[1])}
    missing = set(mapping) - set(headers)
    if missing:
        raise PipelineError(f"empleo registrado: columnas ausentes en {dimension}: {sorted(missing)}")
    levels: dict[str, dict[str, Decimal]] = {slug: {} for slug, _ in mapping.values()}
    for row in range(2, sheet.shape[0]):
        period = _period(sheet.iat[row, 0])
        if period is None:
            if any(levels.values()):
                break
            continue
        for header, (slug, _) in mapping.items():
            raw = sheet.iat[row, headers[header]]
            if pd.isna(raw):
                raise PipelineError(f"empleo registrado: valor ausente en {dimension}/{slug}/{period}")
            value = Decimal(str(raw))
            if value < 0:
                raise PipelineError(f"empleo registrado: valor negativo en {dimension}/{slug}/{period}")
            levels[slug][period] = value
    periods = sorted(next(iter(levels.values())))
    if not periods or periods[0] != "2009-01":
        raise PipelineError(f"empleo registrado: inicio inesperado en {dimension}: {periods[:1]}")
    expected = pd.period_range(periods[0], periods[-1], freq="M").astype(str).tolist()
    if periods != expected or any(sorted(values) != expected for values in levels.values()):
        raise PipelineError(f"empleo registrado: cobertura mensual incompleta en {dimension}")
    records: list[dict[str, str]] = []
    for slug, values in levels.items():
        base = values[periods[0]]
        prefix = f"trabajo_private_registered_{dimension}_{slug}"
        for index, period in enumerate(periods):
            level = values[period]
            records.append(_record(f"{prefix}_level", period, level, "thousand_people", artifact))
            records.append(_record(f"{prefix}_index", period, level / base * 100, "index_jan_2009_100", artifact))
            if index >= 12:
                yoy = (level / values[periods[index - 12]] - 1) * 100
                records.append(_record(f"{prefix}_yoy", period, yoy, "percent", artifact))
    return records, levels


def extract(artifact: Artifact) -> list[dict[str, str]]:
    try:
        sector_sheet = pd.read_excel(artifact.path, sheet_name="A.2.2", header=None, usecols=range(18))
        province_sheet = pd.read_excel(artifact.path, sheet_name="A.5.2", header=None, usecols=range(26))
    except ValueError as exc:
        raise PipelineError(f"empleo registrado: hojas oficiales ausentes: {exc}") from exc
    sector_records, sector_levels = _sheet_records(sector_sheet, SECTORS, "sector", artifact)
    province_records, province_levels = _sheet_records(province_sheet, PROVINCES, "province", artifact)
    periods = sorted(sector_levels["total"])
    for period in periods:
        branch_sum = sum(values[period] for slug, values in sector_levels.items() if slug != "total")
        if abs(branch_sum - sector_levels["total"][period]) > Decimal("0.1"):
            raise PipelineError(f"empleo registrado: ramas no suman el total en {period}")
        province_sum = sum(values[period] for values in province_levels.values())
        if abs(province_sum - sector_levels["total"][period]) / sector_levels["total"][period] > Decimal("0.01"):
            raise PipelineError(f"empleo registrado: provincias difieren del total en {period}")
    return sector_records + province_records


def _existing(path: Path) -> set[tuple[str, str]]:
    if not path.exists():
        return set()
    with path.open(encoding="utf-8", newline="") as handle:
        return {(row["series_id"], row["period"]) for row in csv.DictReader(handle)}


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    records.sort(key=lambda row: (row["series_id"], row["period"]))
    target_dir = root / "data" / "processed"
    log_dir = root / "data" / "logs" / "registered_employment"
    target_dir.mkdir(parents=True, exist_ok=True); log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "registered_employment.csv"
    old, new = _existing(target), {(row["series_id"], row["period"]) for row in records}
    deleted = len(old - new)
    if old and deleted:
        raise PipelineError(f"empleo registrado: la nueva versión elimina {deleted} observaciones")
    report = {
        "run_id": run_id, "rows": len(records), "series": len({row["series_id"] for row in records}),
        "created": len(new - old), "deleted": deleted,
        "min_period": min(row["period"] for row in records), "max_period": max(row["period"] for row in records),
    }
    fd, temporary = tempfile.mkstemp(prefix="registered-employment-", suffix=".csv", dir=target_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS); writer.writeheader(); writer.writerows(records)
            handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    (log_dir / f"{run_id}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def run(root: Path, source_file: Path | None = None) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    url = _source_url() if source_file is None else FALLBACK_URL
    artifact = acquire("trabajo_registered_employment_sipa", url, root / "data" / "raw", source_file)
    return promote(extract(artifact), root, run_id)
