from decimal import Decimal
from pathlib import Path

from argentina_economic_data.inflation import Artifact
from argentina_economic_data.net_reserves import calculate


def test_calculation_matches_published_controls(tmp_path: Path):
    artifact = Artifact("weekly", "https://example.test", tmp_path / "x", "abc", 0, "2026-07-18T00:00:00Z")
    gross = {"2026-06-30": Decimal(44870)}
    anchors = {"2026-06-30": Decimal("12335.212397")}
    ooii = {"2026-06-30": Decimal("120.217062")}
    swap = {"2026-06-30": Decimal("19158.5")}
    repos = {"2026-05-31": Decimal("8384.84"), "2026-06-30": Decimal(8385), "2026-07-17": Decimal(2385)}
    overrides = {
        "2026-06-30": {"gross_override": Decimal(44873), "encajes_override": Decimal(12335), "swap_override": Decimal(19143), "ooii_override": Decimal(120)},
        "2026-07-17": {"gross_override": Decimal(48784), "encajes_override": Decimal(16526), "swap_override": Decimal(19180), "ooii_override": Decimal(123)},
    }
    rows = calculate(gross, anchors, ooii, {}, swap, repos, overrides, artifact)
    net = {r["period"]: r["value"] for r in rows if r["series_id"] == "bcra_net_international_reserves"}
    assert net == {"2026-06-30": "4890.000000", "2026-07-17": "10570.000000"}
