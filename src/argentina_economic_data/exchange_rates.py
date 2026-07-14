from __future__ import annotations

import csv,json,os,tempfile
from datetime import datetime,timezone,date
from decimal import Decimal
from pathlib import Path
from .inflation import OUTPUT_COLUMNS,Artifact,PipelineError,acquire

BASE_URL="https://api.argentinadatos.com/v1/cotizaciones/dolares"
MARKETS={"oficial":"official_retail","blue":"blue","bolsa":"mep","contadoconliqui":"ccl"}

def _record(s,p,v,a):
    return {"series_id":s,"period":p,"frequency":"daily","value":format(v.quantize(Decimal("0.000001")),"f"),"unit":"ars_per_usd","status":"aggregated_quote","source_id":a.source_id,"source_url":a.url,"source_sha256":a.sha256,"retrieved_at":a.retrieved_at}
def extract(a:Artifact,house:str):
    try:data=json.loads(a.path.read_text(encoding="utf-8"))
    except Exception as e:raise PipelineError(f"tipo de cambio {house}: JSON inválido: {e}") from e
    if not isinstance(data,list) or not data:raise PipelineError(f"tipo de cambio {house}: respuesta vacía")
    out=[];seen=set();first=None;last=None
    for row in data:
        if set(row)!={"casa","compra","venta","fecha"} or row["casa"]!=house:raise PipelineError(f"tipo de cambio {house}: esquema inesperado")
        try:p=date.fromisoformat(row["fecha"]).isoformat();buy=Decimal(str(row["compra"]));sell=Decimal(str(row["venta"]))
        except Exception as e:raise PipelineError(f"tipo de cambio {house}: observación inválida") from e
        if p in seen:raise PipelineError(f"tipo de cambio {house}: fecha duplicada {p}")
        if buy<=0 or sell<=0:raise PipelineError(f"tipo de cambio {house}: precios no positivos en {p}")
        seen.add(p);first=p if first is None else first;last=p
        prefix=f"argentinadatos_usd_{MARKETS[house]}";out.append(_record(prefix+"_sell",p,sell,a))
    expected_start={"oficial":"2011-01-03","blue":"2011-01-03","bolsa":"2018-10-29","contadoconliqui":"2013-01-02"}[house]
    if first!=expected_start or last is None or len(seen)<2500:raise PipelineError(f"tipo de cambio {house}: cobertura inesperada {first}–{last}")
    return out
def _existing(p):
    if not p.exists():return {}
    with p.open(encoding="utf-8",newline="") as h:return {(r["series_id"],r["period"]):r["value"] for r in csv.DictReader(h)}
def promote(records,root,rid):
    records.sort(key=lambda r:(r["series_id"],r["period"]));td=root/"data"/"processed";ld=root/"data"/"logs"/"exchange_rates";td.mkdir(parents=True,exist_ok=True);ld.mkdir(parents=True,exist_ok=True);target=td/"exchange_rates.csv";old=_existing(target);new={(r["series_id"],r["period"]):r["value"] for r in records};coverage={s:{"from":min(r["period"] for r in records if r["series_id"]==s),"through":max(r["period"] for r in records if r["series_id"]==s)} for s in sorted({r["series_id"] for r in records})};report={"run_id":rid,"created":len(new.keys()-old.keys()),"deleted":len(old.keys()-new.keys()),"modified":sum(old[k]!=new[k] for k in old.keys()&new.keys()),"rows":len(records),"series":len(coverage),"coverage":coverage}
    if old and report["deleted"]:raise PipelineError(f"tipo de cambio: la nueva versión elimina {report['deleted']} observaciones")
    fd,tmp=tempfile.mkstemp(prefix="exchange-rates-",suffix=".csv",dir=td)
    try:
        with os.fdopen(fd,"w",encoding="utf-8",newline="") as h:w=csv.DictWriter(h,fieldnames=OUTPUT_COLUMNS);w.writeheader();w.writerows(records);h.flush();os.fsync(h.fileno())
        os.replace(tmp,target)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    (ld/f"{rid}.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");return report
def run(root:Path,files:dict[str,Path|None]|None=None):
    rid=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ");raw=root/"data"/"raw";records=[];files=files or {}
    for house in MARKETS:
        a=acquire(f"argentinadatos_usd_{house}",f"{BASE_URL}/{house}",raw,files.get(house));records.extend(extract(a,house))
    return promote(records,root,rid)
