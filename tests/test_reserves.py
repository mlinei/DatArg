import json
from pathlib import Path

import pytest

from argentina_economic_data.inflation import Artifact, PipelineError
from argentina_economic_data.reserves import extract, promote


def test_extracts_official_gross_reserves(tmp_path: Path):
    path = tmp_path/"source.json"
    path.write_text(json.dumps({"status":200,"results":[{"idVariable":1,"detalle":[{"fecha":"2026-01-02","valor":45000}]}]}), encoding="utf-8")
    artifact = Artifact("test", "https://example.test", path, "h", 100, "t")
    row = extract(artifact)[0]
    assert row["series_id"] == "bcra_gross_international_reserves"
    assert row["value"] == "45000.000000"
    assert row["status"] == "official_provisional"


def test_rejects_wrong_variable(tmp_path: Path):
    path = tmp_path/"source.json"
    path.write_text(json.dumps({"status":200,"results":[{"idVariable":2,"detalle":[{"fecha":"2026-01-02","valor":1}]}]}), encoding="utf-8")
    with pytest.raises(PipelineError, match="respuesta inesperada"):
        extract(Artifact("test", "https://example.test", path, "h", 100, "t"))


def reserve_row(period: str) -> dict[str, str]:
    return {
        "series_id": "bcra_gross_international_reserves",
        "period": period,
        "frequency": "daily",
        "value": "17314.000000",
        "unit": "million_usd",
        "status": "official_provisional",
        "source_id": "bcra_monetary_variable_1",
        "source_url": "https://example.test",
        "source_sha256": "hash",
        "retrieved_at": "2026-10-22T00:00:00Z",
    }


def test_promote_accepts_bcra_historical_backfill(tmp_path: Path):
    report = promote([reserve_row("1996-01-02")], tmp_path, "backfill")

    assert report["min_period"] == "1996-01-02"


def test_promote_rejects_truncated_initial_coverage(tmp_path: Path):
    with pytest.raises(PipelineError, match="cobertura inicial inesperada"):
        promote([reserve_row("1996-01-04")], tmp_path, "truncated")
