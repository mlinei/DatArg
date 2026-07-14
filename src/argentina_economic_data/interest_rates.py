from __future__ import annotations
import csv,json,os,tempfile
from datetime import date,datetime,timezone
from decimal import Decimal
from pathlib import Path
from .inflation import OUTPUT_COLUMNS,Artifact,PipelineError,acquire

BASE="https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias"
VARIABLES={7:("bcra_badlar_private_tna","1999-01-04","percent_nominal_annual"),35:("bcra_badlar_private_tea","2020-01-23","percent_effective_annual"),44:("bcra_tamar_private_tna","2024-10-01","percent_nominal_annual"),45:("bcra_tamar_private_tea","2024-10-01","percent_effective_annual")}
def extract(a:Artifact,var_id:int):
    try:d=json.loads(a.path.read_text(encoding="utf-8"));items=d["results"][0]["detalle"]
    except Exception as e:raise PipelineError(f"tasas BCRA {var_id}: esquema inválido: {e}") from e
    if d.get("status")!=200 or d["results"][0].get("idVariable")!=var_id or not items:raise PipelineError(f"tasas BCRA {var_id}: respuesta inesperada")
    sid,start,unit=VARIABLES[var_id];seen=set();out=[]
    for row in items:
        try:p=date.fromisoformat(row["fecha"]).isoformat();v=Decimal(str(row["valor"]))
        except Exception as e:raise PipelineError(f"tasas BCRA {var_id}: observación inválida") from e
        if p in seen:raise PipelineError(f"tasas BCRA {var_id}: fecha duplicada {p}")
        if v<0 or v>Decimal("1000"):raise PipelineError(f"tasas BCRA {var_id}: valor fuera de rango en {p}")
        seen.add(p);out.append({"series_id":sid,"period":p,"frequency":"daily","value":format(v.quantize(Decimal("0.000001")),"f"),"unit":unit,"status":"official","source_id":a.source_id,"source_url":a.url,"source_sha256":a.sha256,"retrieved_at":a.retrieved_at})
    out.sort(key=lambda r:r["period"])
    return out
def _existing(p):
    if not p.exists():return {}
    with p.open(encoding="utf-8",newline="") as h:return {(r["series_id"],r["period"]):r["value"] for r in csv.DictReader(h)}
def promote(records,root,rid):
    records.sort(key=lambda r:(r["series_id"],r["period"]));td=root/"data"/"processed";ld=root/"data"/"logs"/"interest_rates";td.mkdir(parents=True,exist_ok=True);ld.mkdir(parents=True,exist_ok=True);target=td/"interest_rates.csv";old=_existing(target);new={(r["series_id"],r["period"]):r["value"] for r in records};coverage={s:{"from":min(r["period"] for r in records if r["series_id"]==s),"through":max(r["period"] for r in records if r["series_id"]==s)} for s in sorted({r["series_id"] for r in records})};report={"run_id":rid,"created":len(new.keys()-old.keys()),"deleted":len(old.keys()-new.keys()),"modified":sum(old[k]!=new[k] for k in old.keys()&new.keys()),"rows":len(records),"series":len(coverage),"coverage":coverage}
    if old and report["deleted"]:raise PipelineError(f"tasas BCRA: la nueva versión elimina {report['deleted']} observaciones")
    fd,tmp=tempfile.mkstemp(prefix="interest-rates-",suffix=".csv",dir=td)
    try:
        with os.fdopen(fd,"w",encoding="utf-8",newline="") as h:w=csv.DictWriter(h,fieldnames=OUTPUT_COLUMNS);w.writeheader();w.writerows(records);h.flush();os.fsync(h.fileno())
        os.replace(tmp,target)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    (ld/f"{rid}.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");return report
def run(root:Path,files:dict[int,Path|None]|None=None):
    rid=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ");raw=root/"data"/"raw";files=files or {};records=[]
    for var_id in VARIABLES:
        if files.get(var_id):
            artifacts=[acquire(f"bcra_monetary_variable_{var_id}",f"{BASE}/{var_id}",raw,files[var_id])]
        else:
            artifacts=[];offset=0
            while True:
                a=acquire(f"bcra_monetary_variable_{var_id}_offset_{offset}",f"{BASE}/{var_id}?offset={offset}&limit=1000",raw)
                artifacts.append(a)
                payload=json.loads(a.path.read_text(encoding="utf-8"));count=payload["metadata"]["resultset"]["count"]
                offset+=1000
                if offset>=count:break
        variable_records=[]
        for a in artifacts:variable_records.extend(extract(a,var_id))
        variable_records.sort(key=lambda r:r["period"])
        expected_start=VARIABLES[var_id][1]
        if variable_records[0]["period"]!=expected_start:raise PipelineError(f"tasas BCRA {var_id}: inicio inesperado {variable_records[0]['period']}")
        if len({r["period"] for r in variable_records})!=len(variable_records):raise PipelineError(f"tasas BCRA {var_id}: páginas superpuestas")
        records.extend(variable_records)
    return promote(records,root,rid)
