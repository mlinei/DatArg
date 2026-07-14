from __future__ import annotations

import csv,json,os,tempfile
from datetime import date,datetime,timezone
from decimal import Decimal
from pathlib import Path
from .inflation import OUTPUT_COLUMNS,Artifact,PipelineError,acquire

COUNTRY_RISK_URL="https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais"

def extract(a:Artifact):
    try:data=json.loads(a.path.read_text(encoding="utf-8"))
    except Exception as e:raise PipelineError(f"riesgo país: JSON inválido: {e}") from e
    if not isinstance(data,list) or len(data)<7000:raise PipelineError("riesgo país: cobertura insuficiente")
    out=[];seen=set();previous=None
    for row in data:
        if set(row)!={"fecha","valor"}:raise PipelineError("riesgo país: esquema inesperado")
        try:p=date.fromisoformat(row["fecha"]).isoformat();v=Decimal(str(row["valor"]))
        except Exception as e:raise PipelineError("riesgo país: observación inválida") from e
        if p in seen:raise PipelineError(f"riesgo país: fecha duplicada {p}")
        if previous and p<previous:raise PipelineError("riesgo país: fechas fuera de orden")
        if v<=0 or v>Decimal("20000"):raise PipelineError(f"riesgo país: valor fuera de rango en {p}")
        seen.add(p);previous=p
        out.append({"series_id":"argentinadatos_country_risk","period":p,"frequency":"daily","value":format(v.quantize(Decimal("0.000001")),"f"),"unit":"basis_points","status":"aggregated_index","source_id":a.source_id,"source_url":a.url,"source_sha256":a.sha256,"retrieved_at":a.retrieved_at})
    if out[0]["period"]!="1999-01-22":raise PipelineError(f"riesgo país: inicio inesperado {out[0]['period']}")
    return out
def _existing(p):
    if not p.exists():return {}
    with p.open(encoding="utf-8",newline="") as h:return {(r["series_id"],r["period"]):r["value"] for r in csv.DictReader(h)}
def promote(records,root,rid):
    records.sort(key=lambda r:r["period"]);td=root/"data"/"processed";ld=root/"data"/"logs"/"country_risk";td.mkdir(parents=True,exist_ok=True);ld.mkdir(parents=True,exist_ok=True);target=td/"country_risk.csv";old=_existing(target);new={(r["series_id"],r["period"]):r["value"] for r in records};report={"run_id":rid,"created":len(new.keys()-old.keys()),"deleted":len(old.keys()-new.keys()),"modified":sum(old[k]!=new[k] for k in old.keys()&new.keys()),"rows":len(records),"series":1,"min_period":records[0]["period"],"max_period":records[-1]["period"]}
    if old and report["deleted"]:raise PipelineError(f"riesgo país: la nueva versión elimina {report['deleted']} observaciones")
    fd,tmp=tempfile.mkstemp(prefix="country-risk-",suffix=".csv",dir=td)
    try:
        with os.fdopen(fd,"w",encoding="utf-8",newline="") as h:w=csv.DictWriter(h,fieldnames=OUTPUT_COLUMNS);w.writeheader();w.writerows(records);h.flush();os.fsync(h.fileno())
        os.replace(tmp,target)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    (ld/f"{rid}.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");return report
def run(root:Path,source_file:Path|None=None):
    rid=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ");a=acquire("argentinadatos_country_risk",COUNTRY_RISK_URL,root/"data"/"raw",source_file);return promote(extract(a),root,rid)
