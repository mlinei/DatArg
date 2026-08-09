from decimal import Decimal
from pathlib import Path

import pytest

from argentina_economic_data.inflation import Artifact, PipelineError
from argentina_economic_data.reserve_requirements import SERIES, extract


def _artifact(tmp_path: Path, lines: list[str]) -> Artifact:
    path = tmp_path / "din1_ser.txt"
    path.write_text("\n".join(lines) + "\n", encoding="latin-1")
    return Artifact("test", "https://example.test/din1_ser.txt", path, "hash", path.stat().st_size, "now")


def test_extracts_panel_and_removes_only_trailing_all_zero_period(tmp_path: Path):
    lines = [
        f"{code};30/04/2026;{value}"
        for code, value in (("1554", "30.05"), ("1555", "34.42"), ("1556", "20.97"))
    ] + [f"{code};31/05/2026;0" for code in SERIES] + ["9999;31/05/2026;123"]
    records = extract(_artifact(tmp_path, lines))
    assert len(records) == 3
    assert {row["period"] for row in records} == {"2026-04"}
    assert {row["series_id"] for row in records} == {value[0] for value in SERIES.values()}
    assert Decimal(next(row["value"] for row in records if row["series_id"].endswith("_total"))) == Decimal("30.050000")


def test_keeps_genuine_zero_component_when_other_series_are_nonzero(tmp_path: Path):
    lines = [
        "1554;30/04/1985;12.5",
        "1555;30/04/1985;15",
        "1556;30/04/1985;0",
    ]
    records = extract(_artifact(tmp_path, lines))
    assert len(records) == 3
    assert next(row["value"] for row in records if row["series_id"].endswith("_fx")) == "0.000000"


def test_rejects_incomplete_panel(tmp_path: Path):
    artifact = _artifact(tmp_path, [
        "1554;30/04/2026;30.05",
        "1555;30/04/2026;34.42",
        "1556;31/03/2026;20.97",
    ])
    with pytest.raises(PipelineError, match="panel"):
        extract(artifact)
