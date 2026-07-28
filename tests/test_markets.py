import csv
import json
from decimal import Decimal
from pathlib import Path

import pytest

from argentina_economic_data.inflation import Artifact, PipelineError
from argentina_economic_data.markets import calculate, extract_ars, promote


def artifact(path: Path) -> Artifact:
    return Artifact("yahoo_sp_merval", "https://example.test", path, "hash", 1, "now")


def test_extracts_and_converts_merval_by_mep(tmp_path: Path):
    source = tmp_path / "merval.json"
    source.write_text(json.dumps({"chart":{"result":[{"meta":{"symbol":"^MERV"},
        "timestamp":[1547164800], "indicators":{"quote":[{"close":[33884.6]}]}}]}}), encoding="utf-8")
    ars = extract_ars(artifact(source))
    rows = calculate(ars, {"2019-01-11": Decimal("36.8")}, artifact(source))
    assert rows[0]["series_id"] == "datarg_sp_merval_mep_usd"
    assert Decimal(rows[0]["value"]) == pytest.approx(Decimal("920.777174"), abs=Decimal("0.000001"))
    assert rows[0]["status"] == "calculated"


def test_rejects_wrong_symbol(tmp_path: Path):
    source = tmp_path / "merval.json"
    source.write_text(json.dumps({"chart":{"result":[{"meta":{"symbol":"OTHER"},
        "timestamp":[], "indicators":{"quote":[{"close":[]}]}}]}}), encoding="utf-8")
    with pytest.raises(PipelineError, match="metadatos"):
        extract_ars(artifact(source))


def market_row(period: str, value: str, source_sha256: str = "new") -> dict[str, str]:
    return {
        "series_id": "datarg_sp_merval_mep_usd",
        "period": period,
        "frequency": "daily",
        "value": value,
        "unit": "usd_index_points",
        "status": "calculated",
        "source_id": "yahoo_sp_merval_divided_by_argentinadatos_mep",
        "source_url": "https://example.test",
        "source_sha256": source_sha256,
        "retrieved_at": "now",
    }


def test_promote_retains_dates_temporarily_omitted_by_source(tmp_path: Path):
    initial = [
        market_row("2026-07-23", "2100", "old"),
        market_row("2026-07-24", "2200", "old"),
    ]
    promote(initial, tmp_path, "initial")

    report = promote([
        market_row("2026-07-23", "2150"),
        market_row("2026-07-27", "2250"),
    ], tmp_path, "update")

    rows = {
        row["period"]: row
        for row in csv.DictReader(
            (tmp_path / "data" / "processed" / "markets.csv").open(encoding="utf-8")
        )
    }
    assert list(rows) == ["2026-07-23", "2026-07-24", "2026-07-27"]
    assert rows["2026-07-23"]["value"] == "2150"
    assert rows["2026-07-24"]["value"] == "2200"
    assert rows["2026-07-24"]["source_sha256"] == "old"
    assert report["created"] == 1
    assert report["deleted"] == 0
    assert report["retained_from_history"] == 1
    assert report["modified"] == 1


def test_promote_rejects_abrupt_source_history_truncation(tmp_path: Path):
    promote([market_row(f"2026-07-{day:02}", str(2000 + day)) for day in range(1, 21)],
            tmp_path, "initial")

    with pytest.raises(PipelineError, match="cobertura histórica"):
        promote([market_row("2026-07-01", "2001")], tmp_path, "truncated")
