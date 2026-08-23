from decimal import Decimal

from argentina_economic_data.pensions import build_records


def test_opc_coverage_uses_a_homogeneous_perimeter() -> None:
    rows = {
        row["period"]: row for row in build_records("2026-01-01T00:00:00+00:00")
        if row["series_id"] == "opc_contributory_semicontributory_coverage"
    }
    assert Decimal(rows["2022"]["value"]) == Decimal("61")
    assert Decimal(rows["2023"]["value"]) == Decimal("69")
    assert Decimal(rows["2024"]["value"]) == Decimal("77")
    assert rows["2024"]["status"] == "official"


def test_2023_financing_shares_sum_to_one_hundred() -> None:
    rows = [
        row for row in build_records("2026-01-01T00:00:00+00:00")
        if row["series_id"].startswith("anses_financing_")
    ]
    assert sum(Decimal(row["value"]) for row in rows) == Decimal("100.0")


def test_contributions_resource_share_is_the_official_2009_2023_series() -> None:
    rows = {
        row["period"]: row for row in build_records("2026-01-01T00:00:00+00:00")
        if row["series_id"] == "anses_contributions_resource_share"
    }
    assert len(rows) == 15
    assert Decimal(rows["2009"]["value"]) == Decimal("59.2")
    assert Decimal(rows["2020"]["value"]) == Decimal("33.5")
    assert Decimal(rows["2023"]["value"]) == Decimal("46.0")
    assert rows["2023"]["status"] == "official"


def test_invalid_mixed_perimeter_coverage_is_not_emitted() -> None:
    series = {row["series_id"] for row in build_records("2026-01-01T00:00:00+00:00")}
    assert "anses_pure_contributory_coverage" not in series
    assert "anses_broad_contributory_coverage" not in series
