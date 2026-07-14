from datetime import date
from pathlib import Path

from argentina_economic_data.inflation import Artifact
from argentina_economic_data.public_debt import BCRA_VARIABLES, calculate_bcra_monthly


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
