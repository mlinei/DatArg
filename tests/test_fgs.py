import csv
from decimal import Decimal

from argentina_economic_data.fgs import BUCKETS, SNAPSHOTS, build_records


def test_official_components_reconcile_with_totals():
    for snapshot in SNAPSHOTS.values():
        assert abs(sum(Decimal(str(v)) for v in snapshot[:12]) - Decimal(str(snapshot[12]))) <= 2


def test_builds_ccl_total_and_complete_composition(tmp_path):
    target = tmp_path / "data" / "processed"
    target.mkdir(parents=True)
    with (target / "exchange_rates.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["series_id", "period", "value", "source_sha256", "retrieved_at"])
        writer.writeheader()
        for year in SNAPSHOTS:
            writer.writerow({"series_id": "argentinadatos_usd_ccl_sell", "period": f"{year}-12-31", "value": "100", "source_sha256": "fx", "retrieved_at": "2026-01-01T00:00:00Z"})
    rows = build_records(tmp_path)
    assert len(rows) == len(SNAPSHOTS) * (1 + 2 * len(BUCKETS))
    total_2025 = next(row for row in rows if row["series_id"] == "datarg_fgs_total_ccl_usd" and row["period"] == "2025")
    assert total_2025["value"] == "1061417.850"
    shares = [Decimal(row["value"]) for row in rows if row["period"] == "2025" and row["series_id"].endswith("_share")]
    assert abs(sum(shares) - 100) < Decimal("0.01")
