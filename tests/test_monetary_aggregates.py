from pathlib import Path

from argentina_economic_data.inflation import Artifact
from argentina_economic_data.monetary_aggregates import extract_history


def test_extract_history_uses_current_peso_and_millions(tmp_path: Path, monkeypatch):
    source = tmp_path / "panhis.xls"
    source.write_bytes(b"fixture")

    class Sheet:
        nrows = 28
        rows = {
            26: {0: 1991.12, 1: "Dic.", 3: "Pesos", 6: 9000},
            27: {0: 1992.01, 1: "Ene.", 3: "Pesos", 6: 123456},
        }

        def cell_value(self, row, column):
            return self.rows.get(row, {}).get(column, "")

    class Workbook:
        def sheet_by_name(self, _name):
            return Sheet()

    monkeypatch.setattr("argentina_economic_data.monetary_aggregates.xlrd.open_workbook", lambda _path: Workbook())
    artifact = Artifact("test", "https://example.test/panhis.xls", source, "abc", len(source.read_bytes()), "2026-01-01T00:00:00Z")
    rows = extract_history(artifact)
    assert len(rows) == 5
    assert {row["period"] for row in rows} == {"1992-01"}
    assert {row["value"] for row in rows} == {"123.456000"}
