from pathlib import Path

import pandas as pd
import pytest

from argentina_economic_data.inflation import Artifact, PipelineError
from argentina_economic_data.registered_employment import _sheet_records


def artifact(tmp_path: Path) -> Artifact:
    source = tmp_path / "employment.xlsx"
    source.touch()
    return Artifact("trabajo_registered_employment_sipa", "https://example.test/employment.xlsx", source, "hash", 1, "now")


def sheet(periods: int = 14) -> pd.DataFrame:
    rows = [[None, None], [None, "Total"]]
    for period in pd.period_range("2009-01", periods=periods, freq="M"):
        rows.append([period.to_timestamp(), 100 + len(rows) - 2])
    return pd.DataFrame(rows)


def test_builds_level_index_and_interannual_change(tmp_path: Path):
    records, levels = _sheet_records(sheet(), {"total": ("total", "Total")}, "sector", artifact(tmp_path))

    assert levels["total"]["2009-01"] == 100
    assert next(row for row in records if row["series_id"].endswith("_index") and row["period"] == "2009-01")["value"] == "100.000000"
    yoy = next(row for row in records if row["series_id"].endswith("_yoy") and row["period"] == "2010-01")
    assert float(yoy["value"]) == pytest.approx(12.0)


def test_rejects_a_missing_official_column(tmp_path: Path):
    with pytest.raises(PipelineError, match="columnas ausentes"):
        _sheet_records(sheet(), {"industria": ("manufacturing", "Industria")}, "sector", artifact(tmp_path))
