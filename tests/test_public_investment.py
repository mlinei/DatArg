from __future__ import annotations

from pathlib import Path

import pandas as pd

from argentina_economic_data.inflation import Artifact
from argentina_economic_data.public_investment import CAPITAL_FUNCTIONS, PUBLIC_FUNCTIONS, extract


def _total_sheet(years: list[object], title: str, values: list[float]) -> pd.DataFrame:
    frame = pd.DataFrame([[None] * (len(years) + 1) for _ in range(8)])
    frame.iat[2, 0] = title
    frame.iat[5, 0] = "Concepto"
    frame.iloc[5, 1:] = years
    frame.iat[6, 0] = title
    frame.iloc[6, 1:] = values
    return frame


def _function_sheet(years: list[object], functions: list[str], totals: list[float]) -> pd.DataFrame:
    frame = pd.DataFrame([[None] * (len(years) + 1) for _ in range(len(functions) + 7)])
    frame.iat[5, 0] = "Función"
    frame.iloc[5, 1:] = years
    for offset, function in enumerate(functions, 6):
        frame.iat[offset, 0] = function
        share = 0.2 if function == "RESTO" else 0.1
        frame.iloc[offset, 1:] = [total * share for total in totals]
    return frame


def test_extract_public_investment_levels_components_and_excludes_projection(tmp_path: Path) -> None:
    public_years = list(range(1995, 2026))
    public_gdp_years: list[object] = public_years + ["2026*"]
    public_totals = [2.0 if year == 2023 else 0.5 if year == 2025 else 1.0 for year in public_years]
    public_index = [100.0 if year == 2019 else 80.0 for year in public_years]
    capital_years = list(range(1997, 2026))
    capital_totals = [2.0 if year == 2023 else 0.5 if year == 2025 else 1.0 for year in capital_years]
    capital_index = [100.0 if year == 2019 else 80.0 for year in capital_years]
    recent_years = list(range(2016, 2026))
    path = tmp_path / "investment.xlsx"
    with pd.ExcelWriter(path) as writer:
        _total_sheet(public_years, "Inversión Pública total", public_index).to_excel(writer, sheet_name="serie 2", header=False, index=False)
        _total_sheet(public_gdp_years, "Inversión Pública total", public_totals + [0.2]).to_excel(writer, sheet_name="serie 3", header=False, index=False)
        _function_sheet(public_gdp_years, list(PUBLIC_FUNCTIONS), public_totals + [0.2]).to_excel(writer, sheet_name="serie 4", header=False, index=False)
        _function_sheet(public_years, [key for key in PUBLIC_FUNCTIONS if key != "RESTO"], [100.0] * len(public_years)).to_excel(writer, sheet_name="serie 6", header=False, index=False)
        _total_sheet(capital_years + ["2026*"], "Gastos de Capital", capital_totals + [0.4]).to_excel(writer, sheet_name="serie 7", header=False, index=False)
        _total_sheet(capital_years, "Gastos de Capital", capital_index).to_excel(writer, sheet_name="serie 9", header=False, index=False)
        _function_sheet(recent_years, list(CAPITAL_FUNCTIONS), [1.0] * len(recent_years)).to_excel(writer, sheet_name="serie 10", header=False, index=False)
        _function_sheet(recent_years, list(CAPITAL_FUNCTIONS), [100.0] * len(recent_years)).to_excel(writer, sheet_name="serie 12", header=False, index=False)
    artifact = Artifact("test", "https://example.test/investment.xlsx", path, "abc", path.stat().st_size, "2026-07-19T00:00:00Z")

    rows = extract(artifact)
    values = {(row["series_id"], row["period"]): row["value"] for row in rows}

    assert values[("jgm_public_investment_real_index", "2019")] == "100.000000"
    assert values[("jgm_public_investment_gdp_ratio", "2025")] == "0.500000"
    assert values[("jgm_public_investment_function_gdp_ratio_transport", "2023")] == "0.200000"
    assert values[("jgm_capital_expenditure_real_index", "2019")] == "100.000000"
    assert not any(row["period"] == "2026" for row in rows)
