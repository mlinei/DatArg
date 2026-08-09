from decimal import Decimal
from pathlib import Path

from argentina_economic_data.inflation import Artifact
from argentina_economic_data.treasury_liquidity import (
    ARS_DAILY_CHANGE,
    ARS_DAILY_STOCK,
    ARS_CHANGE,
    ARS_STOCK,
    USD_DAILY_CHANGE,
    USD_DAILY_STOCK,
    USD_CHANGE,
    USD_STOCK,
    extract_daily,
    extract,
)


def _artifact(path: Path, text: str, source_id: str) -> Artifact:
    path.write_text(text, encoding="latin-1")
    return Artifact(source_id, f"https://example.test/{path.name}", path, "hash", path.stat().st_size, "now")


def test_extracts_both_accounts_and_uses_last_business_day_fx(tmp_path: Path):
    months = []
    for year in range(1990, 2026):
        for month in range(1, 13):
            months.append(f"28/{month:02d}/{year}")
    months += ["30/04/2026", "31/05/2026"]
    balance_lines = []
    for index, date in enumerate(months):
        ars = Decimal("1000000") + index
        foreign = Decimal("3000000") + index
        balance_lines += [
            f"105;{date};{ars + foreign}",
            f"106;{date};{ars}",
            f"107;{date};{foreign}",
        ]
    fx_lines = []
    for date in months:
        if int(date[-4:]) < 2002:
            continue
        if date == "31/05/2026":
            fx_lines.append("271;29/05/2026;1500")
        else:
            fx_lines.append(f"271;{date};1000")
    balance = _artifact(tmp_path / "din1.txt", "\n".join(balance_lines), "balance")
    valuation = _artifact(tmp_path / "din2.txt", "\n".join(fx_lines), "fx")

    rows = extract(balance, valuation)
    values = {(row["series_id"], row["period"]): Decimal(row["value"]) for row in rows}
    last_foreign = Decimal("3000000") + len(months) - 1
    previous_foreign = last_foreign - 1

    assert values[(ARS_STOCK, "2026-05")] == (Decimal("1000000") + len(months) - 1) / 1000
    assert values[(ARS_CHANGE, "2026-05")] == Decimal("0.001000")
    assert values[(USD_STOCK, "2026-05")] == (last_foreign / 1000 / 1500).quantize(Decimal("0.000001"))
    expected_change = last_foreign / 1000 / 1500 - previous_foreign / 1000 / 1000
    assert values[(USD_CHANGE, "2026-05")] == expected_change.quantize(Decimal("0.000001"))


def test_may_2026_public_validation(tmp_path: Path):
    months = []
    for year in range(1990, 2026):
        for month in range(1, 13):
            months.append(f"28/{month:02d}/{year}")
    months.append("31/05/2026")
    balance_lines = []
    for date in months[:-1]:
        balance_lines += [f"105;{date};2", f"106;{date};1", f"107;{date};1"]
    balance_lines += [
        "105;31/05/2026;17141055368.22233",
        "106;31/05/2026;12828550485.8906",
        "107;31/05/2026;4312504882.33173",
    ]
    balance = _artifact(tmp_path / "din1.txt", "\n".join(balance_lines), "balance")
    fx_lines = []
    for date in months:
        if int(date[-4:]) < 2002:
            continue
        if date == "31/05/2026":
            fx_lines.append("271;29/05/2026;1410.2904")
        else:
            fx_lines.append(f"271;{date};1000")
    valuation = _artifact(tmp_path / "din2.txt", "\n".join(fx_lines), "fx")
    rows = extract(balance, valuation)
    usd = next(Decimal(row["value"]) for row in rows if row["series_id"] == USD_STOCK and row["period"] == "2026-05")
    # The reconstructed stock rounds to the same roughly USD 3.059bn public figure.
    assert abs(usd - Decimal("3059")) < Decimal("2")


def test_daily_extract_uses_valuation_fx_and_ignores_provisional_zero_rows(monkeypatch, tmp_path: Path):
    class Sheet:
        ncols = 6
        rows = [["", 269, 8842, 8843, 271, ""]]
        rows += [[45000 + index, 400 + index * 2, 100 + index, 300 + index, 2, ""] for index in range(501)]
        rows += [[45501, 0, 0, 0, 5, ""], ["", "", "", "", "", ""]]
        nrows = len(rows)

        def cell_value(self, row, column):
            return self.rows[row][column]

    class Workbook:
        datemode = 0

        @staticmethod
        def sheet_by_name(name):
            assert name == "Serie_diaria"
            return Sheet()

    monkeypatch.setattr("argentina_economic_data.treasury_liquidity.xlrd.open_workbook", lambda _path: Workbook())
    monkeypatch.setattr(
        "argentina_economic_data.treasury_liquidity.xlrd.xldate_as_datetime",
        lambda value, _datemode: __import__("datetime").datetime(2025, 1, 1)
        + __import__("datetime").timedelta(days=value - 45000),
    )
    artifact = _artifact(tmp_path / "daily.xls", "placeholder", "daily")
    rows = extract_daily(artifact)
    values = {(row["series_id"], row["period"]): Decimal(row["value"]) for row in rows}
    last_period = "2026-05-16"
    assert values[(ARS_DAILY_STOCK, last_period)] == Decimal("600")
    assert values[(ARS_DAILY_CHANGE, last_period)] == Decimal("1")
    assert values[(USD_DAILY_STOCK, last_period)] == Decimal("400")
    assert values[(USD_DAILY_CHANGE, last_period)] == Decimal("0.5")
    assert all(row["period"] != "2026-05-17" for row in rows)
