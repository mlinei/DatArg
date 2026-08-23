from __future__ import annotations

from pathlib import Path

import pytest

from argentina_economic_data.inflation import Artifact, PipelineError
from argentina_economic_data.public_spending import FUNCTIONS, extract


class _Sheet:
    def __init__(self, changed_label: bool = False) -> None:
        self.ncols = 47
        self.nrows = len(FUNCTIONS) + 6
        self.values: dict[tuple[int, int], object] = {}
        for column, year in enumerate(range(1980, 2025), 2):
            self.values[3, column] = f"{year}*" if year >= 2021 else float(year)
        for row, (code, (_slug, label)) in enumerate(FUNCTIONS.items(), 5):
            self.values[row, 0] = code
            self.values[row, 1] = "Rótulo modificado" if changed_label and code == "1.2.2" else label
            for column in range(2, self.ncols):
                self.values[row, column] = 20.0 if code == "1.0" else 2.0

    def cell_value(self, row: int, column: int) -> object:
        return self.values.get((row, column), "")


class _Book:
    def __init__(self, sheet: _Sheet) -> None:
        self.sheet = sheet

    def sheet_by_name(self, name: str) -> _Sheet:
        assert name == "% del PIB"
        return self.sheet


def _artifact(tmp_path: Path) -> Artifact:
    path = tmp_path / "gasto.xls"
    path.write_bytes(b"xls")
    return Artifact("test", "https://example.test/gasto.xls", path, "abc", 3, "2026-08-17T00:00:00Z")


def test_extract_preserves_official_names_and_calculates_shares(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("argentina_economic_data.public_spending.xlrd.open_workbook", lambda _path: _Book(_Sheet()))

    rows = extract(_artifact(tmp_path), "consolidated")
    indexed = {(row["series_id"], row["period"]): row for row in rows}

    health = indexed[("mecon_public_spending_consolidated_gdp_health", "2024")]
    health_share = indexed[("mecon_public_spending_consolidated_share_health", "2024")]
    assert health["value"] == "2.000000"
    assert health["status"] == "official_provisional"
    assert health_share["value"] == "10.000000"
    assert health_share["status"] == "calculated"
    assert indexed[("mecon_public_spending_consolidated_gdp_health", "2020")]["status"] == "official"


def test_extract_rejects_changed_official_label(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "argentina_economic_data.public_spending.xlrd.open_workbook",
        lambda _path: _Book(_Sheet(changed_label=True)),
    )

    with pytest.raises(PipelineError, match="cambió el rótulo 1.2.2"):
        extract(_artifact(tmp_path), "consolidated")
