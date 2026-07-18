from pathlib import Path

import pytest

from argentina_economic_data.consolidated_debt import calculate_benchmark_series, extract, extract_facimex_annual
from argentina_economic_data.inflation import Artifact, PipelineError


TEXT = """
Deuda Bruta 465.353.130 76,3%
Fondo de garantía de sustentabilidad 68.456.800 11,2%
Depósitos del tesoro en el BCRA (ARS y USD) 11.690.555 1,9%
Adelantos transitorios 2.230.652 0,4%
Bonos y Letras instransf. del tesoro en manos del BCRA 103.840.678 17,0%
Pasivos remunerados del BCRA 14.025.208 2,3%
Reservas netas 4.439.143 0,7%
Deuda neta sector público 288.720.510 47,3%
"""


def artifact():
    return Artifact("test", "https://example.test/source.pdf", Path("x"), "a" * 64, 1000, "2025-01-01T00:00:00Z")


def test_extracts_and_validates_published_identity():
    rows = extract(artifact(), TEXT)
    values = {r["series_id"]: r["value"] for r in rows}
    assert values["estimated_net_consolidated_public_sector_debt"] == "288720.510000"
    assert values["estimated_net_consolidated_public_sector_debt_gdp"] == "47.300000"
    assert all(r["status"] == "estimated" for r in rows)


def test_rejects_inconsistent_total():
    with pytest.raises(PipelineError, match="identidad inconsistente"):
        extract(artifact(), TEXT.replace("288.720.510", "288.000.000"))


def test_calculates_comparable_series_and_gdp_ratio(tmp_path):
    path = tmp_path / "benchmarks.csv"
    path.write_text(
        "period,gross_private_and_ooi_million_usd,net_reserves_million_usd,bcra_liabilities_million_usd,gross_total_million_usd,gross_debt_percent_gdp,published_net_debt_million_usd\n"
        "2003-Q2,146061.1,1300,5862,152587,78,150623.1\n"
        "2007-Q3,141085.924,41829,18532.80255,165206,35,117789.72655\n"
        "2015-Q3,93703,-1446,38532.91796,239959,52.6,133681.91796\n"
        "2019-11,195811.88,12100,17422.06596,313299,89.8,201133.94596\n"
        "2023-11,229800.24,-10500,70043.66141,425556,97.8,310343.90141\n"
        "2026-05,268392.88,-9100,15546.50884,479273,70,293039.38884\n",
        encoding="utf-8",
    )
    rows = calculate_benchmark_series(path, artifact())
    values = {(r["series_id"], r["period"]): r["value"] for r in rows}
    assert values[("estimated_comparable_net_public_debt", "2026-05")] == "293039.388840"
    assert values[("estimated_comparable_net_public_debt_gdp", "2026-05")] == "42.799735"


def test_extracts_facimex_annual_points(tmp_path):
    path = tmp_path / "facimex.csv"
    path.write_text(
        "period,value_million_usd,percent_gdp,value_basis\n"
        "2023-Q3,265600,40.6,published_difference\n"
        "2024-Q4,240663.576663,37.7,derived\n"
        "2025-Q4,247000,36,published\n"
        "2026-Q1,254000,36.9,published\n",
        encoding="utf-8",
    )
    rows = extract_facimex_annual(path, artifact())
    values = {(r["series_id"], r["period"]): r["value"] for r in rows}
    assert values[("estimated_facimex_net_consolidated_debt", "2025-Q4")] == "247000.000000"
    assert values[("estimated_facimex_net_consolidated_debt_gdp", "2026-Q1")] == "36.900000"
