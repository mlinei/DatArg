from __future__ import annotations

import csv
import html
import json
import os
import re
import tempfile
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import urljoin, urlparse

import pandas as pd

from .inflation import Artifact, PipelineError, acquire


INDEX_URL = "https://www.argentina.gob.ar/economia/finanzas/datos-trimestrales-de-la-deuda"
FALLBACK_URL = "https://www.argentina.gob.ar/sites/default/files/deuda_publica_31-03-2026.xlsx"
SOURCE_ID = "mecon_quarterly_treasury_maturity_profile"
OUTPUT_COLUMNS = (
    "series_id", "snapshot_date", "period", "frequency", "service_type", "category",
    "detail_level", "source_row", "instrument", "value", "unit", "status",
    "source_id", "source_url", "source_sha256", "retrieved_at",
)
SHEETS = {
    "A.3.2": "capital",
    "A.3.3": "interest",
    "A.3.4": "capital",
    "A.3.5": "interest",
}
CATEGORY_LABELS = {
    "PRÉSTAMOS": "loans",
    "ADELANTOS TRANSITORIOS BCRA": "bcra_advances",
    "TÍTULOS PÚBLICOS Y LETRAS DEL TESORO": "securities",
}
CATEGORY_NAMES = {
    "total": "Total",
    "loans": "Préstamos",
    "bcra_advances": "Adelantos transitorios BCRA",
    "securities": "Títulos públicos y Letras del Tesoro",
}


def discover_latest_url() -> str:
    request = urllib.request.Request(INDEX_URL, headers={"User-Agent": "argentina-economic-data/0.2"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            page = response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")
    except Exception as exc:
        raise PipelineError(f"vencimientos: no se pudo consultar el índice oficial: {exc}") from exc
    candidates = []
    for href in re.findall(r'href=["\']([^"\']+deuda_publica_[^"\']+\.xlsx)["\']', page, flags=re.I):
        url = urljoin(INDEX_URL, html.unescape(href))
        match = re.search(r"deuda_publica_(\d{2})-(\d{2})-(\d{4})", url, flags=re.I)
        if match and urlparse(url).hostname in {"www.argentina.gob.ar", "argentina.gob.ar"}:
            day, month, year = map(int, match.groups())
            candidates.append((datetime(year, month, day), url))
    if not candidates:
        raise PipelineError("vencimientos: la página oficial no expone ningún libro trimestral reconocible")
    return max(candidates)[1]


def _snapshot_date(sheet: pd.DataFrame) -> str:
    text = " ".join(str(value) for value in sheet.iloc[:10, :4].to_numpy().ravel() if not pd.isna(value))
    match = re.search(r"(?:Stock de deuda y tipo de cambio|Tipo de cambio)\s+(\d{2})/(\d{2})/(\d{4})", text, flags=re.I)
    if not match:
        raise PipelineError("vencimientos: no se encontró la fecha de corte del informe")
    day, month, year = match.groups()
    return f"{year}-{month}-{day}"


def _row_kind(label: str, current_category: str | None) -> tuple[str, str]:
    normalized = re.sub(r"\s+", " ", label).strip()
    if normalized == "TOTAL":
        return "total", "total"
    if normalized in {"CORTO PLAZO", "MEDIANO Y LARGO PLAZO"}:
        return "term", "total"
    if normalized in CATEGORY_LABELS:
        return "category", CATEGORY_LABELS[normalized]
    return "detail", current_category or "unclassified"


def _series_id(service_type: str, category: str, detail_level: str, source_row: int) -> str:
    if detail_level in {"total", "category"}:
        return f"mecon_treasury_maturity_{service_type}_{category}"
    return f"mecon_treasury_maturity_{service_type}_row_{source_row}"


def extract(artifact: Artifact) -> list[dict[str, str]]:
    try:
        book = pd.ExcelFile(artifact.path)
    except Exception as exc:
        raise PipelineError(f"vencimientos: libro oficial ilegible: {exc}") from exc
    missing = set(SHEETS) - set(book.sheet_names)
    if missing:
        raise PipelineError(f"vencimientos: faltan hojas oficiales: {', '.join(sorted(missing))}")

    records: list[dict[str, str]] = []
    snapshots: set[str] = set()
    sheet_totals: dict[tuple[str, str], Decimal] = {}
    category_totals: dict[tuple[str, str], Decimal] = {}
    for sheet_name, service_type in SHEETS.items():
        sheet = pd.read_excel(book, sheet_name=sheet_name, header=None)
        snapshot = _snapshot_date(sheet)
        snapshots.add(snapshot)
        periods: dict[int, str] = {}
        for column in range(2, sheet.shape[1]):
            raw = sheet.iat[8, column]
            if isinstance(raw, (datetime, pd.Timestamp)):
                periods[column] = pd.Timestamp(raw).strftime("%Y-%m")
        if not periods:
            raise PipelineError(f"vencimientos: {sheet_name} no contiene meses")

        current_category: str | None = None
        for row_index in range(10, sheet.shape[0]):
            raw_label = sheet.iat[row_index, 1]
            if pd.isna(raw_label):
                continue
            label = re.sub(r"\s+", " ", str(raw_label)).strip()
            detail_level, category = _row_kind(label, current_category)
            if detail_level == "category":
                current_category = category
            if detail_level == "total":
                current_category = None
            if detail_level == "detail" and category == "unclassified":
                continue
            for column, period in periods.items():
                raw_value = sheet.iat[row_index, column]
                if pd.isna(raw_value):
                    continue
                try:
                    value = Decimal(str(raw_value))
                except Exception as exc:
                    raise PipelineError(f"vencimientos: valor inválido en {sheet_name}, fila {row_index + 1}") from exc
                if value < 0:
                    raise PipelineError(f"vencimientos: valor negativo en {sheet_name}, fila {row_index + 1}")
                if value == 0 and detail_level not in {"total", "category"}:
                    continue
                record = {
                    "series_id": _series_id(service_type, category, detail_level, row_index + 1),
                    "snapshot_date": snapshot,
                    "period": period,
                    "frequency": "monthly",
                    "service_type": service_type,
                    "category": category,
                    "detail_level": detail_level,
                    "source_row": str(row_index + 1),
                    "instrument": CATEGORY_NAMES.get(category, label) if detail_level in {"total", "category"} else label,
                    "value": format(value.quantize(Decimal("0.000001")), "f"),
                    "unit": "million_usd",
                    "status": "official_projection",
                    "source_id": SOURCE_ID,
                    "source_url": artifact.url,
                    "source_sha256": artifact.sha256,
                    "retrieved_at": artifact.retrieved_at,
                }
                records.append(record)
                if detail_level == "total":
                    sheet_totals[service_type, period] = value
                elif detail_level == "category":
                    category_totals[service_type, period, category] = value

    if len(snapshots) != 1:
        raise PipelineError(f"vencimientos: las hojas tienen fechas de corte distintas: {sorted(snapshots)}")
    periods = sorted({record["period"] for record in records if record["detail_level"] == "total"})
    snapshot_period = pd.Period(next(iter(snapshots))[:7], freq="M")
    expected_first = str(snapshot_period + 1)
    expected_last = f"{snapshot_period.year + 1}-12"
    if not periods or periods[0] != expected_first or periods[-1] != expected_last:
        raise PipelineError(f"vencimientos: cobertura mensual inesperada ({periods[:1]} a {periods[-1:]})")
    for key, total in sheet_totals.items():
        category_sum = sum(
            (category_totals.get((*key, category), Decimal(0)) for category in CATEGORY_NAMES if category != "total"),
            Decimal(0),
        )
        if abs(total - category_sum) > Decimal("0.00001"):
            raise PipelineError(f"vencimientos: las categorías no suman el total en {key[0]} {key[1]}")
    return records


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    target_dir = root / "data" / "processed"
    log_dir = root / "data" / "logs" / "debt_maturities"
    target_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "treasury_maturities.csv"
    snapshot = records[0]["snapshot_date"]
    merged: dict[tuple[str, str, str, str], dict[str, str]] = {}
    if target.exists():
        with target.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row["snapshot_date"] != snapshot:
                    merged[(row["snapshot_date"], row["service_type"], row["source_row"], row["period"])] = row
    for row in records:
        merged[(row["snapshot_date"], row["service_type"], row["source_row"], row["period"])] = row
    output = sorted(merged.values(), key=lambda row: (
        row["snapshot_date"], row["period"], row["service_type"], int(row["source_row"])
    ))
    report = {
        "run_id": run_id,
        "snapshot_date": snapshot,
        "rows": len(records),
        "stored_rows": len(output),
        "period_from": min(row["period"] for row in records),
        "period_through": max(row["period"] for row in records),
    }
    fd, temporary = tempfile.mkstemp(prefix="treasury-maturities-", suffix=".csv", dir=target_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader()
            writer.writerows(output)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    (log_dir / f"{run_id}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def run(root: Path, source_file: Path | None = None) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    source_url = FALLBACK_URL if source_file else discover_latest_url()
    artifact = acquire(SOURCE_ID, source_url, root / "data" / "raw", source_file)
    return promote(extract(artifact), root, run_id)
