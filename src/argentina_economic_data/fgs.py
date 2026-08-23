from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from .inflation import OUTPUT_COLUMNS, PipelineError

SOURCE_ARCHIVE = "https://www.anses.gob.ar/fgs-fondo-de-garantia-de-sustentabilidad/politica-de-transparencia/Informes-del-fgs"
SOURCE_2017 = "https://www.anses.gob.ar/sites/default/files/inline-files/FGS%20-%20IVQ%202017.pdf"
SOURCE_2023_Q1 = "https://www.anses.gob.ar/sites/default/files/inline-files/FGS%20-%20I.TRIM_.23.pdf"
SOURCE_2023 = "https://www.anses.gob.ar/sites/default/files/inline-files/Anuario_2023.pdf"
SOURCE_2024 = "https://www.anses.gob.ar/sites/default/files/archivo/2025-04/Consejo%20FGS%20-%20Febrero%202025.pdf"
SOURCE_2025 = "https://www.anses.gob.ar/sites/default/files/archivo/2026-03/Anuario-2025.pdf"

# Cierres nominales oficiales, en millones de pesos. El orden es:
# disponibilidades, títulos nacionales, otros títulos estatales, ON, plazo fijo,
# acciones, FCI, infraestructura, préstamos SIPA, otros préstamos, provincias y otros.
SNAPSHOTS = {
    2013: (9104, 205503, 2279, 7802, 15996, 27838, 7826, 44677, 2630, 0, 0, 5818, 329472, SOURCE_2017),
    2014: (5406, 306724, 2818, 9122, 11213, 52128, 12651, 59088, 6052, 0, 0, 7062, 472265, SOURCE_2017),
    2015: (12313, 415421, 3823, 9758, 8552, 85092, 17639, 85468, 15801, 0, 0, 10162, 664029, SOURCE_2017),
    2016: (7813, 519114, 5667, 10058, 50895, 117835, 22617, 94419, 16071, 0, 26842, 4050, 875380, SOURCE_2017),
    2017: (8602, 688717, 17425, 10361, 1531, 242287, 20397, 93775, 43132, 30614, 44330, 1408, 1202579, SOURCE_2017),
    2018: (14195, 1012157, 33466, 11949, 74877, 206312, 20131, 109969, 65078, 32108, 67614, 298, 1648154, SOURCE_2023_Q1),
    2019: (28745, 1542256, 71883, 19634, 26893, 264152, 24984, 88960, 123501, 75373, 120897, 504, 2387780, SOURCE_2023_Q1),
    2020: (13541, 2512970, 114471, 41556, 52287, 338488, 37834, 74246, 125606, 77124, 112426, 28, 3500577, SOURCE_2023_Q1),
    2021: (2745, 3840791, 157119, 51068, 48216, 578515, 59117, 158429, 160199, 70367, 126114, 2246, 5254924, SOURCE_2023_Q1),
    2022: (37185, 6946292, 338253, 87188, 39831, 1254726, 35767, 413526, 264622, 65724, 47656, 4201, 9534971, SOURCE_2023_Q1),
    2023: (93420, 28468004, 1453544, 287527, 156897, 5473607, 202324, 2551387, 1251827, 127826, 0, 17954, 40084317, SOURCE_2023),
    # En 2024 el informe denomina "Depósitos en bancos" al primer componente.
    2024: (526506, 56631411, 1591096, 320996, 135618, 13232491, 219311, 3274604, 868906, 79869, 0, 24128, 76904936, SOURCE_2024),
    2025: (449764, 80227432, 2205202, 286499, 696589, 17302232, 240724, 4240182, 430438, 36060, 0, 26662, 106141785, SOURCE_2025),
}

BUCKETS = {
    "public_securities": (1,),
    "other_public_assets": (2,),
    "shares": (5,),
    "infrastructure": (7,),
    "loans": (8, 9, 10),
    "private_fixed_income_liquidity": (3, 4, 6),
    "cash_other": (0, 11),
}


def _ccl_year_ends(root: Path) -> dict[int, tuple[Decimal, dict[str, str]]]:
    path = root / "data" / "processed" / "exchange_rates.csv"
    if not path.exists():
        raise PipelineError("FGS: falta data/processed/exchange_rates.csv")
    selected: dict[int, tuple[Decimal, dict[str, str]]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["series_id"] != "argentinadatos_usd_ccl_sell":
                continue
            year = int(row["period"][:4])
            if year not in SNAPSHOTS:
                continue
            if year not in selected or row["period"] > selected[year][1]["period"]:
                selected[year] = (Decimal(row["value"]), row)
    if set(selected) != set(SNAPSHOTS):
        raise PipelineError("FGS: la serie CCL no cubre todos los cierres desde 2013")
    return selected


def build_records(root: Path) -> list[dict[str, str]]:
    ccl = _ccl_year_ends(root)
    records: list[dict[str, str]] = []
    source_hash = hashlib.sha256(json.dumps(SNAPSHOTS, default=str, sort_keys=True).encode()).hexdigest()
    for year, snapshot in SNAPSHOTS.items():
        values = [Decimal(str(value)) for value in snapshot[:12]]
        total = Decimal(str(snapshot[12]))
        source_url = snapshot[13]
        if abs(sum(values) - total) > Decimal("2"):
            raise PipelineError(f"FGS: los componentes no concilian con el total en {year}")
        rate, fx_row = ccl[year]
        common = {
            "period": str(year), "frequency": "annual", "status": "calculated_from_official",
            "source_id": "anses_fgs_and_datarg_ccl", "source_url": source_url,
            "source_sha256": source_hash + ":" + fx_row["source_sha256"],
            "retrieved_at": fx_row["retrieved_at"],
        }
        records.append(common | {
            "series_id": "datarg_fgs_total_ccl_usd", "value": format((total / rate).quantize(Decimal("0.001")), "f"),
            "unit": "million_usd_ccl",
        })
        for bucket, indexes in BUCKETS.items():
            amount = sum(values[index] for index in indexes)
            records.append(common | {
                "series_id": f"datarg_fgs_{bucket}_ccl_usd",
                "value": format((amount / rate).quantize(Decimal("0.001")), "f"), "unit": "million_usd_ccl",
            })
            records.append(common | {
                "series_id": f"datarg_fgs_{bucket}_share",
                "value": format((amount / total * 100).quantize(Decimal("0.001")), "f"), "unit": "percent",
            })
    return sorted(records, key=lambda row: (row["series_id"], row["period"]))


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    target_dir = root / "data" / "processed"
    log_dir = root / "data" / "logs" / "fgs"
    target_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "fgs.csv"
    fd, temporary = tempfile.mkstemp(prefix="fgs-", suffix=".csv", dir=target_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader()
            writer.writerows(records)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    report = {"run_id": run_id, "rows": len(records), "series": len({r['series_id'] for r in records}), "min_period": "2013", "max_period": "2025"}
    (log_dir / f"{run_id}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def run(root: Path) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return promote(build_records(root), root, run_id)
