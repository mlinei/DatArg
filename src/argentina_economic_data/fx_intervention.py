from __future__ import annotations

import csv
import json
import os
import re
import tempfile
import urllib.error
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from pypdf import PdfReader

from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, acquire

BASE_URL = "https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias"
VARIABLE_ID = 78
SOURCE_ID = "bcra_fx_market_intervention"
FUTURES_SOURCE_ID = "bcra_fx_futures_position"
FUTURES_BASE_URL = "https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas"
FIRST_PERIOD = "2003-01-02"
FUTURES_SERIES = {
    "bcra_fx_futures_short_position",
    "bcra_fx_futures_long_position",
    "bcra_fx_futures_net_short_position",
}
NUMBER_RE = re.compile(r"[-−]?\d{1,3}(?:\.\d{3})*,\d{2}")


def extract(artifact: Artifact) -> list[dict[str, str]]:
    try:
        payload = json.loads(artifact.path.read_text(encoding="utf-8"))
        result = payload["results"][0]
        observations = result["detalle"]
    except Exception as exc:
        raise PipelineError(f"intervención BCRA: esquema inválido: {exc}") from exc
    if payload.get("status") != 200 or result.get("idVariable") != VARIABLE_ID:
        raise PipelineError("intervención BCRA: respuesta inesperada")

    records: list[dict[str, str]] = []
    for row in observations:
        try:
            period = date.fromisoformat(row["fecha"]).isoformat()
            value = Decimal(str(row["valor"]))
        except (KeyError, ValueError, InvalidOperation) as exc:
            raise PipelineError("intervención BCRA: observación inválida") from exc
        records.append({
            "series_id": "bcra_fx_intervention_daily",
            "period": period,
            "frequency": "daily",
            "value": format(value.quantize(Decimal("0.000001")), "f"),
            "unit": "million_usd",
            "status": "official",
            "source_id": SOURCE_ID,
            "source_url": artifact.url,
            "source_sha256": artifact.sha256,
            "retrieved_at": artifact.retrieved_at,
        })
    return records


def aggregate(daily: list[dict[str, str]]) -> list[dict[str, str]]:
    totals: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
    for row in daily:
        totals[("monthly", row["period"][:7])] += Decimal(row["value"])
        totals[("annual", row["period"][:4])] += Decimal(row["value"])
    template = daily[-1]
    records = list(daily)
    for (frequency, period), value in sorted(totals.items()):
        records.append(template | {
            "series_id": f"bcra_fx_intervention_{frequency}",
            "period": period,
            "frequency": frequency,
            "value": format(value.quantize(Decimal("0.000001")), "f"),
            "status": "calculated",
        })
    return records


def _spanish_decimal(value: str) -> Decimal:
    try:
        return Decimal(value.replace("−", "-").replace(".", "").replace(",", "."))
    except InvalidOperation as exc:
        raise PipelineError(f"posición en futuros BCRA: número inválido {value!r}") from exc


def _futures_url(period: str) -> str:
    year, month = period.split("-")
    suffix = f"{month}{year}" if int(year) <= 2024 else f"{month}{year[2:]}"
    return f"{FUTURES_BASE_URL}/temp{suffix}.pdf"


def _extract_section_iv_values(page: str) -> tuple[Decimal, Decimal, Decimal]:
    values = [_spanish_decimal(item) for item in NUMBER_RE.findall(page[:1000])]
    if len(values) < 5:
        raise PipelineError("posición en futuros BCRA: sección IV.1.b incompleta")
    _, derivatives, short_signed, long_signed, _ = values[:5]
    if short_signed > 0 or long_signed < 0:
        raise PipelineError("posición en futuros BCRA: signos inesperados")
    if abs(derivatives - (short_signed + long_signed)) > Decimal("0.05"):
        raise PipelineError("posición en futuros BCRA: el neto no concilia con cortos y largos")
    return -short_signed, long_signed, -derivatives


def extract_futures(artifact: Artifact) -> list[dict[str, str]]:
    """Extrae la posición nocional del BCRA liquidada en pesos de la sección IV.1.b."""
    try:
        reader = PdfReader(str(artifact.path))
        cover = reader.pages[0].extract_text() or ""
        page = reader.pages[3].extract_text() or ""
    except Exception as exc:
        raise PipelineError(f"posición en futuros BCRA: PDF inválido: {exc}") from exc

    period_match = re.search(r"(\d{2})/(\d{2})/(\d{2,4})", cover)
    if not period_match:
        raise PipelineError("posición en futuros BCRA: no se encontró la fecha de cierre")
    _, month, year = period_match.groups()
    year = f"20{year}" if len(year) == 2 else year
    period = f"{year}-{month}"

    # PDFKit/pypdf ubican primero los valores de IV.1.b: total, derivados,
    # posición corta, posición larga y otros instrumentos, en ese orden.
    short_position, long_position, net_short = _extract_section_iv_values(page)

    observations = {
        "bcra_fx_futures_short_position": short_position,
        "bcra_fx_futures_long_position": long_position,
        "bcra_fx_futures_net_short_position": net_short,
    }
    return [{
        "series_id": series_id,
        "period": period,
        "frequency": "monthly",
        "value": format(value.quantize(Decimal("0.000001")), "f"),
        "unit": "million_usd",
        "status": "official",
        "source_id": FUTURES_SOURCE_ID,
        "source_url": artifact.url,
        "source_sha256": artifact.sha256,
        "retrieved_at": artifact.retrieved_at,
    } for series_id, value in observations.items()]


def _previous_month(period: str) -> str:
    year, month = map(int, period.split("-"))
    return f"{year - 1}-12" if month == 1 else f"{year}-{month - 1:02d}"


def add_adjusted_intervention(
    spot_records: list[dict[str, str]], futures_records: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Combina spot con el cambio de la posición vendida: spot - delta(cortos netos)."""
    spot = {
        row["period"]: Decimal(row["value"])
        for row in spot_records if row["series_id"] == "bcra_fx_intervention_monthly"
    }
    net_short = {
        row["period"]: row
        for row in futures_records if row["series_id"] == "bcra_fx_futures_net_short_position"
    }
    derived: list[dict[str, str]] = []
    for period, current in sorted(net_short.items()):
        previous = net_short.get(_previous_month(period))
        if previous is None or period not in spot:
            continue
        change = Decimal(current["value"]) - Decimal(previous["value"])
        futures_component = -change
        adjusted = spot[period] + futures_component
        for series_id, value in (
            ("bcra_fx_futures_net_short_change", change),
            ("bcra_fx_futures_intervention_component", futures_component),
            ("bcra_fx_intervention_adjusted_monthly", adjusted),
        ):
            derived.append(current | {
                "series_id": series_id,
                "value": format(value.quantize(Decimal("0.000001")), "f"),
                "status": "calculated",
            })
    return futures_records + derived


def _existing_futures(root: Path) -> list[dict[str, str]]:
    target = root / "data" / "processed" / "fx_intervention.csv"
    if not target.exists():
        return []
    with target.open(encoding="utf-8", newline="") as handle:
        return [row for row in csv.DictReader(handle) if row["series_id"] in FUTURES_SERIES]


def _recent_periods(today: date) -> list[str]:
    periods: list[str] = []
    year, month = today.year, today.month
    for offset in (1, 2, 3):
        absolute = year * 12 + month - 1 - offset
        periods.append(f"{absolute // 12}-{absolute % 12 + 1:02d}")
    return periods


def acquire_futures(
    root: Path, futures_dir: Path | None = None, *, refresh: bool = True,
) -> list[dict[str, str]]:
    raw_root = root / "data" / "raw"
    records = _existing_futures(root)
    by_key = {(row["series_id"], row["period"]): row for row in records}

    sources: list[tuple[str, Path | None]] = []
    if futures_dir:
        sources = [("", path) for path in sorted(futures_dir.glob("*.pdf"))]
    elif refresh:
        sources = [(period, None) for period in _recent_periods(date.today())]

    for hinted_period, local in sources:
        url = _futures_url(hinted_period) if hinted_period else local.as_uri()
        source_id = f"{FUTURES_SOURCE_ID}_{hinted_period or local.stem}"
        try:
            artifact = acquire(source_id, url, raw_root, local, min_bytes=10_000)
        except urllib.error.HTTPError as exc:
            if exc.code == 404 and local is None:
                continue
            raise PipelineError(f"posición en futuros BCRA: descarga fallida: {exc}") from exc
        extracted = extract_futures(artifact)
        if hinted_period and extracted[0]["period"] != hinted_period:
            raise PipelineError("posición en futuros BCRA: el PDF no corresponde al mes solicitado")
        for row in extracted:
            # En la carga histórica local se conserva la URL pública reproducible.
            if local is not None:
                row["source_url"] = _futures_url(row["period"])
            by_key[(row["series_id"], row["period"])] = row
    return list(by_key.values())


def _promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    records.sort(key=lambda row: (row["series_id"], row["period"]))
    keys = [(row["series_id"], row["period"]) for row in records]
    if len(keys) != len(set(keys)):
        raise PipelineError("intervención BCRA: claves duplicadas")
    daily = [row for row in records if row["series_id"] == "bcra_fx_intervention_daily"]
    if not daily or daily[0]["period"] != FIRST_PERIOD:
        raise PipelineError("intervención BCRA: cobertura histórica inesperada")

    target_dir = root / "data" / "processed"
    log_dir = root / "data" / "logs" / "fx_intervention"
    target_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "fx_intervention.csv"
    old: dict[tuple[str, str], str] = {}
    if target.exists():
        with target.open(encoding="utf-8", newline="") as handle:
            old = {(row["series_id"], row["period"]): row["value"] for row in csv.DictReader(handle)}
    new = {(row["series_id"], row["period"]): row["value"] for row in records}
    report = {
        "run_id": run_id, "rows": len(records), "series": len({row["series_id"] for row in records}),
        "min_period": daily[0]["period"], "max_period": daily[-1]["period"],
        "created": len(new.keys() - old.keys()), "deleted": len(old.keys() - new.keys()),
        "modified": sum(old[key] != new[key] for key in old.keys() & new.keys()),
    }
    # El acumulado del año/mes corriente cambia cada día; las observaciones diarias no deben desaparecer.
    old_daily = {key for key in old if key[0] == "bcra_fx_intervention_daily"}
    new_daily = {key for key in new if key[0] == "bcra_fx_intervention_daily"}
    if old_daily - new_daily:
        raise PipelineError("intervención BCRA: la fuente eliminó observaciones diarias")

    fd, temporary = tempfile.mkstemp(prefix="fx-intervention-", suffix=".csv", dir=target_dir)
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
    (log_dir / f"{run_id}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def run(
    root: Path, source_file: Path | None = None, futures_dir: Path | None = None,
) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw_root = root / "data" / "raw"
    if source_file:
        artifacts = [acquire(SOURCE_ID, f"{BASE_URL}/{VARIABLE_ID}", raw_root, source_file)]
    else:
        artifacts = []
        offset = 0
        while True:
            artifact = acquire(
                f"{SOURCE_ID}_offset_{offset}",
                f"{BASE_URL}/{VARIABLE_ID}?offset={offset}&limit=1000",
                raw_root,
            )
            artifacts.append(artifact)
            payload = json.loads(artifact.path.read_text(encoding="utf-8"))
            count = payload["metadata"]["resultset"]["count"]
            offset += 1000
            if offset >= count:
                break
    daily: list[dict[str, str]] = []
    for artifact in artifacts:
        daily.extend(extract(artifact))
    daily.sort(key=lambda row: row["period"])
    if len({row["period"] for row in daily}) != len(daily):
        raise PipelineError("intervención BCRA: páginas superpuestas")
    spot_records = aggregate(daily)
    futures_records = acquire_futures(
        root, futures_dir, refresh=source_file is None or futures_dir is not None,
    )
    return _promote(spot_records + add_adjusted_intervention(spot_records, futures_records), root, run_id)
