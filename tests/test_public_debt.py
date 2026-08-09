from datetime import date
from pathlib import Path

from argentina_economic_data.inflation import Artifact
import pandas as pd

from argentina_economic_data.public_debt import (
    BCRA_VARIABLES,
    DAILY_ARS_SECURITIES,
    DAILY_FX_SECURITIES,
    DAILY_GOVERNMENT_DEPOSITS,
    DAILY_LELIQ_NOTALIQ,
    DAILY_LIQUIDITY_BILLS,
    DAILY_MONETARY_LIABILITIES,
    DAILY_NOCOM,
    DAILY_PASSIVE_REPOS,
    DAILY_SDR_ALLOCATIONS,
    DAILY_VALUATION_FX,
    calculate_bcra_broad_value,
    calculate_bcra_monthly,
    extract_bcra_total_accounting_monthly,
    extract_gdp_ratio,
)


def test_bcra_total_converts_ars_and_adds_usd_repo():
    d = date(2025, 6, 30)
    series = {i: {d: 0} for i in BCRA_VARIABLES}
    series[1258][d] = 100
    series[1259][d] = 200
    series[1260][d] = 300
    series[1262][d] = 400
    series[76][d] = 2
    series[5][d] = 100
    artifact = Artifact("bcra", "https://example.test", Path("x"), "a"*64, 100, "2025-01-01T00:00:00Z")
    rows = calculate_bcra_monthly(series, {i: artifact for i in BCRA_VARIABLES})
    assert rows[0]["period"] == "2025-06"
    assert rows[0]["value"] == "12.000000"
    assert rows[0]["status"] == "calculated"


def test_extracts_official_debt_to_gdp_ratio(tmp_path):
    frame = pd.DataFrame([[None] * 5 for _ in range(10)])
    frame.iat[7, 3] = "2000"
    frame.iat[7, 4] = "1er. Trim. 2026 (1)"
    frame.iat[9, 2] = "Deuda Bruta de la Administración Central"
    frame.iat[9, 3] = 0.45
    frame.iat[9, 4] = 0.734188
    path = tmp_path / "quarterly.xlsx"
    with pd.ExcelWriter(path) as writer:
        frame.to_excel(writer, sheet_name="A.4.7", header=False, index=False)
    artifact = Artifact("quarterly", "https://example.test", path, "a" * 64, path.stat().st_size, "2026-07-18T00:00:00Z")

    rows = extract_gdp_ratio(artifact)

    assert [(row["period"], row["frequency"], row["value"]) for row in rows] == [
        ("2000", "annual", "45.000000"),
        ("2026-Q1", "quarterly", "73.418800"),
    ]
    assert all(row["unit"] == "percent_gdp" for row in rows)


def test_broad_bcra_liabilities_add_components_without_double_counting():
    values = {
        DAILY_MONETARY_LIABILITIES: 1_000,
        DAILY_ARS_SECURITIES: 100,
        DAILY_FX_SECURITIES: 200,
        DAILY_LELIQ_NOTALIQ: 300,
        DAILY_NOCOM: 400,
        DAILY_PASSIVE_REPOS: 500,
        DAILY_LIQUIDITY_BILLS: 600,
        DAILY_GOVERNMENT_DEPOSITS: 700,
        DAILY_VALUATION_FX: 100,
        DAILY_SDR_ALLOCATIONS: 2,
    }

    assert calculate_bcra_broad_value({key: pd.to_numeric(value) for key, value in values.items()}) == 40


def test_extracts_total_accounting_liabilities_from_first_weekly_block(tmp_path):
    path = tmp_path / "weekly.xlsx"
    with pd.ExcelWriter(path) as writer:
        for year in range(1998, 2026):
            months = range(1, 13) if year < 2025 else (1,)
            frame = pd.DataFrame([[None] * (len(months) + 1) for _ in range(12)])
            frame.iat[5, 0] = "Tipo de Cambio"
            frame.iat[8, 0] = "TOTAL DEL PASIVO"
            frame.iat[10, 0] = "TOTAL DEL PASIVO"
            for column, month in enumerate(months, start=1):
                frame.iat[3, column] = pd.Timestamp(year=year, month=month, day=15)
                frame.iat[5, column] = 1_000
                frame.iat[8, column] = 100_000_000
                # Un bloque de reexpresión posterior no debe reemplazar la serie principal.
                frame.iat[10, column] = 999_000_000
            if year == 2025:
                frame.iat[3, 1] = pd.Timestamp("2025-01-31")
                frame.iat[5, 1] = 2_000
                frame.iat[8, 1] = 240_000_000
            frame.to_excel(writer, sheet_name=f"serie semanal {year}", header=False, index=False)
    artifact = Artifact("weekly", "https://example.test", path, "a" * 64, path.stat().st_size, "2026-01-01T00:00:00Z")

    rows = extract_bcra_total_accounting_monthly(artifact)

    assert rows[-1]["period"] == "2025-01"
    assert rows[-1]["value"] == "120.000000"
