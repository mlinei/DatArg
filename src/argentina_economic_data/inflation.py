from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import tempfile
import urllib.request
from urllib.parse import urlparse
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

import pandas as pd

IPC_URL = "https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv"
IPIM_URL = "https://www.indec.gob.ar/ftp/cuadros/economia/series_sipm_dic2015.xls"
OUTPUT_COLUMNS = [
    "series_id", "period", "frequency", "value", "unit", "status",
    "source_id", "source_url", "source_sha256", "retrieved_at",
]
IPC_CODES = {
    "0": "indec_ipc_general",
    "Núcleo": "indec_ipc_core",
    "Regulados": "indec_ipc_regulated",
    "Estacional": "indec_ipc_seasonal",
}


class PipelineError(RuntimeError):
    """Falla visible de descarga, esquema o calidad."""


@dataclass(frozen=True)
class Artifact:
    source_id: str
    url: str
    path: Path
    sha256: str
    size: int
    retrieved_at: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def acquire(source_id: str, url: str, raw_root: Path, local: Path | None = None) -> Artifact:
    retrieved = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    stamp = retrieved.replace(":", "").replace("-", "")
    suffix = Path(urlparse(url).path).suffix
    target_dir = raw_root / source_id / stamp
    target_dir.mkdir(parents=True, exist_ok=False)
    target = target_dir / f"source{suffix}"
    try:
        if local:
            shutil.copyfile(local, target)
        else:
            request = urllib.request.Request(url, headers={"User-Agent": "argentina-economic-data/0.2"})
            with urllib.request.urlopen(request, timeout=60) as response, target.open("wb") as output:
                content_type = response.headers.get_content_type()
                if content_type == "text/html":
                    raise PipelineError(f"{source_id}: INDEC devolvió HTML en lugar del recurso")
                shutil.copyfileobj(response, output)
    except Exception:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise
    size = target.stat().st_size
    if size < 100:
        raise PipelineError(f"{source_id}: archivo demasiado pequeño ({size} bytes)")
    artifact = Artifact(source_id, url, target, _sha256(target), size, retrieved)
    (target_dir / "manifest.json").write_text(
        json.dumps(artifact.__dict__ | {"path": target.name}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return artifact


def _decimal(value: object, field: str) -> Decimal | None:
    text = str(value).strip()
    if not text or text.upper() in {"NA", "NAN", "-"}:
        return None
    try:
        return Decimal(text.replace(".", "").replace(",", "."))
    except InvalidOperation as exc:
        raise PipelineError(f"valor inválido en {field}: {text!r}") from exc


def extract_ipc(artifact: Artifact) -> list[dict[str, str]]:
    required = {"Codigo", "Descripcion", "Clasificador", "Periodo", "Indice_IPC", "v_m_IPC", "v_i_a_IPC", "Region"}
    with artifact.path.open(encoding="latin-1", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        if set(reader.fieldnames or []) != required:
            raise PipelineError(f"IPC: esquema desconocido: {reader.fieldnames}")
        source = list(reader)
    if not source:
        raise PipelineError("IPC: fuente vacía")
    selected = [row for row in source if row["Region"] == "Nacional" and row["Codigo"] in IPC_CODES]
    periods = sorted({row["Periodo"] for row in selected})
    if not periods or periods[0] != "201612" or len(periods) < 13:
        raise PipelineError("IPC: cobertura nacional inesperada")
    keys = [(IPC_CODES[row["Codigo"]], row["Periodo"]) for row in selected]
    if len(keys) != len(set(keys)):
        raise PipelineError("IPC: claves duplicadas")
    expected = {(sid, period) for sid in IPC_CODES.values() for period in periods}
    if set(keys) != expected:
        raise PipelineError("IPC: panel incompleto para las cuatro categorías")

    result: list[dict[str, str]] = []
    by_series: dict[str, list[dict[str, str]]] = {}
    for row in selected:
        by_series.setdefault(IPC_CODES[row["Codigo"]], []).append(row)
    for series_id, rows in by_series.items():
        rows.sort(key=lambda row: row["Periodo"])
        previous: Decimal | None = None
        for row in rows:
            index = _decimal(row["Indice_IPC"], "Indice_IPC")
            monthly = _decimal(row["v_m_IPC"], "v_m_IPC")
            yoy = _decimal(row["v_i_a_IPC"], "v_i_a_IPC")
            if index is None or index <= 0:
                raise PipelineError("IPC: índice ausente o no positivo")
            if previous is not None and monthly is not None:
                calculated = (index / previous - 1) * 100
                if abs(calculated - monthly) > Decimal("0.16"):
                    raise PipelineError(f"IPC: variación mensual inconsistente en {series_id}/{row['Periodo']}")
            period = f"{row['Periodo'][:4]}-{row['Periodo'][4:]}"
            for suffix, value, unit in (
                ("index", index, "index_dec_2016_100"),
                ("mom", monthly, "percent_change"),
                ("yoy", yoy, "percent_change"),
            ):
                if value is not None:
                    result.append(_record(f"{series_id}_{suffix}", period, value, unit, artifact))
            previous = index
    return result


def extract_ipim(artifact: Artifact) -> list[dict[str, str]]:
    try:
        sheet = pd.read_excel(artifact.path, sheet_name="IPIM", header=None)
    except Exception as exc:
        raise PipelineError(f"IPIM: no se pudo leer la hoja esperada: {exc}") from exc
    if sheet.shape[0] < 8 or sheet.shape[1] < 14:
        raise PipelineError(f"IPIM: dimensiones inesperadas {sheet.shape}")
    codes = sheet.iloc[:, 0].astype(str).str.strip()
    matches = sheet.index[codes == "NG"].tolist()
    if len(matches) != 1:
        raise PipelineError(f"IPIM: se esperaba una fila NG y se encontraron {len(matches)}")
    row_index = matches[0]
    description = str(sheet.iat[row_index, 1]).strip().lower()
    if description != "nivel general":
        raise PipelineError(f"IPIM: descripción NG inesperada: {description!r}")

    years = sheet.iloc[3].ffill()
    months = sheet.iloc[4]
    result: list[dict[str, str]] = []
    previous: Decimal | None = None
    seen: set[str] = set()
    month_map = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
                 "jul": 7, "ago": 8, "sep": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12}
    for column in range(2, sheet.shape[1]):
        raw_year, raw_month = years.iat[column], months.iat[column]
        if pd.isna(raw_year) or pd.isna(raw_month) or pd.isna(sheet.iat[row_index, column]):
            continue
        try:
            year = int(float(raw_year))
        except (TypeError, ValueError):
            continue
        key = str(raw_month).strip().lower().rstrip(".*")[:3]
        if key not in month_map:
            raise PipelineError(f"IPIM: mes desconocido {raw_month!r}")
        period = f"{year:04d}-{month_map[key]:02d}"
        if period in seen:
            raise PipelineError(f"IPIM: período duplicado {period}")
        seen.add(period)
        index = Decimal(str(sheet.iat[row_index, column]))
        if index <= 0:
            raise PipelineError(f"IPIM: índice no positivo en {period}")
        result.append(_record("indec_ipim_general_index", period, index, "index_dec_2015_100", artifact))
        if previous is not None:
            change = (index / previous - 1) * 100
            result.append(_record("indec_ipim_general_mom", period, change, "percent_change", artifact, "calculated"))
        previous = index
    if not seen or min(seen) != "2015-12" or len(seen) < 13:
        raise PipelineError("IPIM: cobertura inesperada")
    return result


def _record(
    series_id: str, period: str, value: Decimal, unit: str, artifact: Artifact, status: str = "official"
) -> dict[str, str]:
    return {
        "series_id": series_id, "period": period, "frequency": "monthly",
        "value": format(value.quantize(Decimal("0.000001")), "f"), "unit": unit,
        "status": status, "source_id": artifact.source_id, "source_url": artifact.url,
        "source_sha256": artifact.sha256, "retrieved_at": artifact.retrieved_at,
    }


def _read_output(path: Path) -> dict[tuple[str, str], str]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        return {(row["series_id"], row["period"]): row["value"] for row in csv.DictReader(handle)}


def promote(records: Iterable[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    records = sorted(records, key=lambda row: (row["series_id"], row["period"]))
    if not records:
        raise PipelineError("no se promueve una salida vacía")
    processed = root / "data" / "processed"
    logs = root / "data" / "logs" / "inflation"
    processed.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    destination = processed / "inflation.csv"
    old = _read_output(destination)
    new = {(row["series_id"], row["period"]): row["value"] for row in records}
    diff = {
        "run_id": run_id,
        "created": len(new.keys() - old.keys()),
        "deleted": len(old.keys() - new.keys()),
        "modified": sum(old[key] != new[key] for key in old.keys() & new.keys()),
        "rows": len(records),
        "series": len({row["series_id"] for row in records}),
        "min_period": min(row["period"] for row in records),
        "max_period": max(row["period"] for row in records),
    }
    if old and diff["deleted"]:
        raise PipelineError(f"la nueva versión elimina {diff['deleted']} observaciones; no se promueve")
    fd, temporary = tempfile.mkstemp(prefix="inflation-", suffix=".csv", dir=processed)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader()
            writer.writerows(records)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    (logs / f"{run_id}.json").write_text(json.dumps(diff, indent=2) + "\n", encoding="utf-8")
    return diff


def run(root: Path, ipc_file: Path | None = None, ipim_file: Path | None = None) -> dict[str, object]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw = root / "data" / "raw"
    ipc = acquire("indec_ipc_divisiones_csv", IPC_URL, raw, ipc_file)
    ipim = acquire("indec_ipim", IPIM_URL, raw, ipim_file)
    records = extract_ipc(ipc) + extract_ipim(ipim)
    return promote(records, root, run_id)
