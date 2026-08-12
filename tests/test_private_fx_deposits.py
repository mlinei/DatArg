import json
from pathlib import Path

import pytest

from argentina_economic_data.inflation import Artifact, PipelineError
from argentina_economic_data.private_fx_deposits import aggregate_monthly, extract


def artifact(tmp_path: Path, variable_id: int = 108) -> Artifact:
    path = tmp_path / "source.json"
    path.write_text(json.dumps({
        "status": 200,
        "results": [{"idVariable": variable_id, "detalle": [
            {"fecha": "2026-01-30", "valor": 38000},
            {"fecha": "2026-01-02", "valor": 37000},
            {"fecha": "2026-02-03", "valor": 39000},
        ]}],
    }), encoding="utf-8")
    return Artifact("test", "https://example.test", path, "h", 100, "t")


def test_monthly_balance_uses_last_daily_observation(tmp_path: Path):
    rows = aggregate_monthly(extract(artifact(tmp_path)))
    assert [(row["period"], row["value"]) for row in rows] == [
        ("2026-01", "38000.000000"),
        ("2026-02", "39000.000000"),
    ]
    assert all(row["frequency"] == "monthly" for row in rows)
    assert all(row["unit"] == "million_usd" for row in rows)


def test_rejects_wrong_variable(tmp_path: Path):
    with pytest.raises(PipelineError, match="respuesta inesperada"):
        extract(artifact(tmp_path, 109))
