from __future__ import annotations

import bisect
import csv
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import xlrd

from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, acquire

BALANCE_URL = "https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/din1_ser.txt"
VALUATION_FX_URL = "https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/din2_ser.txt"
DAILY_BALANCE_URL = "https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/diar_bas.xls"
LANDING_URL = "https://www.bcra.gob.ar/consulta-de-series-estadisticas-en-formato-txt/"
BALANCE_SOURCE_ID = "bcra_money_credit_balances"
FX_SOURCE_ID = "bcra_daily_reserves_liabilities"
DAILY_BALANCE_SOURCE_ID = "bcra_daily_government_deposits"

ARS_CODE = "106"
FX_DEPOSITS_CODE = "107"
OFFICIAL_DEPOSITS_CODE = "105"
VALUATION_FX_CODE = "271"

ARS_STOCK = "bcra_treasury_deposits_ars"
ARS_CHANGE = "bcra_treasury_deposits_ars_monthly_change"
USD_STOCK = "bcra_treasury_deposits_usd"
USD_CHANGE = "bcra_treasury_deposits_usd_monthly_change"

DAILY_TOTAL_CODE = "269"
DAILY_ARS_CODE = "8842"
DAILY_FX_DEPOSITS_CODE = "8843"
DAILY_VALUATION_FX_CODE = "271"
ARS_DAILY_STOCK = "bcra_treasury_deposits_ars_daily"
ARS_DAILY_CHANGE = "bcra_treasury_deposits_ars_daily_change"
USD_DAILY_STOCK = "bcra_treasury_deposits_usd_daily"
USD_DAILY_CHANGE = "bcra_treasury_deposits_usd_daily_change"


def _read_series(artifact: Artifact, wanted: set[str]) -> dict[str, dict[str, Decimal]]:
    result = {code: {} for code in wanted}
    try:
        handle = artifact.path.open(encoding="latin-1", newline="")
    except OSError as exc:
        raise PipelineError(f"liquidez del Tesoro: no se pudo abrir {artifact.path.name}: {exc}") from exc
    with handle:
        reader = csv.reader(handle, delimiter=";")
        for row_number, row in enumerate(reader, start=1):
            if len(row) != 3 or row[0] not in wanted:
                continue
            code, raw_date, raw_value = row
            try:
                period = datetime.strptime(raw_date, "%d/%m/%Y").date().isoformat()
                value = Decimal(raw_value)
            except (ValueError, InvalidOperation) as exc:
                raise PipelineError(
                    f"liquidez del Tesoro: observación inválida en {artifact.path.name}:{row_number}"
                ) from exc
            if period in result[code]:
                raise PipelineError(f"liquidez del Tesoro: fecha duplicada para serie {code}: {period}")
            result[code][period] = value
    missing = [code for code in wanted if not result[code]]
    if missing:
        raise PipelineError(f"liquidez del Tesoro: faltan series oficiales {', '.join(sorted(missing))}")
    return result


def _record(
    series_id: str,
    period: str,
    value: Decimal,
    unit: str,
    artifact: Artifact,
    *,
    status: str = "official",
    source_id: str | None = None,
    source_url: str | None = None,
    source_sha256: str | None = None,
    frequency: str = "monthly",
) -> dict[str, str]:
    return {
        "series_id": series_id,
        "period": period,
        "frequency": frequency,
        "value": format(value.quantize(Decimal("0.000001")), "f"),
        "unit": unit,
        "status": status,
        "source_id": source_id or artifact.source_id,
        "source_url": source_url or artifact.url,
        "source_sha256": source_sha256 or artifact.sha256,
        "retrieved_at": artifact.retrieved_at,
    }


def _code(value: object) -> str:
    if isinstance(value, (int, float)) and float(value).is_integer():
        return str(int(value))
    return str(value).strip()


def _daily_rows(artifact: Artifact) -> list[tuple[str, Decimal, Decimal, Decimal, Decimal]]:
    try:
        workbook = xlrd.open_workbook(artifact.path)
        sheet = workbook.sheet_by_name("Serie_diaria")
    except (OSError, xlrd.XLRDError) as exc:
        raise PipelineError(f"liquidez del Tesoro: no se pudo abrir la planilla diaria: {exc}") from exc

    wanted = {DAILY_TOTAL_CODE, DAILY_ARS_CODE, DAILY_FX_DEPOSITS_CODE, DAILY_VALUATION_FX_CODE}
    code_row = -1
    columns: dict[str, int] = {}
    for row_index in range(min(80, sheet.nrows)):
        candidate = {_code(sheet.cell_value(row_index, column)): column for column in range(sheet.ncols)}
        if wanted <= candidate.keys():
            code_row = row_index
            columns = {code: candidate[code] for code in wanted}
            break
    if code_row < 0:
        raise PipelineError("liquidez del Tesoro: cambió el esquema de códigos de la planilla diaria")

    result: list[tuple[str, Decimal, Decimal, Decimal, Decimal]] = []
    for row_index in range(code_row + 1, sheet.nrows):
        raw_date = sheet.cell_value(row_index, 0)
        if not isinstance(raw_date, (int, float)) or raw_date <= 0:
            continue
        try:
            values = {
                code: Decimal(str(sheet.cell_value(row_index, column)))
                for code, column in columns.items()
            }
        except (InvalidOperation, ValueError):
            continue
        total = values[DAILY_TOTAL_CODE]
        ars = values[DAILY_ARS_CODE]
        foreign_ars = values[DAILY_FX_DEPOSITS_CODE]
        valuation_fx = values[DAILY_VALUATION_FX_CODE]
        # El BCRA suele adelantar fechas todavía no informadas con saldos cero.
        if total == 0 and ars == 0 and foreign_ars == 0:
            continue
        if min(total, ars, foreign_ars) < 0 or valuation_fx <= 0:
            raise PipelineError(f"liquidez del Tesoro: valor diario inválido en la fila {row_index + 1}")
        if abs(total - ars - foreign_ars) > Decimal("1"):
            raise PipelineError(f"liquidez del Tesoro: componentes diarios inconsistentes en la fila {row_index + 1}")
        period = xlrd.xldate_as_datetime(raw_date, workbook.datemode).date().isoformat()
        result.append((period, total, ars, foreign_ars, valuation_fx))

    if len(result) < 500 or result[-1][0] < "2025-01-01":
        raise PipelineError("liquidez del Tesoro: cobertura diaria inesperada")
    if len({row[0] for row in result}) != len(result):
        raise PipelineError("liquidez del Tesoro: fechas diarias duplicadas")
    return result


def extract_daily(artifact: Artifact) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    previous_ars: Decimal | None = None
    previous_usd: Decimal | None = None
    for period, _total, ars, foreign_ars, valuation_fx in _daily_rows(artifact):
        usd = foreign_ars / valuation_fx
        records.append(_record(
            ARS_DAILY_STOCK, period, ars, "million_ars", artifact, frequency="daily",
        ))
        records.append(_record(
            USD_DAILY_STOCK, period, usd, "million_usd", artifact,
            status="calculated", source_id="bcra_treasury_deposits_usd_daily_calculated",
            frequency="daily",
        ))
        if previous_ars is not None:
            records.append(_record(
                ARS_DAILY_CHANGE, period, ars - previous_ars, "million_ars", artifact,
                status="calculated", frequency="daily",
            ))
        if previous_usd is not None:
            records.append(_record(
                USD_DAILY_CHANGE, period, usd - previous_usd, "million_usd", artifact,
                status="calculated", source_id="bcra_treasury_deposits_usd_daily_calculated",
                frequency="daily",
            ))
        previous_ars = ars
        previous_usd = usd
    return records


def extract(
    balance: Artifact,
    valuation_fx: Artifact,
    daily_balance: Artifact | None = None,
) -> list[dict[str, str]]:
    balances = _read_series(
        balance,
        {OFFICIAL_DEPOSITS_CODE, ARS_CODE, FX_DEPOSITS_CODE},
    )
    fx = _read_series(valuation_fx, {VALUATION_FX_CODE})[VALUATION_FX_CODE]

    shared = sorted(set(balances[ARS_CODE]) & set(balances[FX_DEPOSITS_CODE]))
    if not shared or shared[-1] < "2025-01-01" or len(shared) < 400:
        raise PipelineError("liquidez del Tesoro: cobertura mensual inesperada")

    # El total de depósitos oficiales debe ser la suma de moneda nacional y extranjera.
    recent = [period for period in shared if period >= "2020-01-01"]
    for period in recent:
        official = balances[OFFICIAL_DEPOSITS_CODE].get(period)
        if official is None:
            raise PipelineError(f"liquidez del Tesoro: falta el total de control en {period}")
        difference = abs(official - balances[ARS_CODE][period] - balances[FX_DEPOSITS_CODE][period])
        if difference > Decimal("1"):
            raise PipelineError(f"liquidez del Tesoro: componentes inconsistentes en {period}")

    fx_dates = sorted(fx)
    composite_hash = hashlib.sha256(f"{balance.sha256}:{valuation_fx.sha256}".encode()).hexdigest()
    records: list[dict[str, str]] = []
    previous_ars: Decimal | None = None
    previous_usd: Decimal | None = None

    for period in shared:
        ars = balances[ARS_CODE][period] / Decimal("1000")
        records.append(_record(ARS_STOCK, period[:7], ars, "million_ars", balance))
        if previous_ars is not None:
            records.append(_record(
                ARS_CHANGE, period[:7], ars - previous_ars, "million_ars", balance,
                status="calculated",
            ))
        previous_ars = ars

        # La serie diaria de tipo de cambio comienza en 2002. Se toma el último día
        # hábil disponible hasta el cierre mensual del balance.
        index = bisect.bisect_right(fx_dates, period) - 1
        if index < 0:
            continue
        fx_period = fx_dates[index]
        if (datetime.fromisoformat(period) - datetime.fromisoformat(fx_period)).days > 7:
            raise PipelineError(f"liquidez del Tesoro: tipo de cambio de valuación distante en {period}")
        rate = fx[fx_period]
        if rate <= 0:
            raise PipelineError(f"liquidez del Tesoro: tipo de cambio no positivo en {fx_period}")
        usd = (balances[FX_DEPOSITS_CODE][period] / Decimal("1000")) / rate
        records.append(_record(
            USD_STOCK, period[:7], usd, "million_usd", balance,
            status="calculated", source_id="bcra_treasury_deposits_usd_calculated",
            source_url=LANDING_URL, source_sha256=composite_hash,
        ))
        if previous_usd is not None:
            records.append(_record(
                USD_CHANGE, period[:7], usd - previous_usd, "million_usd", balance,
                status="calculated", source_id="bcra_treasury_deposits_usd_calculated",
                source_url=LANDING_URL, source_sha256=composite_hash,
            ))
        previous_usd = usd

    if daily_balance is not None:
        records.extend(extract_daily(daily_balance))
    return records


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    records.sort(key=lambda row: (row["series_id"], row["period"]))
    keys = [(row["series_id"], row["period"]) for row in records]
    if len(keys) != len(set(keys)):
        raise PipelineError("liquidez del Tesoro: claves duplicadas")

    target_dir = root / "data" / "processed"
    log_dir = root / "data" / "logs" / "treasury_liquidity"
    target_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "treasury_liquidity.csv"

    old: dict[tuple[str, str], str] = {}
    if target.exists():
        with target.open(encoding="utf-8", newline="") as handle:
            old = {(row["series_id"], row["period"]): row["value"] for row in csv.DictReader(handle)}
    new = {(row["series_id"], row["period"]): row["value"] for row in records}
    report = {
        "run_id": run_id,
        "rows": len(records),
        "series": len({row["series_id"] for row in records}),
        "min_period": min(row["period"] for row in records),
        "max_period": max(row["period"] for row in records),
        "created": len(new.keys() - old.keys()),
        "deleted": len(old.keys() - new.keys()),
        "modified": sum(old[key] != new[key] for key in old.keys() & new.keys()),
    }
    if old.keys() - new.keys():
        raise PipelineError("liquidez del Tesoro: la fuente eliminó observaciones existentes")

    fd, temporary = tempfile.mkstemp(prefix="treasury-liquidity-", suffix=".csv", dir=target_dir)
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
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def run(
    root: Path,
    balance_file: Path | None = None,
    valuation_fx_file: Path | None = None,
    daily_balance_file: Path | None = None,
) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw = root / "data" / "raw"
    balance = acquire(BALANCE_SOURCE_ID, BALANCE_URL, raw, balance_file, min_bytes=1000)
    valuation_fx = acquire(FX_SOURCE_ID, VALUATION_FX_URL, raw, valuation_fx_file, min_bytes=1000)
    daily_balance = acquire(
        DAILY_BALANCE_SOURCE_ID, DAILY_BALANCE_URL, raw, daily_balance_file, min_bytes=100_000,
    )
    return promote(extract(balance, valuation_fx, daily_balance), root, run_id)
