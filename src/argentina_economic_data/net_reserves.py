from __future__ import annotations

import csv
import json
import os
import tempfile
from bisect import bisect_right
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd

from .inflation import OUTPUT_COLUMNS, Artifact, PipelineError, acquire

WEEKLY_URL = "https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/estados-resumidos-activos-pasivos-bcra-serie-anual-1998-actualidad.xls"
ECB_CNY_URL = "https://data-api.ecb.europa.eu/service/data/EXR/D.CNY.EUR.SP00.A?startPeriod=2023-12-01&format=csvdata"
ECB_USD_URL = "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?startPeriod=2023-12-01&format=csvdata"
FLOW_URL = "https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/81?desde=2023-12-01&limit=3000"
METHODOLOGY_URL = "https://www.bcra.gob.ar/normas-especiales-para-la-divulgacion-de-datos-fmi/"
START = "2023-12-01"


def _num(value: object) -> Decimal:
    if pd.isna(value):
        raise PipelineError("reservas netas: valor vacío")
    return Decimal(str(value))


def extract_weekly(artifact: Artifact) -> tuple[dict[str, Decimal], dict[str, Decimal]]:
    encajes: dict[str, Decimal] = {}; ooii: dict[str, Decimal] = {}
    try:
        book = pd.ExcelFile(artifact.path)
        sheets = [s for s in book.sheet_names if "semanal" in s.lower() and any(str(year) in s for year in range(2023, 2100))]
        for sheet in sheets:
            frame = pd.read_excel(artifact.path, sheet_name=sheet, header=None)
            labels = frame.iloc[:, 0].astype(str).str.lower()
            date_row = next(i for i in range(min(8, len(frame))) if sum(isinstance(v, (datetime, pd.Timestamp)) for v in frame.iloc[i, 1:]) >= 2)
            enc_hits = labels[labels.str.contains("cuentas corrientes en otras monedas", regex=False)].index
            if not len(enc_hits): continue
            enc_row = enc_hits[-1]
            ooii_row = labels[labels.str.contains("obligaciones con organismos internacionales", regex=False)].index[-1]
            fx_row = labels[labels.str.strip().eq("tipo de cambio")].index[-1]
            for col in range(1, frame.shape[1]):
                raw_date = frame.iat[date_row, col]
                if not isinstance(raw_date, (datetime, pd.Timestamp)): continue
                period = pd.Timestamp(raw_date).date().isoformat()
                if period < START: continue
                fx = _num(frame.iat[fx_row, col])
                encajes[period] = _num(frame.iat[enc_row, col]) / fx / Decimal(1000)
                ooii[period] = _num(frame.iat[ooii_row, col]) / fx / Decimal(1000)
    except Exception as exc:
        if isinstance(exc, PipelineError): raise
        raise PipelineError(f"reservas netas: balance semanal ilegible: {exc}") from exc
    if not encajes or encajes.keys() != ooii.keys(): raise PipelineError("reservas netas: serie semanal incompleta")
    return encajes, ooii


def extract_flow(artifact: Artifact) -> dict[str, Decimal]:
    try:
        payload = json.loads(artifact.path.read_text(encoding="utf-8")); result = payload["results"][0]
        rows = result["detalle"]
    except Exception as exc: raise PipelineError(f"reservas netas: flujo de encajes inválido: {exc}") from exc
    if result.get("idVariable") != 81: raise PipelineError("reservas netas: variable de encajes inesperada")
    return {r["fecha"]: Decimal(str(r["valor"])) for r in rows}


def extract_swap(cny: Artifact, usd: Artifact) -> dict[str, Decimal]:
    try:
        c = pd.read_csv(cny.path)[["TIME_PERIOD", "OBS_VALUE"]].rename(columns={"OBS_VALUE": "cny"})
        u = pd.read_csv(usd.path)[["TIME_PERIOD", "OBS_VALUE"]].rename(columns={"OBS_VALUE": "usd"})
        merged = c.merge(u, on="TIME_PERIOD")
    except Exception as exc: raise PipelineError(f"reservas netas: cotizaciones BCE inválidas: {exc}") from exc
    values = {str(r.TIME_PERIOD): Decimal(130000) / (Decimal(str(r.cny)) / Decimal(str(r.usd))) for r in merged.itertuples()}
    if not values: raise PipelineError("reservas netas: faltan cotizaciones del yuan")
    return values


def _latest(values: dict[str, Decimal], period: str) -> Decimal:
    keys = sorted(values); position = bisect_right(keys, period) - 1
    if position < 0: raise PipelineError(f"reservas netas: falta componente para {period}")
    return values[keys[position]]


def _encaje(period: str, anchors: dict[str, Decimal], flows: dict[str, Decimal]) -> Decimal:
    keys = sorted(anchors); position = bisect_right(keys, period) - 1
    if position < 0: return anchors[keys[0]]
    anchor = keys[position]
    return anchors[anchor] + sum((value for day, value in flows.items() if anchor < day <= period), Decimal(0))


def load_adjustments(path: Path) -> tuple[dict[str, Decimal], dict[str, dict[str, Decimal]]]:
    repos: dict[str, Decimal] = {}; overrides: dict[str, dict[str, Decimal]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            period = row["period"]; repos[period] = Decimal(row["repo_usd_million"])
            overrides[period] = {key: Decimal(row[key]) for key in ("gross_override", "encajes_override", "swap_override", "ooii_override") if row[key]}
    return repos, overrides


def calculate(gross: dict[str, Decimal], encajes: dict[str, Decimal], ooii: dict[str, Decimal], flows: dict[str, Decimal], swap: dict[str, Decimal], repos: dict[str, Decimal], overrides: dict[str, dict[str, Decimal]], artifact: Artifact) -> list[dict[str, str]]:
    gross = {**gross, **{p: v["gross_override"] for p, v in overrides.items() if "gross_override" in v}}
    rows: list[dict[str, str]] = []
    names = (("bcra_net_international_reserves", "net"), ("bcra_reserve_requirements_fx", "encajes"), ("bcra_china_swap", "swap"), ("bcra_international_organizations_liability", "ooii"), ("bcra_repos_up_to_one_year", "repo"))
    first_complete = max(START, min(encajes), min(ooii), min(swap), min(repos))
    for period in sorted(p for p in gross if p >= first_complete):
        override = overrides.get(period, {})
        components = {"gross": gross[period], "encajes": override.get("encajes_override", _encaje(period, encajes, flows)), "swap": override.get("swap_override", _latest(swap, period)), "ooii": override.get("ooii_override", _latest(ooii, period)), "repo": _latest(repos, period)}
        components["net"] = components["gross"] - components["encajes"] - components["swap"] - components["ooii"] - components["repo"]
        for series_id, key in names:
            rows.append({"series_id": series_id, "period": period, "frequency": "daily", "value": format(components[key].quantize(Decimal("0.000001")), "f"), "unit": "million_usd", "status": "calculated", "source_id": "datarg_bcra_net_reserves_reconstruction", "source_url": METHODOLOGY_URL, "source_sha256": artifact.sha256, "retrieved_at": artifact.retrieved_at})
    controls = {(r["period"], r["series_id"]): Decimal(r["value"]) for r in rows}
    for period, expected in (("2026-06-30", Decimal(4890)), ("2026-07-17", Decimal(10570))):
        actual = controls[(period, "bcra_net_international_reserves")]
        if actual != expected: raise PipelineError(f"reservas netas: control {period}={actual}, esperado {expected}")
    return rows


def promote(records: list[dict[str, str]], root: Path, run_id: str) -> dict[str, object]:
    target_dir=root/"data"/"processed"; log_dir=root/"data"/"logs"/"net_reserves"; target_dir.mkdir(parents=True,exist_ok=True); log_dir.mkdir(parents=True,exist_ok=True)
    target=target_dir/"net_reserves.csv"; fd,tmp=tempfile.mkstemp(prefix="net-reserves-",suffix=".csv",dir=target_dir)
    try:
        with os.fdopen(fd,"w",encoding="utf-8",newline="") as h:
            w=csv.DictWriter(h,fieldnames=OUTPUT_COLUMNS); w.writeheader(); w.writerows(records); h.flush(); os.fsync(h.fileno())
        os.replace(tmp,target)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
    net=[r for r in records if r["series_id"]=="bcra_net_international_reserves"]
    report={"run_id":run_id,"rows":len(records),"series":5,"min_period":net[0]["period"],"max_period":net[-1]["period"],"controls":{"2026-06-30":4890,"2026-07-17":10570}}
    (log_dir/f"{run_id}.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); return report


def run(root: Path, weekly_file: Path | None=None, flow_file: Path | None=None, cny_file: Path | None=None, usd_file: Path | None=None) -> dict[str, object]:
    run_id=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); raw=root/"data"/"raw"
    weekly=acquire("bcra_weekly_balance",WEEKLY_URL,raw,weekly_file); flow=acquire("bcra_reserve_requirement_flow",FLOW_URL,raw,flow_file); cny=acquire("ecb_cny_eur",ECB_CNY_URL,raw,cny_file); usd=acquire("ecb_usd_eur",ECB_USD_URL,raw,usd_file)
    gross={r["period"]:Decimal(r["value"]) for r in csv.DictReader((root/"data"/"processed"/"reserves.csv").open(encoding="utf-8"))}
    encajes,ooii=extract_weekly(weekly); repos,overrides=load_adjustments(root/"data"/"reference"/"net_reserves_adjustments.csv")
    return promote(calculate(gross,encajes,ooii,extract_flow(flow),extract_swap(cny,usd),repos,overrides,weekly),root,run_id)
