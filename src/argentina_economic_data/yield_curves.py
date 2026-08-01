from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .inflation import Artifact, PipelineError, acquire


SOURCE_ID = "datarg_byma_yield_curves"
SOURCE_URL = "https://www.byma.com.ar/productos/productos-de-datos/market-data/apis"
PUBLIC_SOURCE_ID = "argentinadatos_data912_yield_curves"
LETTERS_URL = "https://api.argentinadatos.com/v1/finanzas/letras"
NOTES_URL = "https://data912.com/live/arg_notes"
BONDS_URL = "https://data912.com/live/arg_bonds"
CER_URL = "https://api.argentinadatos.com/v1/finanzas/bonos-cer"
RENDIMIENTOS_CONFIG_URL = "https://rendimientos.co/api/config"
RENDIMIENTOS_CER_PRICES_URL = "https://rendimientos.co/api/cer-precios"
RENDIMIENTOS_CER_URL = "https://rendimientos.co/api/cer"
RENDIMIENTOS_SOURCE_ID = "rendimientos_bcra_calculated_cer_yield"
INPUT_COLUMNS = {
    "snapshot_date", "ticker", "instrument_name", "curve_type", "instrument_type",
    "settlement_date", "maturity_date", "price", "cashflows", "volume", "source_url",
}
OUTPUT_COLUMNS = [
    "snapshot_date", "ticker", "instrument_name", "curve_type", "instrument_type",
    "settlement_date", "maturity_date", "days_to_maturity", "price", "annual_yield",
    "monthly_yield", "duration_years", "volume", "status", "source_id", "source_url",
    "source_sha256", "retrieved_at",
]


def _parse_cashflows(value: str, settlement: date) -> list[tuple[date, float]]:
    flows: list[tuple[date, float]] = []
    for item in value.split("|"):
        if not item.strip():
            continue
        try:
            period, amount = item.split(":", 1)
            flow_date = date.fromisoformat(period.strip())
            flow_amount = float(amount.strip())
        except (ValueError, TypeError) as exc:
            raise PipelineError(f"curvas BYMA: flujo inválido {item!r}") from exc
        if flow_date <= settlement or not math.isfinite(flow_amount) or flow_amount <= 0:
            raise PipelineError(f"curvas BYMA: flujo no positivo o anterior a la liquidación: {item!r}")
        flows.append((flow_date, flow_amount))
    if not flows:
        raise PipelineError("curvas BYMA: instrumento sin flujos futuros")
    return sorted(flows)


def _npv(rate: float, price: float, settlement: date, flows: list[tuple[date, float]]) -> float:
    return -price + sum(amount / (1 + rate) ** ((period - settlement).days / 365.0) for period, amount in flows)


def annual_yield(price: float, settlement: date, flows: list[tuple[date, float]]) -> float:
    """TIR efectiva anual con días reales/365, resuelta sobre los flujos del instrumento."""
    if not math.isfinite(price) or price <= 0:
        raise PipelineError("curvas BYMA: precio inválido")
    low, high = -0.999999, 1.0
    low_value, high_value = _npv(low, price, settlement, flows), _npv(high, price, settlement, flows)
    while low_value * high_value > 0 and high < 10_000:
        high *= 2
        high_value = _npv(high, price, settlement, flows)
    if low_value * high_value > 0:
        raise PipelineError("curvas BYMA: los flujos no permiten resolver una TIR")
    for _ in range(160):
        middle = (low + high) / 2
        value = _npv(middle, price, settlement, flows)
        if abs(value) < 1e-11:
            return middle
        if low_value * value <= 0:
            high = middle
        else:
            low, low_value = middle, value
    return (low + high) / 2


def macaulay_duration(rate: float, price: float, settlement: date, flows: list[tuple[date, float]]) -> float:
    weighted = 0.0
    present = 0.0
    for period, amount in flows:
        years = (period - settlement).days / 365.0
        pv = amount / (1 + rate) ** years
        weighted += years * pv
        present += pv
    return weighted / present if present else 0.0


def extract(source: Path) -> list[dict[str, str]]:
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    retrieved_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    with source.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not INPUT_COLUMNS.issubset(set(reader.fieldnames or [])):
            missing = sorted(INPUT_COLUMNS - set(reader.fieldnames or []))
            raise PipelineError(f"curvas BYMA: faltan columnas {missing}")
        source_rows = list(reader)
    if not source_rows:
        raise PipelineError("curvas BYMA: archivo sin instrumentos")

    records: list[dict[str, str]] = []
    identities: set[tuple[str, str]] = set()
    for row in source_rows:
        try:
            snapshot = date.fromisoformat(row["snapshot_date"])
            settlement = date.fromisoformat(row["settlement_date"])
            maturity = date.fromisoformat(row["maturity_date"])
            price = float(row["price"])
            volume = float(row["volume"] or 0)
        except (ValueError, TypeError) as exc:
            raise PipelineError(f"curvas BYMA: fechas o valores inválidos para {row.get('ticker', 'instrumento')}") from exc
        curve_type = row["curve_type"].strip().lower()
        if curve_type not in {"nominal", "cer"}:
            raise PipelineError(f"curvas BYMA: tipo de curva inválido {curve_type!r}")
        ticker = row["ticker"].strip().upper()
        identity = (snapshot.isoformat(), ticker)
        if not ticker or identity in identities:
            raise PipelineError(f"curvas BYMA: ticker vacío o duplicado {ticker!r} en {snapshot}")
        if settlement < snapshot or maturity <= settlement:
            raise PipelineError(f"curvas BYMA: calendario inválido para {ticker}")
        if not math.isfinite(volume) or volume < 0:
            raise PipelineError(f"curvas BYMA: volumen inválido para {ticker}")
        flows = _parse_cashflows(row["cashflows"], settlement)
        if flows[-1][0] != maturity:
            raise PipelineError(f"curvas BYMA: el último flujo de {ticker} no coincide con su vencimiento")
        rate = annual_yield(price, settlement, flows)
        monthly = (1 + rate) ** (1 / 12) - 1
        duration = macaulay_duration(rate, price, settlement, flows)
        identities.add(identity)
        records.append({
            "snapshot_date": snapshot.isoformat(),
            "ticker": ticker,
            "instrument_name": row["instrument_name"].strip(),
            "curve_type": curve_type,
            "instrument_type": row["instrument_type"].strip().lower(),
            "settlement_date": settlement.isoformat(),
            "maturity_date": maturity.isoformat(),
            "days_to_maturity": str((maturity - settlement).days),
            "price": f"{price:.6f}",
            "annual_yield": f"{rate * 100:.6f}",
            "monthly_yield": f"{monthly * 100:.6f}",
            "duration_years": f"{duration:.6f}",
            "volume": f"{volume:.6f}",
            "status": "calculated",
            "source_id": SOURCE_ID,
            "source_url": row["source_url"].strip() or SOURCE_URL,
            "source_sha256": checksum,
            "retrieved_at": retrieved_at,
        })
    records.sort(key=lambda item: (item["snapshot_date"], item["curve_type"], int(item["days_to_maturity"]), item["ticker"]))
    return records


def _json_list(artifact: Artifact, label: str) -> list[dict[str, object]]:
    try:
        payload = json.loads(artifact.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PipelineError(f"curvas públicas: JSON inválido en {label}") from exc
    if not isinstance(payload, list):
        raise PipelineError(f"curvas públicas: esquema inesperado en {label}")
    return [row for row in payload if isinstance(row, dict)]


def _previous_market_day(moment: datetime) -> date:
    day = moment.astimezone(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


def _next_business_day(day: date) -> date:
    candidate = day + timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate


def _public_record(
    *, snapshot: date, settlement: date, ticker: str, instrument_name: str,
    curve_type: str, instrument_type: str, maturity: date, price: float,
    rate: float, duration: float, volume: float, status: str, source_id: str,
    source_url: str, checksum: str, retrieved_at: str,
) -> dict[str, str]:
    monthly = (1 + rate) ** (1 / 12) - 1 if rate > -1 else float("nan")
    return {
        "snapshot_date": snapshot.isoformat(), "ticker": ticker,
        "instrument_name": instrument_name, "curve_type": curve_type,
        "instrument_type": instrument_type, "settlement_date": settlement.isoformat(),
        "maturity_date": maturity.isoformat(), "days_to_maturity": str((maturity - settlement).days),
        "price": f"{price:.6f}", "annual_yield": f"{rate * 100:.6f}",
        "monthly_yield": f"{monthly * 100:.6f}", "duration_years": f"{duration:.6f}",
        "volume": f"{volume:.6f}", "status": status, "source_id": source_id,
        "source_url": source_url, "source_sha256": checksum, "retrieved_at": retrieved_at,
    }


def extract_public_nominal(
    letters: Artifact, notes: Artifact, bonds: Artifact,
) -> list[dict[str, str]]:
    """Construye LECAP/BONCAP con metadatos públicos y cotizaciones demoradas."""
    terms = _json_list(letters, "ArgentinaDatos/letras")
    note_quotes = _json_list(notes, "Data912/notas")
    bond_quotes = _json_list(bonds, "Data912/bonos")
    term_by_ticker = {str(row.get("ticker", "")).upper(): row for row in terms}
    quote_by_ticker = {
        **{str(row.get("symbol", "")).upper(): (row, NOTES_URL) for row in note_quotes},
        **{str(row.get("symbol", "")).upper(): (row, BONDS_URL) for row in bond_quotes},
    }
    try:
        retrieved = datetime.fromisoformat(notes.retrieved_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PipelineError("curvas públicas: fecha de recuperación inválida") from exc
    snapshot = _previous_market_day(retrieved)
    settlement = _next_business_day(snapshot)
    checksum = hashlib.sha256(
        f"{letters.sha256}:{notes.sha256}:{bonds.sha256}".encode("ascii")
    ).hexdigest()
    rows: list[dict[str, str]] = []
    for ticker, term in term_by_ticker.items():
        quote_entry = quote_by_ticker.get(ticker)
        if not quote_entry or not ticker.startswith(("S", "T")):
            continue
        quote, quote_url = quote_entry
        try:
            maturity = date.fromisoformat(str(term["fechaVencimiento"]))
            final_payment = float(term["vpv"])
            price = float(quote["c"])
            volume = float(quote.get("v") or 0)
        except (KeyError, TypeError, ValueError):
            continue
        if maturity <= settlement or price <= 0 or final_payment <= 0 or volume < 0:
            continue
        flows = [(maturity, final_payment)]
        rate = annual_yield(price, settlement, flows)
        rows.append(_public_record(
            snapshot=snapshot, settlement=settlement, ticker=ticker,
            instrument_name="LECAP" if ticker.startswith("S") else "BONCAP",
            curve_type="nominal", instrument_type="lecap" if ticker.startswith("S") else "boncap",
            maturity=maturity, price=price, rate=rate,
            duration=macaulay_duration(rate, price, settlement, flows), volume=volume,
            status="calculated_from_delayed_quote", source_id=PUBLIC_SOURCE_ID,
            source_url=quote_url, checksum=checksum, retrieved_at=notes.retrieved_at,
        ))
    if len(rows) < 3:
        raise PipelineError(f"curvas públicas: sólo quedaron {len(rows)} instrumentos nominales válidos")
    return sorted(rows, key=lambda row: (int(row["days_to_maturity"]), row["ticker"]))


def extract_public_cer(artifact: Artifact) -> list[dict[str, str]]:
    """Usa la TIR CER publicada; nunca intenta reconstruirla sin flujos contractuales."""
    try:
        payload = json.loads(artifact.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PipelineError("curvas públicas: JSON inválido en bonos CER") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("bonos"), list):
        raise PipelineError("curvas públicas: esquema inesperado en bonos CER")
    updated = payload.get("fechaActualizacion") or artifact.retrieved_at
    try:
        moment = datetime.fromisoformat(str(updated).replace("Z", "+00:00"))
    except ValueError:
        moment = datetime.fromisoformat(artifact.retrieved_at.replace("Z", "+00:00"))
    snapshot = _previous_market_day(moment)
    settlement = _next_business_day(snapshot)
    rows: list[dict[str, str]] = []
    for item in payload["bonos"]:
        if not isinstance(item, dict):
            continue
        try:
            ticker = str(item["ticker"]).upper()
            price = float(item["precioArs"])
            rate = float(item["tirPorcentaje"]) / 100
            maturity = date.fromisoformat(str(item["fechaVencimiento"]))
            volume = float(item.get("volumen") or 0)
        except (KeyError, TypeError, ValueError):
            continue
        days = (maturity - settlement).days
        if not ticker or days <= 0 or price <= 0 or not math.isfinite(rate) or volume < 0:
            continue
        rows.append(_public_record(
            snapshot=snapshot, settlement=settlement, ticker=ticker, instrument_name="Bono CER",
            curve_type="cer", instrument_type="boncer", maturity=maturity, price=price,
            rate=rate, duration=days / 365, volume=volume, status="reported_yield",
            source_id="argentinadatos_bonos_cer", source_url=CER_URL,
            checksum=artifact.sha256, retrieved_at=artifact.retrieved_at,
        ))
    return sorted(rows, key=lambda row: (int(row["days_to_maturity"]), row["ticker"]))


def _json_object(artifact: Artifact, label: str) -> dict[str, object]:
    try:
        payload = json.loads(artifact.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PipelineError(f"curvas públicas: JSON inválido en {label}") from exc
    if not isinstance(payload, dict):
        raise PipelineError(f"curvas públicas: esquema inesperado en {label}")
    return payload


def _cer_cashflows(
    raw_flows: object, settlement: date,
) -> list[tuple[date, float]]:
    """Reconstruye flujos reales por VN 100 y el capital residual de cada cupón."""
    if not isinstance(raw_flows, list):
        raise PipelineError("curvas CER: cronograma contractual inválido")
    outstanding = 1.0
    flows: list[tuple[date, float]] = []
    for item in sorted(
        (row for row in raw_flows if isinstance(row, dict)),
        key=lambda row: str(row.get("fecha", "")),
    ):
        try:
            flow_date = date.fromisoformat(str(item["fecha"]))
            amortization = float(item.get("amortizacion") or 0)
            coupon_rate = float(item.get("tasa_interes") or 0)
            year_fraction = float(item.get("base") or 0)
        except (KeyError, TypeError, ValueError) as exc:
            raise PipelineError("curvas CER: flujo contractual inválido") from exc
        if not all(math.isfinite(value) and value >= 0 for value in (amortization, coupon_rate, year_fraction)):
            raise PipelineError("curvas CER: flujo contractual no positivo")
        if amortization > outstanding + 1e-6:
            raise PipelineError("curvas CER: amortización superior al capital residual")
        amount = amortization + outstanding * coupon_rate * year_fraction
        if flow_date > settlement and amount > 0:
            flows.append((flow_date, amount * 100))
        outstanding = max(0.0, outstanding - amortization)
    if not flows:
        raise PipelineError("curvas CER: instrumento sin flujos futuros")
    return flows


def extract_rendimientos_cer(
    config: Artifact, prices: Artifact, cer_value: Artifact,
) -> list[dict[str, str]]:
    """Calcula la curva CER desde precios, CER oficial y flujos contractuales públicos."""
    config_payload = _json_object(config, "Rendimientos/config")
    prices_payload = _json_object(prices, "Rendimientos/cer-precios")
    cer_payload = _json_object(cer_value, "Rendimientos/cer")
    definitions = config_payload.get("bonos_cer")
    quotes = prices_payload.get("data")
    if not isinstance(definitions, dict) or not isinstance(quotes, list):
        raise PipelineError("curvas CER: metadatos o precios con esquema inesperado")
    try:
        current_cer = float(cer_payload["cer"])
        cer_date = date.fromisoformat(str(cer_payload["fecha"]))
        retrieved = datetime.fromisoformat(prices.retrieved_at.replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError) as exc:
        raise PipelineError("curvas CER: valor o fecha CER inválidos") from exc
    if not math.isfinite(current_cer) or current_cer <= 0:
        raise PipelineError("curvas CER: valor CER no positivo")
    snapshot = _previous_market_day(retrieved)
    settlement = _next_business_day(snapshot)
    if cer_date > settlement or (settlement - cer_date).days > 30:
        raise PipelineError(f"curvas CER: CER fuera de vigencia ({cer_date})")
    checksum = hashlib.sha256(
        f"{config.sha256}:{prices.sha256}:{cer_value.sha256}".encode("ascii")
    ).hexdigest()
    rows: list[dict[str, str]] = []
    for quote in quotes:
        if not isinstance(quote, dict):
            continue
        ticker = str(quote.get("symbol", "")).upper()
        definition = definitions.get(ticker)
        if not ticker or not isinstance(definition, dict):
            continue
        try:
            maturity = date.fromisoformat(str(definition["vencimiento"]))
            emission_cer = float(definition["cer_emision"])
            price = float(quote["c"])
            volume = float(quote.get("v") or 0)
            flows = _cer_cashflows(definition.get("flujos"), settlement)
        except (KeyError, TypeError, ValueError, PipelineError):
            continue
        if maturity <= settlement or price <= 0 or emission_cer <= 0 or volume < 0:
            continue
        # El precio nominal cotizado se expresa en VN 100 ajustado. Al dividirlo
        # por CER vigente / CER de emisión queda bajo la misma unidad real que
        # los flujos contractuales reconstruidos.
        real_price = price * emission_cer / current_cer
        try:
            rate = annual_yield(real_price, settlement, flows)
            duration = macaulay_duration(rate, real_price, settlement, flows)
        except (PipelineError, OverflowError, ZeroDivisionError):
            continue
        if not (-0.80 < rate < 5.0) or not math.isfinite(duration) or duration <= 0:
            continue
        rows.append(_public_record(
            snapshot=snapshot, settlement=settlement, ticker=ticker,
            instrument_name="Bono CER", curve_type="cer", instrument_type="boncer",
            maturity=maturity, price=price, rate=rate, duration=duration, volume=volume,
            status="calculated_from_public_price_and_cashflows",
            source_id=RENDIMIENTOS_SOURCE_ID, source_url=RENDIMIENTOS_CER_PRICES_URL,
            checksum=checksum, retrieved_at=prices.retrieved_at,
        ))
    if len(rows) < 5:
        raise PipelineError(f"curvas CER: sólo quedaron {len(rows)} instrumentos válidos")
    return sorted(rows, key=lambda row: (int(row["days_to_maturity"]), row["ticker"]))


def promote(records: list[dict[str, str]], root: Path, warnings: list[str] | None = None) -> dict[str, object]:
    target_dir = root / "data" / "processed"
    log_dir = root / "data" / "logs" / "yield_curves"
    target_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "yield_curves.csv"
    retained_cer = 0
    if target.exists() and not any(row["curve_type"] == "cer" for row in records):
        with target.open(encoding="utf-8", newline="") as handle:
            existing_cer = [row for row in csv.DictReader(handle) if row.get("curve_type") == "cer"]
        if existing_cer:
            last_cer_snapshot = max(row["snapshot_date"] for row in existing_cer)
            retained = [row for row in existing_cer if row["snapshot_date"] == last_cer_snapshot]
            records.extend(retained)
            retained_cer = len(retained)
    records.sort(key=lambda item: (item["snapshot_date"], item["curve_type"], int(item["days_to_maturity"]), item["ticker"]))
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    fd, temporary = tempfile.mkstemp(prefix="yield-curves-", suffix=".csv", dir=target_dir)
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
    report = {
        "run_id": run_id,
        "rows": len(records),
        "snapshots": len({row["snapshot_date"] for row in records}),
        "nominal": sum(row["curve_type"] == "nominal" for row in records),
        "cer": sum(row["curve_type"] == "cer" for row in records),
        "retained_cer": retained_cer,
        "warnings": warnings or [],
    }
    (log_dir / f"{run_id}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def run(root: Path, source_file: Path | None = None) -> dict[str, object]:
    source = source_file or (Path(os.environ["BYMA_YIELD_CURVE_FILE"]) if os.environ.get("BYMA_YIELD_CURVE_FILE") else None)
    if source is None:
        raw = root / "data" / "raw"
        letters = acquire("argentinadatos_yield_curve_terms", LETTERS_URL, raw)
        notes = acquire("data912_yield_curve_notes", NOTES_URL, raw)
        bonds = acquire("data912_yield_curve_bonds", BONDS_URL, raw)
        records = extract_public_nominal(letters, notes, bonds)
        warnings: list[str] = []
        try:
            cer_config = acquire("rendimientos_yield_curve_config", RENDIMIENTOS_CONFIG_URL, raw)
            cer_prices = acquire("rendimientos_yield_curve_prices", RENDIMIENTOS_CER_PRICES_URL, raw)
            cer_value = acquire(
                "rendimientos_yield_curve_cer", RENDIMIENTOS_CER_URL, raw,
                min_bytes=20,
            )
            records.extend(extract_rendimientos_cer(cer_config, cer_prices, cer_value))
        except Exception as primary_exc:  # una curva opcional no bloquea la nominal
            warnings.append(f"Rendimientos/CER no disponible: {type(primary_exc).__name__}")
            try:
                cer = acquire("argentinadatos_yield_curve_cer", CER_URL, raw)
                records.extend(extract_public_cer(cer))
                if not any(row["curve_type"] == "cer" for row in records):
                    warnings.append("ArgentinaDatos/bonos-cer no devolvió observaciones válidas")
            except Exception as fallback_exc:
                warnings.append(f"ArgentinaDatos/bonos-cer no disponible: {type(fallback_exc).__name__}")
        return promote(records, root, warnings)
    if not source.exists():
        raise PipelineError(f"curvas BYMA: no existe {source}")
    return promote(extract(source), root)
