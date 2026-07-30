from decimal import Decimal
import unittest

from argentina_economic_data.fx_intervention import aggregate


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


if __name__ == "__main__":
    unittest.main()
