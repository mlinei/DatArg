from decimal import Decimal

import pytest

from argentina_economic_data.usd_inflation import calculate


def row(series_id: str, period: str, value: str) -> dict[str, str]:
    return {
        "series_id": series_id,
        "period": period,
        "value": value,
        "retrieved_at": "2026-08-01T00:00:00Z",
    }


def test_calculates_exact_monthly_index_and_yoy_views():
    inflation = []
    exchange = []
    for year in (2023, 2024):
        for month in range(1, 13):
            period = f"{year}-{month:02d}"
            month_number = (year - 2023) * 12 + month
            inflation.append(row("indec_ipc_general_index", period, str(100 + month_number * 10)))
            exchange.append(row("argentinadatos_usd_official_retail_sell", f"{period}-01", str(80 + month_number * 5)))
            exchange.append(row("argentinadatos_usd_official_retail_sell", f"{period}-15", str(100 + month_number * 5)))

    records = calculate(inflation, exchange)
    values = {(item["series_id"], item["period"]): Decimal(item["value"]) for item in records}
    jan_level = Decimal("230") / Decimal("155")
    dec_level = Decimal("340") / Decimal("210")
    dec_2023_level = Decimal("220") / Decimal("150")

    assert values[("datarg_usd_inflation_index_jan_2024", "2024-01")] == Decimal("100.000000")
    assert values[("datarg_usd_inflation_index_jan_2024", "2024-12")] == pytest.approx(dec_level / jan_level * 100, abs=Decimal("0.000001"))
    assert values[("datarg_usd_inflation_mom", "2024-01")] == pytest.approx((jan_level / dec_2023_level - 1) * 100, abs=Decimal("0.000001"))
    assert values[("datarg_usd_inflation_yoy", "2024-01")] == pytest.approx((jan_level / (Decimal("110") / Decimal("95")) - 1) * 100, abs=Decimal("0.000001"))


def test_uses_monthly_average_of_official_daily_quotes():
    inflation = [
        row("indec_ipc_general_index", "2023-12", "100"),
        row("indec_ipc_general_index", "2024-01", "110"),
    ]
    exchange = [
        row("argentinadatos_usd_official_retail_sell", "2023-12-01", "100"),
        row("argentinadatos_usd_official_retail_sell", "2024-01-01", "100"),
        row("argentinadatos_usd_official_retail_sell", "2024-01-02", "110"),
    ]

    values = {(item["series_id"], item["period"]): Decimal(item["value"]) for item in calculate(inflation, exchange)}
    assert values[("datarg_usd_inflation_mom", "2024-01")] == pytest.approx(Decimal("4.7619047619"), abs=Decimal("0.000001"))
