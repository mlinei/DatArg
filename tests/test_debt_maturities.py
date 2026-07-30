from datetime import datetime
from pathlib import Path

import pandas as pd

from argentina_economic_data.debt_maturities import extract, promote
from argentina_economic_data.inflation import Artifact


def make_workbook(path: Path) -> None:
    specs = {
        "A.3.2": (2026, 4, 9, "capital"),
        "A.3.3": (2026, 4, 9, "interest"),
        "A.3.4": (2027, 1, 12, "capital"),
        "A.3.5": (2027, 1, 12, "interest"),
    }
    with pd.ExcelWriter(path) as writer:
        for sheet_name, (year, first_month, count, service) in specs.items():
            frame = pd.DataFrame([[None] * (count + 2) for _ in range(111)])
            frame.iat[7, 1] = "(En millones de U$S - Stock de deuda y tipo de cambio 31/03/2026)"
            for offset in range(count):
                month = first_month + offset
                frame.iat[8, offset + 2] = datetime(year, month, 1)
                if service == "capital":
                    frame.iat[12, offset + 2] = 80
                    frame.iat[16, offset + 2] = 10
                    frame.iat[32, offset + 2] = 20
                    frame.iat[34, offset + 2] = 50
                    frame.iat[49, offset + 2] = 25
                else:
                    frame.iat[12, offset + 2] = 30
                    frame.iat[16, offset + 2] = 10
                    frame.iat[35, offset + 2] = 20
                    frame.iat[76, offset + 2] = 7
            frame.iat[12, 1] = "TOTAL "
            frame.iat[16, 1] = "PRÉSTAMOS"
            if service == "capital":
                frame.iat[32, 1] = "ADELANTOS TRANSITORIOS BCRA"
                frame.iat[34, 1] = "TÍTULOS PÚBLICOS Y LETRAS DEL TESORO"
                frame.iat[49, 1] = "BONO R.A./U$S/1,00%/09-07-2029"
            else:
                frame.iat[35, 1] = "TÍTULOS PÚBLICOS Y LETRAS DEL TESORO"
                frame.iat[76, 1] = "BONO R.A./U$S/1,00%/09-07-2029"
            frame.to_excel(writer, sheet_name=sheet_name, header=False, index=False)


def artifact(path: Path) -> Artifact:
    return Artifact(
        source_id="mecon_quarterly_treasury_maturity_profile",
        url="https://www.argentina.gob.ar/sites/default/files/deuda_publica_31-03-2026.xlsx",
        path=path,
        sha256="fixture",
        size=path.stat().st_size,
        retrieved_at="2026-07-30T00:00:00Z",
    )


def test_extracts_official_monthly_totals_and_instruments(tmp_path):
    path = tmp_path / "debt.xlsx"
    make_workbook(path)
    rows = extract(artifact(path))
    july_capital = next(
        row for row in rows
        if row["period"] == "2026-07" and row["service_type"] == "capital"
        and row["detail_level"] == "total"
    )
    assert july_capital["snapshot_date"] == "2026-03-31"
    assert july_capital["value"] == "80.000000"
    assert any(
        row["instrument"] == "BONO R.A./U$S/1,00%/09-07-2029"
        and row["period"] == "2026-07" and row["service_type"] == "capital"
        for row in rows
    )


def test_promote_preserves_previous_snapshots(tmp_path):
    path = tmp_path / "debt.xlsx"
    make_workbook(path)
    rows = extract(artifact(path))
    first = promote(rows, tmp_path, "first")
    second = promote(rows, tmp_path, "second")
    assert first["snapshot_date"] == "2026-03-31"
    assert second["stored_rows"] == first["stored_rows"]
