from __future__ import annotations

import csv,json,os,re,tempfile,unicodedata
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
import pandas as pd
from .inflation import OUTPUT_COLUMNS,Artifact,PipelineError,acquire

INDUSTRY_URL="https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipi_manufacturero_2026.xls"
MONTHS={"enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,"julio":7,"agosto":8,"septiembre":9,"octubre":10,"noviembre":11,"diciembre":12}
DIVISIONS={"Nivel general":"total","15":"food_beverages","16":"tobacco","17":"textiles","18-19":"apparel_leather_footwear","20-22":"wood_paper_printing","23":"petroleum_refining","24":"chemicals","25":"rubber_plastic","26":"nonmetallic_minerals","27":"basic_metals","28":"metal_products","29":"machinery_equipment","30-33":"other_equipment_instruments","34":"motor_vehicles","35":"other_transport_equipment","36-38":"furniture_other_manufacturing"}

def _code(v:object)->str:
    if isinstance(v,float) and v.is_integer():return str(int(v))
    return str(v).strip()
def _record(s,p,v,u,a):
    return {"series_id":s,"period":p,"frequency":"monthly","value":format(v.quantize(Decimal("0.000001")),"f"),"unit":u,"status":"official","source_id":a.source_id,"source_url":a.url,"source_sha256":a.sha256,"retrieved_at":a.retrieved_at}
def _periods(d,start):
    year=None;out=[]
    for r in range(start,len(d)):
        if not pd.isna(d.iat[r,1]):
            m=re.search(r"20\d{2}",str(d.iat[r,1]));year=int(m.group()) if m else year
        month=unicodedata.normalize("NFKD",str(d.iat[r,2])).encode("ascii","ignore").decode().lower()
        if year and month in MONTHS:out.append((r,f"{year:04d}-{MONTHS[month]:02d}"))
    if len({p for _,p in out})!=len(out):raise PipelineError("industria: períodos duplicados")
    return out
def _columns(d):
    found={}
    for c in range(3,d.shape[1]):
        code=_code(d.iat[2,c]);desc=str(d.iat[3,c]).strip()
        if code=="Nivel general": key="Nivel general"
        else:key=code
        if key in DIVISIONS:found[key]=(c,desc)
    if set(found)!=set(DIVISIONS):raise PipelineError(f"industria: divisiones faltantes {set(DIVISIONS)-set(found)}")
    return found
def _table(d,metric,unit,a):
    cols=_columns(d); periods=_periods(d,6 if metric=="index" else 5);out=[];values={}
    for code,(c,_) in cols.items():
        sid=f"indec_industry_{DIVISIONS[code]}_{metric}";values[code]={}
        for r,p in periods:
            raw=d.iat[r,c]
            if isinstance(raw,str) and raw.strip()=="///":continue
            if pd.isna(raw):raise PipelineError(f"industria: valor ausente en {sid}/{p}")
            try:v=Decimal(str(raw))
            except Exception as e:raise PipelineError(f"industria: valor inválido en {sid}/{p}") from e
            if metric=="index" and v<=0:raise PipelineError(f"industria: índice no positivo en {sid}/{p}")
            values[code][p]=v;out.append(_record(sid,p,v,unit,a))
    return out,values
def extract(a:Artifact):
    try:
        idx=pd.read_excel(a.path,sheet_name="Cuadro 2",header=None);yoy=pd.read_excel(a.path,sheet_name="Cuadro 3",header=None);ytd=pd.read_excel(a.path,sheet_name="Cuadro 4",header=None)
    except Exception as e:raise PipelineError(f"industria: hojas históricas ausentes: {e}") from e
    ri,vi=_table(idx,"index","index_2004_100",a);ry,vy=_table(yoy,"yoy","percent_change",a);ra,va=_table(ytd,"ytd_yoy","percent_change",a)
    if min(vi["Nivel general"])!="2016-01" or max(vi["Nivel general"])!="2026-05":raise PipelineError("industria: cobertura inesperada")
    for code in DIVISIONS:
        for p,official in vy[code].items():
            year,month=p.split("-");prior=f"{int(year)-1:04d}-{month}";calc=(vi[code][p]/vi[code][prior]-1)*100
            if abs(calc-official)>Decimal("0.0001"):raise PipelineError(f"industria: interanual inconsistente en {code}/{p}")
        for p,official in va[code].items():
            year,month=map(int,p.split("-"));cur=sum(vi[code][f"{year:04d}-{m:02d}"] for m in range(1,month+1))/month;prev=sum(vi[code][f"{year-1:04d}-{m:02d}"] for m in range(1,month+1))/month;calc=(cur/prev-1)*100
            if abs(calc-official)>Decimal("0.0001"):raise PipelineError(f"industria: acumulada inconsistente en {code}/{p}")
    return ri+ry+ra
def _existing(p):
    if not p.exists():return {}
    with p.open(encoding="utf-8",newline="") as h:return {(r["series_id"],r["period"]):r["value"] for r in csv.DictReader(h)}
def promote(records,root,run_id):
    records.sort(key=lambda r:(r["series_id"],r["period"]));td=root/"data"/"processed";ld=root/"data"/"logs"/"industry";td.mkdir(parents=True,exist_ok=True);ld.mkdir(parents=True,exist_ok=True);target=td/"industry.csv";old=_existing(target);new={(r["series_id"],r["period"]):r["value"] for r in records};report={"run_id":run_id,"created":len(new.keys()-old.keys()),"deleted":len(old.keys()-new.keys()),"modified":sum(old[k]!=new[k] for k in old.keys()&new.keys()),"rows":len(records),"series":len({r["series_id"] for r in records}),"min_period":min(r["period"] for r in records),"max_period":max(r["period"] for r in records)}
    if old and report["deleted"]:raise PipelineError(f"industria: la nueva versión elimina {report['deleted']} observaciones")
    fd,tmp=tempfile.mkstemp(prefix="industry-",suffix=".csv",dir=td)
    try:
        with os.fdopen(fd,"w",encoding="utf-8",newline="") as h:w=csv.DictWriter(h,fieldnames=OUTPUT_COLUMNS);w.writeheader();w.writerows(records);h.flush();os.fsync(h.fileno())
        os.replace(tmp,target)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    (ld/f"{run_id}.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");return report
def run(root:Path,source_file:Path|None=None):
    rid=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ");a=acquire("indec_ipi_manufacturing",INDUSTRY_URL,root/"data"/"raw",source_file);return promote(extract(a),root,rid)
