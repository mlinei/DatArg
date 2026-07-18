from datetime import date
from pathlib import Path

from argentina_economic_data.inflation import Artifact
import pandas as pd

from argentina_economic_data.public_debt import BCRA_VARIABLES, calculate_bcra_monthly, extract_gdp_ratio


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
