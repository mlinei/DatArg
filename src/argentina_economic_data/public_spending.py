from __future__ import annotations

import csv
import json
import os
import tempfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import xlrd

from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, acquire

SOURCE_PAGE = "https://www.argentina.gob.ar/economia/politicaeconomica/macroeconomica/gastopublicoconsolidado"
SOURCES = {
    "consolidated": ("Consolidado", "https://www.argentina.gob.ar/sites/default/files/gasto_publico_consolidado_desde_1980_2.xls"),
    "national": ("Nacional", "https://www.argentina.gob.ar/sites/default/files/gasto_publico_nacional_desde_1980_2.xls"),
    "provincial": ("Provincial", "https://www.argentina.gob.ar/sites/default/files/gasto_publico_provincial_desde_1980_2.xls"),
    "municipal": ("Municipal", "https://www.argentina.gob.ar/sites/default/files/gasto_publico_municipal_desde_1980_1.xls"),
}

# Códigos y denominaciones literales de la clasificación funcional oficial.
FUNCTIONS = {
    "1.0": ("total", "GASTO PÚBLICO TOTAL"),
    "1.1": ("state_operation", "I. FUNCIONAMIENTO DEL ESTADO"),
    "1.1.1": ("general_administration", "I.1. Administración general"),
    "1.1.2": ("justice", "I.2. Justicia"),
    "1.1.3": ("defense_security", "I.3. Defensa y seguridad"),
    "1.2": ("social_spending", "II. GASTO PÚBLICO SOCIAL"),
    "1.2.1": ("education_culture_science_technology", "II.1. Educación, cultura y ciencia y técnica"),
    "1.2.1.1": ("basic_education", "II.1.1. Educación básica"),
    "1.2.1.2": ("higher_university_education", "II.1.2. Educación superior y universitaria"),
    "1.2.1.3": ("science_technology", "II.1.3. Ciencia y técnica"),
    "1.2.1.4": ("culture", "II.1.4. Cultura"),
    "1.2.1.5": ("unspecified_education_culture", "II.1.5. Educación y cultura sin discriminar"),
    "1.2.2": ("health", "II.2. Salud"),
    "1.2.2.1": ("public_health_care", "II.2.1. Atención pública de la salud"),
    "1.2.2.2": ("health_insurance_care", "II.2.2. Obras sociales - Atención de la salud"),
    "1.2.2.3": ("inssjyp_health_care", "II.2.3. INSSJyP - Atención de la salud"),
    "1.2.3": ("drinking_water_sewerage", "II.3. Agua potable y alcantarillado"),
    "1.2.4": ("housing_urbanism", "II.4. Vivienda y urbanismo"),
    "1.2.5": ("social_promotion_assistance", "II.5. Promoción y asistencia social"),
    "1.2.5.1": ("public_social_promotion_assistance", "II.5.1. Promoción y asistencia social pública"),
    "1.2.5.2": ("health_insurance_social_benefits", "II.5.2. Obras sociales - Prestaciones sociales"),
    "1.2.5.3": ("inssjyp_social_benefits", "II.5.3. INSSJyP - Prestaciones sociales"),
    "1.2.6": ("social_security", "II.6. Previsión social"),
    "1.2.7": ("labor", "II.7. Trabajo"),
    "1.2.7.1": ("employment_programs_unemployment_insurance", "II.7.1. Programas de empleo y seguro de desempleo"),
    "1.2.7.2": ("family_allowances", "II.7.2. Asignaciones familiares"),
    "1.2.8": ("other_urban_services", "II.8. Otros servicios urbanos"),
    "1.3": ("economic_services", "III. GASTO PÚBLICO EN SERVICIOS ECONÓMICOS"),
    "1.3.1": ("primary_production", "III.1. Producción primaria"),
    "1.3.2": ("energy_fuel", "III.2. Energía y combustible"),
    "1.3.3": ("industry", "III.3. Industria"),
    "1.3.4": ("services", "III.4. Servicios"),
    "1.3.4.1": ("transport", "III.4.1. Transporte"),
    "1.3.4.2": ("communications", "III.4.2. Comunicaciones"),
    "1.3.5": ("other_economic_services", "III.5. Otros gastos en servicios económicos"),
    "1.4": ("public_debt_services", "IV. SERVICIOS DE LA DEUDA PÚBLICA"),
    "1.4.1": ("holdout_interest", "IV.1  Pago intereses Holdouts (estimado)"),
}


def _code(value: object) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _decimal(value: object) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        number = Decimal(str(value).strip().replace(",", "."))
    except (InvalidOperation, ValueError):
        return None
    return number if number >= 0 else None


def extract(artifact: Artifact, coverage: str) -> list[dict[str, str]]:
    if coverage not in SOURCES:
        raise PipelineError(f"gasto público: cobertura desconocida {coverage}")
    try:
        sheet = xlrd.open_workbook(artifact.path).sheet_by_name("% del PIB")
    except Exception as exc:
        raise PipelineError(f"gasto público: no se pudo leer la hoja % del PIB: {exc}") from exc
    years: dict[int, tuple[int, bool]] = {}
    for column in range(2, sheet.ncols):
        raw_year = str(sheet.cell_value(3, column)).strip()
        try:
            year = int(float(raw_year.rstrip("*")))
        except (TypeError, ValueError):
            continue
        if 1980 <= year <= 2100:
            years[column] = (year, raw_year.endswith("*"))
    if sorted(year for year, _provisional in years.values()) != list(range(1980, 2025)):
        raise PipelineError("gasto público: cobertura anual inesperada; se esperaban 1980-2024")
    found: dict[str, int] = {}
    for row in range(sheet.nrows):
        code = _code(sheet.cell_value(row, 0))
        if code not in FUNCTIONS:
            continue
        expected = FUNCTIONS[code][1]
        actual = str(sheet.cell_value(row, 1)).strip()
        if actual != expected:
            raise PipelineError(f"gasto público: cambió el rótulo {code}: {actual!r} (esperado {expected!r})")
        found[code] = row
    missing = set(FUNCTIONS) - set(found)
    if missing:
        raise PipelineError(f"gasto público: faltan funciones oficiales: {', '.join(sorted(missing))}")
    total_row = found["1.0"]
    source_id = f"mecon_public_spending_{coverage}"
    records: list[dict[str, str]] = []
    for code, (slug, _label) in FUNCTIONS.items():
        row = found[code]
        for column, (year, provisional) in years.items():
            value = _decimal(sheet.cell_value(row, column))
            total = _decimal(sheet.cell_value(total_row, column))
            if value is None:
                continue
            common = {
                "period": str(year), "frequency": "annual",
                "status": "official_provisional" if provisional else "official",
                "source_id": source_id, "source_url": SOURCE_PAGE,
                "source_sha256": artifact.sha256, "retrieved_at": artifact.retrieved_at,
            }
            records.append(common | {
                "series_id": f"mecon_public_spending_{coverage}_gdp_{slug}",
                "value": format(value.quantize(Decimal("0.000001")), "f"), "unit": "percent_gdp",
            })
            if slug != "total" and total and total > 0:
                share = value / total * Decimal(100)
                records.append(common | {
                    "series_id": f"mecon_public_spending_{coverage}_share_{slug}",
                    "value": format(share.quantize(Decimal("0.000001")), "f"), "unit": "percent_total_spending",
                    "status": "calculated",
                })
    return records


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    records.sort(key=lambda row: (row["series_id"], row["period"]))
    keys = [(row["series_id"], row["period"]) for row in records]
    if len(keys) != len(set(keys)):
        raise PipelineError("gasto público: claves duplicadas")
    total = [row for row in records if row["series_id"] == "mecon_public_spending_consolidated_gdp_total"]
    if len(total) != 45 or total[0]["period"] != "1980" or total[-1]["period"] != "2024":
        raise PipelineError("gasto público: serie consolidada total incompleta")
    target_dir = root / "data" / "processed"
    log_dir = root / "data" / "logs" / "public_spending"
    target_dir.mkdir(parents=True, exist_ok=True); log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "public_spending.csv"
    old: dict[tuple[str, str], str] = {}
    if target.exists():
        with target.open(encoding="utf-8", newline="") as handle:
            old = {(row["series_id"], row["period"]): row["value"] for row in csv.DictReader(handle)}
    new = {(row["series_id"], row["period"]): row["value"] for row in records}
    report = {
        "run_id": run_id, "rows": len(records), "series": len({row["series_id"] for row in records}),
        "min_period": "1980", "max_period": "2024", "created": len(new.keys() - old.keys()),
        "deleted": len(old.keys() - new.keys()), "modified": sum(old[key] != new[key] for key in old.keys() & new.keys()),
    }
    if old.keys() - new.keys():
        raise PipelineError("gasto público: la fuente eliminó observaciones existentes")
    fd, temporary = tempfile.mkstemp(prefix="public-spending-", suffix=".csv", dir=target_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS); writer.writeheader(); writer.writerows(records)
            handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    (log_dir / f"{run_id}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def run(root: Path, source_files: dict[str, Path | None] | None = None) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    source_files = source_files or {}
    records: list[dict[str, str]] = []
    for coverage, (_label, url) in SOURCES.items():
        artifact = acquire(f"mecon_public_spending_{coverage}", url, root / "data" / "raw", source_files.get(coverage))
        records.extend(extract(artifact, coverage))
    return promote(records, root, run_id)
