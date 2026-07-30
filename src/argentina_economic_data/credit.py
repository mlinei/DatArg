from __future__ import annotations

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

SOURCE_PAGE = "https://www.bcra.gob.ar/prestamos-y-otros-activos-de-las-entidades-financieras/"
PRIVATE_URL = "https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/perser_priv.xls"
PUBLIC_URL = "https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/perser_pub.xls"
SECURITIES_URL = "https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/titpubser.xls"
REAL_BASE_PERIOD = "2019-12"
LEVEL_SERIES = {
    "bcra_private_nonfinancial_credit",
    "bcra_public_loans_government",
    "bcra_public_loans_enterprises",
    "bcra_public_loans_total",
    "bcra_public_exposure_securities",
    "bcra_public_exposure_total",
}


def _period(value: object) -> str | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    year = int(number)
    month = round((number - year) * 100)
    return f"{year:04d}-{month:02d}" if 1 <= month <= 12 else None


def _number(value: object, field: str, period: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise PipelineError(f"crédito BCRA: valor inválido en {field}/{period}") from exc
    if number < 0:
        raise PipelineError(f"crédito BCRA: valor negativo en {field}/{period}")
    return number / Decimal(1000)  # miles de pesos -> millones de pesos


def _sheet(artifact: Artifact, name: str):
    try:
        workbook = xlrd.open_workbook(artifact.path)
        return workbook.sheet_by_name(name)
    except Exception as exc:
        raise PipelineError(f"crédito BCRA: no se pudo leer la hoja {name}: {exc}") from exc


def _values(artifact: Artifact, sheet_name: str, columns: dict[str, tuple[int, ...]]) -> dict[str, dict[str, Decimal]]:
    sheet = _sheet(artifact, sheet_name)
    result: dict[str, dict[str, Decimal]] = {}
    for row in range(26, sheet.nrows):
        period = _period(sheet.cell_value(row, 0))
        if not period or not str(sheet.cell_value(row, 1)).strip():
            continue
        values = {
            name: sum((_number(sheet.cell_value(row, column), name, period) for column in indices), Decimal())
            for name, indices in columns.items()
        }
        result[period] = values
    if not result:
        raise PipelineError(f"crédito BCRA: la hoja {sheet_name} no contiene observaciones")
    return result


def _record(series_id: str, period: str, value: Decimal, status: str, artifact: Artifact, source_hash: str) -> dict[str, str]:
    return {
        "series_id": series_id, "period": period, "frequency": "monthly",
        "value": format(value.quantize(Decimal("0.000001")), "f"), "unit": "million_ars",
        "status": status, "source_id": "bcra_financial_system_credit",
        "source_url": SOURCE_PAGE, "source_sha256": source_hash,
        "retrieved_at": artifact.retrieved_at,
    }


def extract(private: Artifact, public: Artifact, securities: Artifact) -> list[dict[str, str]]:
    private_values = _values(private, "Prest-Tot", {"private": (3,)})
    public_values = _values(public, "Series", {
        "government": (3, 27),
        "public_enterprises": (10, 11, 12, 13, 34, 35, 36, 37),
    })
    security_values = _values(securities, "Datos", {
        # Gobierno nacional + gobiernos provinciales y municipales. Se excluyen títulos del BCRA.
        "government_securities": (9, 12),
    })
    source_hash = hashlib.sha256(
        "|".join((private.sha256, public.sha256, securities.sha256)).encode()
    ).hexdigest()
    records: list[dict[str, str]] = []
    for period, values in private_values.items():
        records.append(_record("bcra_private_nonfinancial_credit", period, values["private"], "official", private, source_hash))
    for period, values in public_values.items():
        government = values["government"]
        enterprises = values["public_enterprises"]
        total = government + enterprises
        records.extend([
            _record("bcra_public_loans_government", period, government, "official", public, source_hash),
            _record("bcra_public_loans_enterprises", period, enterprises, "official", public, source_hash),
            _record("bcra_public_loans_total", period, total, "calculated", public, source_hash),
        ])
    common_periods = sorted(set(public_values) & set(security_values))
    for period in common_periods:
        loans = public_values[period]["government"] + public_values[period]["public_enterprises"]
        securities_value = security_values[period]["government_securities"]
        records.extend([
            _record("bcra_public_exposure_securities", period, securities_value, "official", securities, source_hash),
            _record("bcra_public_exposure_total", period, loans + securities_value, "calculated", securities, source_hash),
        ])

    # Variaciones nominales interanuales. Se publican explícitamente como nominales.
    levels = {(row["series_id"], row["period"]): Decimal(row["value"]) for row in records}
    for row in list(records):
        previous_period = f"{int(row['period'][:4]) - 1:04d}{row['period'][4:]}"
        previous = levels.get((row["series_id"], previous_period))
        current = Decimal(row["value"])
        if previous and previous > 0:
            records.append(row | {
                "series_id": f"{row['series_id']}_nominal_yoy",
                "value": format(((current / previous - 1) * 100).quantize(Decimal("0.000001")), "f"),
                "unit": "percent_change",
                "status": "calculated",
            })
    return records


def _load_series(path: Path, series_id: str) -> tuple[dict[str, Decimal], str]:
    if not path.exists():
        raise PipelineError(f"crédito BCRA: falta el insumo {path}")
    content = path.read_bytes()
    with path.open(encoding="utf-8", newline="") as handle:
        values = {
            row["period"]: Decimal(row["value"])
            for row in csv.DictReader(handle)
            if row["series_id"] == series_id
        }
    if not values:
        raise PipelineError(f"crédito BCRA: falta la serie {series_id} en {path}")
    return values, hashlib.sha256(content).hexdigest()


def _quarter_number(period: str) -> int:
    year, quarter = period.split("-Q")
    return int(year) * 4 + int(quarter) - 1


def _gdp_denominators(gdp: dict[str, Decimal]) -> dict[int, Decimal]:
    quarterly = {_quarter_number(period): value for period, value in gdp.items()}
    denominators: dict[int, Decimal] = {}
    for quarter in sorted(quarterly):
        window = [quarterly.get(quarter - offset) for offset in range(4)]
        if all(value is not None for value in window):
            # La serie trimestral corriente del INDEC está anualizada. El promedio
            # de cuatro trimestres equivale al PIB nominal de los últimos 12 meses.
            denominators[quarter] = sum(window, Decimal()) / Decimal(4)  # type: ignore[arg-type]
    return denominators


def calculate_derived(records: list[dict[str, str]], inflation_path: Path, gdp_path: Path) -> list[dict[str, str]]:
    cpi, inflation_hash = _load_series(inflation_path, "indec_ipc_general_index")
    gdp, gdp_hash = _load_series(gdp_path, "indec_gdp_current_quarterly")
    if REAL_BASE_PERIOD not in cpi:
        raise PipelineError(f"crédito BCRA: IPC base {REAL_BASE_PERIOD} ausente")

    levels = {
        (row["series_id"], row["period"]): Decimal(row["value"])
        for row in records
        if row["series_id"] in LEVEL_SERIES
    }
    bases = {
        series_id: levels.get((series_id, REAL_BASE_PERIOD))
        for series_id in LEVEL_SERIES
    }
    missing_bases = sorted(series_id for series_id, value in bases.items() if value is None)
    if missing_bases:
        raise PipelineError(f"crédito BCRA: faltan bases {REAL_BASE_PERIOD}: {', '.join(missing_bases)}")

    denominators = _gdp_denominators(gdp)
    if not denominators:
        raise PipelineError("crédito BCRA: no se pudo anualizar el PIB trimestral")
    available_quarters = sorted(denominators)
    derived: list[dict[str, str]] = []
    for row in records:
        series_id, period = row["series_id"], row["period"]
        if series_id not in LEVEL_SERIES:
            continue
        current = Decimal(row["value"])
        if period in cpi and period >= min(cpi):
            base = bases[series_id]
            assert base is not None
            real_index = (current / cpi[period]) / (base / cpi[REAL_BASE_PERIOD]) * Decimal(100)
            derived.append(row | {
                "series_id": f"{series_id}_real_index",
                "value": format(real_index.quantize(Decimal("0.000001")), "f"),
                "unit": "index_dec_2019_100",
                "status": "calculated",
                "source_id": "datarg_bcra_credit_deflated_by_indec_cpi",
                "source_sha256": hashlib.sha256(
                    f"{row['source_sha256']}|{inflation_hash}".encode()
                ).hexdigest(),
            })

        year, month = map(int, period.split("-"))
        period_quarter = year * 4 + (month - 1) // 3
        usable = [quarter for quarter in available_quarters if quarter <= period_quarter]
        if usable:
            denominator = denominators[usable[-1]]
            ratio = current / denominator * Decimal(100)
            derived.append(row | {
                "series_id": f"{series_id}_gdp_ratio",
                "value": format(ratio.quantize(Decimal("0.000001")), "f"),
                "unit": "percent_gdp",
                "status": "calculated",
                "source_id": "datarg_bcra_credit_over_indec_gdp",
                "source_sha256": hashlib.sha256(
                    f"{row['source_sha256']}|{gdp_hash}".encode()
                ).hexdigest(),
            })
    return derived


def _promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    records.sort(key=lambda row: (row["series_id"], row["period"]))
    keys = [(row["series_id"], row["period"]) for row in records]
    if len(keys) != len(set(keys)):
        raise PipelineError("crédito BCRA: claves duplicadas")
    private = [row for row in records if row["series_id"] == "bcra_private_nonfinancial_credit"]
    if not private or private[0]["period"] != "1999-12":
        raise PipelineError("crédito BCRA: cobertura privada inesperada")
    target_dir = root / "data" / "processed"
    log_dir = root / "data" / "logs" / "credit"
    target_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "credit.csv"
    old: dict[tuple[str, str], str] = {}
    if target.exists():
        with target.open(encoding="utf-8", newline="") as handle:
            old = {(row["series_id"], row["period"]): row["value"] for row in csv.DictReader(handle)}
    new = {(row["series_id"], row["period"]): row["value"] for row in records}
    report = {
        "run_id": run_id, "rows": len(records), "series": len({row["series_id"] for row in records}),
        "min_period": min(row["period"] for row in records), "max_period": max(row["period"] for row in records),
        "created": len(new.keys() - old.keys()), "deleted": len(old.keys() - new.keys()),
        "modified": sum(old[key] != new[key] for key in old.keys() & new.keys()),
    }
    if old.keys() - new.keys():
        raise PipelineError("crédito BCRA: la fuente eliminó observaciones existentes")
    fd, temporary = tempfile.mkstemp(prefix="credit-", suffix=".csv", dir=target_dir)
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
    root: Path,
    private_file: Path | None = None,
    public_file: Path | None = None,
    securities_file: Path | None = None,
) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw = root / "data" / "raw"
    private = acquire("bcra_private_nonfinancial_credit_xls", PRIVATE_URL, raw, private_file)
    public = acquire("bcra_public_sector_loans_xls", PUBLIC_URL, raw, public_file)
    securities = acquire("bcra_public_securities_xls", SECURITIES_URL, raw, securities_file)
    records = extract(private, public, securities)
    records.extend(calculate_derived(
        records,
        root / "data" / "processed" / "inflation.csv",
        root / "data" / "processed" / "gdp.csv",
    ))
    return _promote(records, root, run_id)
