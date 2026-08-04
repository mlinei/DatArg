from decimal import Decimal
import unittest

from argentina_economic_data.fx_intervention import (
    _extract_section_iv_values,
    add_adjusted_intervention,
    aggregate,
)


class FxInterventionTests(unittest.TestCase):
    def test_calendar_aggregates_preserve_signs(self):
        daily = [
            {"series_id": "bcra_fx_intervention_daily", "period": "2026-01-02", "frequency": "daily", "value": "10", "unit": "million_usd", "status": "official", "source_id": "x", "source_url": "x", "source_sha256": "x", "retrieved_at": "x"},
            {"series_id": "bcra_fx_intervention_daily", "period": "2026-01-03", "frequency": "daily", "value": "-4", "unit": "million_usd", "status": "official", "source_id": "x", "source_url": "x", "source_sha256": "x", "retrieved_at": "x"},
        ]
        records = aggregate(daily)
        values = {(row["series_id"], row["period"]): Decimal(row["value"]) for row in records}
        self.assertEqual(values[("bcra_fx_intervention_monthly", "2026-01")], Decimal("6"))
        self.assertEqual(values[("bcra_fx_intervention_annual", "2026")], Decimal("6"))

    def test_extracts_official_notional_short_and_long_positions(self):
        page = """IV. Partidas informativas\nAutoridades Monetarias Gobierno Central
        -1.946,08\n-1.946,08\n-1.947,08\n1,00\n0,00\n-25,30
        """
        short, long, net_short = _extract_section_iv_values(page)
        self.assertEqual(short, Decimal("1947.08"))
        self.assertEqual(long, Decimal("1.00"))
        self.assertEqual(net_short, Decimal("1946.08"))

    def test_adjusted_intervention_subtracts_increase_in_net_short(self):
        template = {"frequency": "monthly", "unit": "million_usd", "status": "official", "source_id": "x", "source_url": "x", "source_sha256": "x", "retrieved_at": "x"}
        spot = [template | {"series_id": "bcra_fx_intervention_monthly", "period": "2025-04", "value": "500"}, template | {"series_id": "bcra_fx_intervention_monthly", "period": "2025-05", "value": "1000"}]
        futures = [template | {"series_id": "bcra_fx_futures_net_short_position", "period": "2025-04", "value": "408.78"}, template | {"series_id": "bcra_fx_futures_net_short_position", "period": "2025-05", "value": "1946.08"}]
        records = add_adjusted_intervention(spot, futures)
        values = {(row["series_id"], row["period"]): Decimal(row["value"]) for row in records}
        self.assertEqual(values[("bcra_fx_futures_net_short_change", "2025-05")], Decimal("1537.300000"))
        self.assertEqual(values[("bcra_fx_futures_intervention_component", "2025-05")], Decimal("-1537.300000"))
        self.assertEqual(values[("bcra_fx_intervention_adjusted_monthly", "2025-05")], Decimal("-537.300000"))


if __name__ == "__main__":
    unittest.main()
