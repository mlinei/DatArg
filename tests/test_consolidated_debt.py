from pathlib import Path

import pytest

from argentina_economic_data.consolidated_debt import extract
from argentina_economic_data.inflation import Artifact, PipelineError


TEXT = """
Deuda Bruta 465.353.130 76,3%
Fondo de garantía de sustentabilidad 68.456.800 11,2%
Depósitos del tesoro en el BCRA (ARS y USD) 11.690.555 1,9%
Adelantos transitorios 2.230.652 0,4%
Bonos y Letras instransf. del tesoro en manos del BCRA 103.840.678 17,0%
Pasivos remunerados del BCRA 14.025.208 2,3%
Reservas netas 4.439.143 0,7%
Deuda neta sector público 288.720.510 47,3%
"""


def artifact():
    return Artifact("test", "https://example.test/source.pdf", Path("x"), "a" * 64, 1000, "2025-01-01T00:00:00Z")


def test_extracts_and_validates_published_identity():
    rows = extract(artifact(), TEXT)
    values = {r["series_id"]: r["value"] for r in rows}
    assert values["estimated_net_consolidated_public_sector_debt"] == "288720.510000"
    assert values["estimated_net_consolidated_public_sector_debt_gdp"] == "47.300000"
    assert all(r["status"] == "estimated" for r in rows)


def test_rejects_inconsistent_total():
    with pytest.raises(PipelineError, match="identidad inconsistente"):
        extract(artifact(), TEXT.replace("288.720.510", "288.000.000"))
