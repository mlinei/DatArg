from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from .inflation import OUTPUT_COLUMNS, PipelineError

SOURCE_ANSES_ANNUAL = (
    "https://www.anses.gob.ar/estudiosyestadisticas/anuario-estadistico-anses-2023"
)
SOURCE_OPC_FINANCING = (
    "https://opc.gob.ar/empleo-y-prevision-social/"
    "caracterizacion-del-financiamiento-de-anses-analisis-sobre-su-evolucion-y-la-suficiencia-para-el-pago-de-prestaciones/"
)

# Recursos de ANSES por fuente, expresados como porcentaje del PIB. La serie
# reproduce el gráfico 8.1 del Anuario Estadístico ANSES 2023.
CONTRIBUTIONS_GDP = {
    2009: "5.1", 2010: "5.0", 2011: "5.2", 2012: "5.6", 2013: "5.8",
    2014: "5.4", 2015: "5.6", 2016: "5.5", 2017: "5.6", 2018: "5.0",
    2019: "4.5", 2020: "4.5", 2021: "4.1", 2022: "4.2", 2023: "4.1",
}
TAX_RESOURCES_GDP = {
    2009: "2.0", 2010: "2.1", 2011: "2.1", 2012: "2.2", 2013: "2.2",
    2014: "2.3", 2015: "2.4", 2016: "3.4", 2017: "2.5", 2018: "2.6",
    2019: "2.6", 2020: "2.8", 2021: "2.7", 2022: "2.7", 2023: "2.9",
}

# Prestaciones de la seguridad social pagadas por ANSES, porcentaje del PIB
# (gráfico 8.5 del Anuario Estadístico 2023). Este perímetro incluye los
# beneficios obtenidos mediante moratoria y por eso permite construir una
# cobertura corriente más amplia que la previsional pura.
SOCIAL_SECURITY_BENEFITS_GDP = {
    2009: "5.7", 2010: "5.3", 2011: "5.6", 2012: "6.4", 2013: "6.7",
    2014: "6.5", 2015: "7.3", 2016: "7.3", 2017: "8.0", 2018: "7.6",
    2019: "7.4", 2020: "8.4", 2021: "6.9", 2022: "6.5", 2023: "5.7",
}

# Composición de los recursos totales de ANSES en 2023, publicada en el mismo
# anuario. No debe interpretarse como asignación exclusiva al pago jubilatorio.
FINANCING_SHARES_2023 = {
    "contributions": "46.0",
    "taxes": "32.3",
    "treasury": "21.6",
    "other": "0.1",
}

# Participación de los aportes y contribuciones dentro de los recursos de
# ANSES, excluidas las Rentas de la Propiedad. Serie oficial del gráfico 8.3
# del Anuario Estadístico ANSES 2023. Este indicador mide composición de los
# ingresos y no cobertura de prestaciones.
CONTRIBUTIONS_RESOURCE_SHARE = {
    2009: "59.2", 2010: "58.8", 2011: "58.1", 2012: "59.2", 2013: "59.3",
    2014: "54.8", 2015: "53.1", 2016: "44.1", 2017: "47.7", 2018: "48.9",
    2019: "44.2", 2020: "33.5", 2021: "41.5", 2022: "43.2", 2023: "46.0",
}

# Cobertura homogénea publicada por la Oficina de Presupuesto del Congreso
# (gráfico 2 de “Caracterización del financiamiento de ANSES”, septiembre de
# 2025). El numerador son aportes y contribuciones a la seguridad social y el
# denominador son prestaciones contributivas y semicontributivas (moratorias).
# No incluye PUAM, PNC ni otras prestaciones no contributivas.
CONTRIBUTORY_SEMICONTRIBUTORY_COVERAGE = {
    2009: "80", 2010: "85", 2011: "83", 2012: "80", 2013: "79",
    2014: "76", 2015: "71", 2016: "67", 2017: "63", 2018: "62",
    2019: "58", 2020: "52", 2021: "57", 2022: "61", 2023: "69",
    2024: "77",
}


def build_records(retrieved_at: str | None = None) -> list[dict[str, str]]:
    retrieved_at = retrieved_at or datetime.now(timezone.utc).isoformat()
    source_hash = hashlib.sha256(
        json.dumps(
            {
                "contributions_gdp": CONTRIBUTIONS_GDP,
                "tax_resources_gdp": TAX_RESOURCES_GDP,
                "social_security_benefits_gdp": SOCIAL_SECURITY_BENEFITS_GDP,
                "financing_shares_2023": FINANCING_SHARES_2023,
                "contributions_resource_share": CONTRIBUTIONS_RESOURCE_SHARE,
                "contributory_semicontributory_coverage": CONTRIBUTORY_SEMICONTRIBUTORY_COVERAGE,
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()
    records: list[dict[str, str]] = []

    for series_id, values in (
        ("anses_contributions_gdp", CONTRIBUTIONS_GDP),
        ("anses_tax_resources_gdp", TAX_RESOURCES_GDP),
        ("anses_social_security_benefits_gdp", SOCIAL_SECURITY_BENEFITS_GDP),
    ):
        for year, value in values.items():
            records.append({
                "series_id": series_id, "period": str(year), "frequency": "annual",
                "value": value, "unit": "percent_gdp", "status": "official",
                "source_id": "anses_annual_statistics_2023", "source_url": SOURCE_ANSES_ANNUAL,
                "source_sha256": source_hash, "retrieved_at": retrieved_at,
            })

    for year, coverage in CONTRIBUTORY_SEMICONTRIBUTORY_COVERAGE.items():
        records.append({
            "series_id": "opc_contributory_semicontributory_coverage", "period": str(year),
            "frequency": "annual", "value": coverage,
            "unit": "percent", "status": "official",
            "source_id": "opc_anses_financing_2025", "source_url": SOURCE_OPC_FINANCING,
            "source_sha256": source_hash, "retrieved_at": retrieved_at,
        })

    for year, share in CONTRIBUTIONS_RESOURCE_SHARE.items():
        records.append({
            "series_id": "anses_contributions_resource_share", "period": str(year),
            "frequency": "annual", "value": share,
            "unit": "percent", "status": "official",
            "source_id": "anses_annual_statistics_2023", "source_url": SOURCE_ANSES_ANNUAL,
            "source_sha256": source_hash, "retrieved_at": retrieved_at,
        })

    for key, value in FINANCING_SHARES_2023.items():
        records.append({
            "series_id": f"anses_financing_{key}_share", "period": "2023",
            "frequency": "annual", "value": value, "unit": "percent",
            "status": "official", "source_id": "anses_annual_statistics_2023",
            "source_url": SOURCE_ANSES_ANNUAL, "source_sha256": source_hash,
            "retrieved_at": retrieved_at,
        })

    if abs(sum(Decimal(value) for value in FINANCING_SHARES_2023.values()) - 100) > Decimal("0.01"):
        raise PipelineError("previsión social: la composición financiera no suma 100%")
    return sorted(records, key=lambda row: (row["series_id"], row["period"]))


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    target_dir = root / "data" / "processed"
    log_dir = root / "data" / "logs" / "pensions"
    target_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "pensions.csv"
    fd, temporary = tempfile.mkstemp(prefix="pensions-", suffix=".csv", dir=target_dir)
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
        "run_id": run_id, "rows": len(records),
        "series": len({row["series_id"] for row in records}),
        "min_period": min(row["period"] for row in records),
        "max_period": max(row["period"] for row in records),
    }
    (log_dir / f"{run_id}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def run(root: Path) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return promote(build_records(), root, run_id)
