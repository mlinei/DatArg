import json
from decimal import Decimal
from pathlib import Path

import pytest

from argentina_economic_data.inflation import Artifact, PipelineError
from argentina_economic_data.markets import calculate, extract_ars


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
