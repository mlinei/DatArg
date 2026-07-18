from __future__ import annotations

import csv
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from pypdf import PdfReader

from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, acquire


SOURCE_ID = "econosignal_consolidated_net_debt"
SOURCE_URL = "https://www.deloitte.com/content/dam/assets-zone4/latam/es/docs/services/financial-advisory/2025/diagnostico-macro-argentina-noviembre-2025-espanol.pdf"
PERIOD = "2025-Q2"
BENCHMARK_SOURCE_ID = "chequeado_debt_private_ooi_bcra_net_reserves"
BENCHMARK_SOURCE_URL = "https://chequeado.com/el-explicador/que-paso-con-la-deuda-en-cada-presidencia-los-datos-detras-de-la-pelea-entre-luis-caputo-y-julia-strada/"

# Etiqueta del PDF, identificador estable y signo en la identidad consolidada.
COMPONENTS = (
    ("Deuda Bruta", "gross_central_government_debt", 1),
    ("Fondo de garantía de sustentabilidad", "anses_sustainability_guarantee_fund", -1),
    ("Depósitos del tesoro en el BCRA", "treasury_deposits_at_bcra", -1),
    ("Adelantos transitorios", "bcra_temporary_advances_to_treasury", -1),
    ("Bonos y Letras instransf", "treasury_securities_held_by_bcra", -1),
    ("Pasivos remunerados del BCRA", "bcra_remunerated_liabilities", 1),
    ("Reservas netas", "bcra_net_reserves", -1),
)


def _number(text: str) -> Decimal:
    return Decimal(text.replace(".", "").replace(",", "."))


def extract_text(artifact: Artifact) -> str:
    try:
        return "\n".join(page.extract_text() or "" for page in PdfReader(artifact.path).pages)
    except Exception as exc:
        raise PipelineError(f"deuda consolidada: PDF ilegible: {exc}") from exc


def extract(artifact: Artifact, text: str | None = None) -> list[dict[str, str]]:
    text = text if text is not None else extract_text(artifact)
    values: dict[str, Decimal] = {}
    for label, component_id, _sign in COMPONENTS:
        match = re.search(re.escape(label) + r"[^\d]{0,100}([\d.]+(?:,\d+)?)\s+\d{1,3},\d+%", text, re.I | re.S)
        if not match:
            raise PipelineError(f"deuda consolidada: no se encontró {label!r}")
        values[component_id] = _number(match.group(1)) / Decimal("1000")

    net = sum(values[cid] * sign for _label, cid, sign in COMPONENTS)
    published = re.search(r"Deuda neta sector público\s+([\d.]+(?:,\d+)?)\s+([\d,]+)%", text, re.I)
    if not published:
        raise PipelineError("deuda consolidada: falta el total publicado")
    published_usd = _number(published.group(1)) / Decimal("1000")
    published_gdp = _number(published.group(2))
    if abs(net - published_usd) > Decimal("0.01"):
        raise PipelineError(f"deuda consolidada: identidad inconsistente ({net} != {published_usd})")

    rows: list[dict[str, str]] = []
    for _label, cid, _sign in COMPONENTS:
        rows.append(_record(f"estimated_consolidated_debt_{cid}", values[cid], "million_usd", artifact))
    rows.extend((
        _record("estimated_net_consolidated_public_sector_debt", published_usd, "million_usd", artifact),
        _record("estimated_net_consolidated_public_sector_debt_gdp", published_gdp, "percent_of_gdp", artifact),
    ))
    return rows


def _record(series_id: str, value: Decimal, unit: str, artifact: Artifact) -> dict[str, str]:
    return {
        "series_id": series_id, "period": PERIOD, "frequency": "quarterly",
        "value": format(value.quantize(Decimal("0.000001")), "f"), "unit": unit,
        "status": "estimated", "source_id": artifact.source_id, "source_url": artifact.url,
        "source_sha256": artifact.sha256, "retrieved_at": artifact.retrieved_at,
    }


def calculate_benchmark_series(path: Path, artifact: Artifact) -> list[dict[str, str]]:
    rows = []
    with path.open(encoding="utf-8", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    for source in source_rows:
        private_ooi = Decimal(source["gross_private_and_ooi_million_usd"])
        reserves = Decimal(source["net_reserves_million_usd"])
        bcra = Decimal(source["bcra_liabilities_million_usd"])
        gross = Decimal(source["gross_total_million_usd"])
        gross_gdp = Decimal(source["gross_debt_percent_gdp"])
        published = Decimal(source["published_net_debt_million_usd"])
        calculated = private_ooi + bcra - reserves
        if abs(calculated - published) > Decimal("0.000001"):
            raise PipelineError(f"deuda consolidada comparable: identidad inconsistente en {source['period']}")
        implied_gdp = gross / (gross_gdp / Decimal(100))
        ratio = calculated / implied_gdp * Decimal(100)
        frequency = "quarterly" if "Q" in source["period"] else "monthly"
        for series_id, value, unit in (
            ("estimated_comparable_net_public_debt", calculated, "million_usd"),
            ("estimated_comparable_net_public_debt_gdp", ratio, "percent_of_gdp"),
        ):
            record = _record(series_id, value, unit, artifact)
            record.update({
                "period": source["period"], "frequency": frequency,
                "source_id": BENCHMARK_SOURCE_ID, "source_url": BENCHMARK_SOURCE_URL,
            })
            rows.append(record)
    if len(source_rows) != 6 or source_rows[0]["period"] != "2003-Q2" or source_rows[-1]["period"] != "2026-05":
        raise PipelineError("deuda consolidada comparable: cobertura de referencia inesperada")
    return rows


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    records.sort(key=lambda row: (row["series_id"], row["period"]))
    target_dir = root / "data" / "processed"
    log_dir = root / "data" / "logs" / "consolidated_debt"
    target_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "consolidated_debt.csv"
    old = {}
    if target.exists():
        with target.open(encoding="utf-8", newline="") as handle:
            old = {(r["series_id"], r["period"]): r["value"] for r in csv.DictReader(handle)}
    new = {(r["series_id"], r["period"]): r["value"] for r in records}
    report = {
        "run_id": run_id, "rows": len(records), "series": len({r["series_id"] for r in records}),
        "coverage": {"from": min(r["period"] for r in records), "through": max(r["period"] for r in records)},
        "created": len(new.keys() - old.keys()), "deleted": len(old.keys() - new.keys()),
        "modified": sum(old[k] != new[k] for k in old.keys() & new.keys()),
        "methodology_version": "econosignal_psds_2025q2_v1",
    }
    if old and report["deleted"]:
        raise PipelineError("deuda consolidada: la nueva versión elimina observaciones")
    fd, tmp = tempfile.mkstemp(prefix="consolidated-debt-", suffix=".csv", dir=target_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader(); writer.writerows(records); handle.flush(); os.fsync(handle.fileno())
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
    (log_dir / f"{run_id}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def run(root: Path, source_file: Path | None = None) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifact = acquire(SOURCE_ID, SOURCE_URL, root / "data" / "raw", source_file)
    benchmarks = calculate_benchmark_series(root / "data" / "reference" / "consolidated_debt_benchmarks.csv", artifact)
    return promote(extract(artifact) + benchmarks, root, run_id)
