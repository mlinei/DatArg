from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from argentina_economic_data.fiscal import FISCAL_PAGE, TAX_HISTORY_PAGE, calculate, extract_fiscal, extract_tax
from argentina_economic_data.inflation import Artifact, OUTPUT_COLUMNS


def artifact(path: Path, url: str) -> Artifact:
    return Artifact("test", url, path, "abc", path.stat().st_size, "2026-07-18T00:00:00Z")


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def source_row(series_id: str, period: str, value: str) -> dict[str, str]:
    return {
        "series_id": series_id, "period": period, "frequency": "monthly", "value": value,
        "unit": "million_ars_current", "status": "official", "source_id": "test",
        "source_url": FISCAL_PAGE, "source_sha256": "abc", "retrieved_at": "2026-07-18T00:00:00Z",
    }


def test_extract_tax_finds_year_months_and_official_total(tmp_path: Path) -> None:
    frame = pd.DataFrame([[None] * 15 for _ in range(20)])
    frame.iat[4, 1] = "RECURSOS TRIBUTARIOS AÑO 2025 (1)"
    frame.iloc[8, 2:14] = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    frame.iat[15, 1] = "TOTAL REC. TRIBUTARIOS"
    frame.iloc[15, 2:14] = range(100, 112)
    path = tmp_path / "tax.xlsx"
    with pd.ExcelWriter(path) as writer:
        frame.to_excel(writer, sheet_name="Internet", header=False, index=False)

    rows = extract_tax(artifact(path, TAX_HISTORY_PAGE))

    assert len(rows) == 12
    assert rows[0]["period"] == "2025-01"
    assert rows[-1]["value"] == "111.000000"


def test_extract_fiscal_reads_primary_and_financial_including_prior_year(tmp_path: Path) -> None:
    frame = pd.DataFrame([[None] * 10 for _ in range(20)])
    frame.iat[5, 6] = datetime(2025, 1, 1)
    frame.iat[5, 7] = datetime(2024, 1, 1)
    frame.iat[12, 1] = "RESULTADO PRIMARIO"
    frame.iat[12, 6], frame.iat[12, 7] = 250, 100
    frame.iat[15, 1] = "RESULTADO FINANCIERO NETO (*)"
    frame.iat[15, 6], frame.iat[15, 7] = -50, -75
    path = tmp_path / "fiscal.xlsx"
    with pd.ExcelWriter(path) as writer:
        frame.to_excel(writer, sheet_name="IMIG", header=False, index=False)

    rows = extract_fiscal(artifact(path, FISCAL_PAGE))
    values = {(row["series_id"], row["period"]): row["value"] for row in rows}

    assert values[("mecon_fiscal_primary_nominal_monthly", "2025-01")] == "250.000000"
    assert values[("mecon_fiscal_financial_nominal_monthly", "2024-01")] == "-75.000000"


def test_calculate_deflates_revenue_and_builds_annual_fiscal_ratios(tmp_path: Path) -> None:
    inflation = [
        {**source_row("indec_ipc_general_index", "2024-01", "100"), "unit": "index"},
        {**source_row("indec_ipc_general_index", "2025-01", "200"), "unit": "index"},
        {**source_row("indec_ipc_general_index", "2025-12", "200"), "unit": "index"},
    ]
    gdp = [{**source_row("indec_gdp_current_annual", "2025", "1200"), "frequency": "annual"}]
    write_rows(tmp_path / "inflation.csv", inflation)
    write_rows(tmp_path / "gdp.csv", gdp)
    nominal = [
        source_row("mecon_tax_revenue_total_nominal_monthly", "2024-01", "100"),
        source_row("mecon_tax_revenue_total_nominal_monthly", "2025-01", "300"),
    ]
    for month in range(1, 13):
        nominal.append(source_row("mecon_fiscal_primary_nominal_monthly", f"2025-{month:02d}", "10"))
        nominal.append(source_row("mecon_fiscal_financial_nominal_monthly", f"2025-{month:02d}", "-5"))
    rows = calculate(nominal, tmp_path / "inflation.csv", tmp_path / "gdp.csv")
    values = {(row["series_id"], row["period"]): row["value"] for row in rows}

    assert values[("mecon_tax_revenue_total_real_yoy", "2025-01")] == "50.000000"
    assert values[("mecon_fiscal_primary_annual_gdp", "2025")] == "10.000000"
    assert values[("mecon_fiscal_financial_annual_gdp", "2025")] == "-5.000000"
