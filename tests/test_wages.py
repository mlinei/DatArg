import csv
from decimal import Decimal
from pathlib import Path

import pytest

from argentina_economic_data.inflation import Artifact, PipelineError
from argentina_economic_data.wages import add_real_indices, extract


HEADER = "periodo;IS_sector_privado_registrado;IS_sector_publico;IS_total_registrado;IS_sector_no_registrado;IS_indice_total\n"


def artifact(path: Path) -> Artifact:
    return Artifact("indec_wage_index", "https://example.test/wages.csv", path, "hash", 1, "now")


def test_extracts_official_wage_segments(tmp_path: Path):
    source = tmp_path / "wages.csv"
    source.write_text(HEADER + "1/10/2016;100;100;100;100;100\n1/11/2016;101,5;102;101,7;103;102\n", encoding="utf-8")
    rows = extract(artifact(source))
    assert len(rows) == 10
    public = next(row for row in rows if row["series_id"] == "indec_wage_public_nominal_index" and row["period"] == "2016-11")
    assert public["value"] == "102.000000"
    assert public["status"] == "official"


def test_calculates_real_index_as_wage_over_cpi(tmp_path: Path):
    source = tmp_path / "wages.csv"
    source.write_text(HEADER + "1/12/2016;100;100;100;100;100\n1/1/2017;120;120;120;120;120\n", encoding="utf-8")
    inflation = tmp_path / "inflation.csv"
    with inflation.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["series_id", "period", "value"]); writer.writeheader()
        writer.writerows([
            {"series_id": "indec_ipc_general_index", "period": "2016-12", "value": "100"},
            {"series_id": "indec_ipc_general_index", "period": "2017-01", "value": "110"},
        ])
    rows = add_real_indices(extract(artifact(source)), inflation, artifact(source))
    real = next(row for row in rows if row["series_id"] == "indec_wage_total_real_index" and row["period"] == "2017-01")
    assert Decimal(real["value"]) == pytest.approx(Decimal("109.090909"), abs=Decimal("0.000001"))


def test_rejects_unknown_schema(tmp_path: Path):
    source = tmp_path / "wages.csv"; source.write_text("periodo;otro\n1/1/2020;1\n", encoding="utf-8")
    with pytest.raises(PipelineError, match="esquema inesperado"):
        extract(artifact(source))
