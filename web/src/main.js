import './styles.css';
import { sections, COLORS } from './config.js';
import { loadDataset } from './data-client.js';
import { setupPWA } from './pwa.js';
import { setupNotifications } from './notifications.js';

const state = new Map();
const visibility = new Map();
function human(value, unit) {
  const n = Number(value); if (!Number.isFinite(n)) return '—';
  if (unit === '%' || unit === '% TNA') return `${n.toLocaleString('es-AR',{maximumFractionDigits:1})}%`;
  if (unit === 'pb') return `${Math.round(n).toLocaleString('es-AR')} pb`;
  if (unit === 'ARS/USD') return `$ ${n.toLocaleString('es-AR',{maximumFractionDigits:2})}`;
  if (unit === 'USD M') return `USD ${n.toLocaleString('es-AR',{maximumFractionDigits:0})} M`;
  return n.toLocaleString('es-AR',{maximumFractionDigits:1});
}
function sourceName(row) {
  const id = row?.source_id || '';
  if (id.startsWith('datarg_bcra_credit_')) return 'DatArg sobre BCRA e INDEC';
  if (id.startsWith('indec_')) return 'INDEC';
  if (id.startsWith('bcra_')) return 'BCRA';
  if (id.startsWith('datarg_bcra_')) return 'DatArg sobre fuentes BCRA, FMI y BCE';
  if (id.startsWith('datarg_mecon_')) return 'DatArg sobre Ministerio de Economía e INDEC';
  if (id.startsWith('jgm_')) return 'Jefatura de Gabinete / DNIP';
  if (id.startsWith('mecon_')) return 'Ministerio de Economía';
  if (id.startsWith('argentinadatos_')) return 'ArgentinaDatos';
  if (id.startsWith('yahoo_')) return 'Yahoo Finance / ArgentinaDatos';
  if (id.startsWith('econosignal_')) return 'Econosignal / Deloitte';
  return id || 'Fuente de datos';
}
function periodDate(p) {
  if (/^\d{4}$/.test(p)) return new Date(`${p}-12-31T00:00:00Z`);
  if (/^\d{4}-Q\d$/.test(p)) return new Date(Date.UTC(+p.slice(0,4), (+p.at(-1))*3-1, 1));
  if (/^\d{4}-S\d$/.test(p)) return new Date(Date.UTC(+p.slice(0,4), p.endsWith('1')?5:11, 1));
  if (/^\d{4}-\d{2}$/.test(p)) return new Date(`${p}-01T00:00:00Z`);
  return new Date(`${p}T00:00:00Z`);
}
function precisePeriodLabel(period) {
  if (/^\d{4}$/.test(period)) return period;
  if (/^\d{4}-Q\d$/.test(period)) return `T${period.at(-1)} ${period.slice(0,4)}`;
  if (/^\d{4}-S\d$/.test(period)) return `S${period.at(-1)} ${period.slice(0,4)}`;
  if (/^\d{4}-\d{2}$/.test(period)) return `${period.slice(5)}/${period.slice(0,4)}`;
  if (/^\d{4}-\d{2}-\d{2}$/.test(period)) return period.split('-').reverse().join('/');
  return period;
}
function chartSeries(chart) {
  if (chart.composite) {
    const current = state.get(chart) || { sector: chart.composite.defaultSector, metric: chart.composite.defaultMetric };
    const pattern = chart.composite.seriesPattern || 'indec_industry_{sector}_{metric}';
    return { [pattern.replace('{sector}', current.sector).replace('{metric}', current.metric)]: chart.composite.sectors[current.sector] };
  }
  if (chart.selector) { const selected = state.get(chart) || chart.selected || Object.keys(chart.selector)[0]; return {[selected]: chart.selector[selected]}; }
  if (chart.regionSelector) {
    const region = state.get(chart) || chart.region;
    const prefix = chart.metrics.poverty ? 'indec_' : 'indec_labor_';
    return Object.fromEntries(Object.entries(chart.metrics).map(([metric,label]) => [`${prefix}${metric}${chart.metrics.poverty?'_persons':''}_${region}`,label]));
  }
  if (chart.metricToggle) {
    const metric = state.get(chart) || chart.metricToggle.default;
    if (chart.metricToggle.seriesByMetric) return chart.metricToggle.seriesByMetric[metric];
    return Object.fromEntries(Object.entries(chart.series).map(([id, label]) => [id.replace('{metric}', metric), label]));
  }
  return chart.series;
}
function filterRange(points, range, from, to) {
  if (from || to) {
    const min = from ? Number(from) : -Infinity;
    const max = to ? Number(to) : Infinity;
    return points.filter(p => p.date >= min && p.date <= max);
  }
  if (range === 'ALL' || !points.length) return points;
  const max = Math.max(...points.map(p=>p.date)); const years = range === '1Y' ? 1 : range === '5Y' ? 5 : 10;
  return points.filter(p => p.date >= max - years*365.25*864e5);
}
function buildTableModel(points, selectedSeries, colorFor) {
  const byPeriod = new Map();
  points.forEach(point => {
    if (!byPeriod.has(point.period)) byPeriod.set(point.period, new Map());
    byPeriod.get(point.period).set(point.series_id, point);
  });
  const periods = [...byPeriod.keys()].sort((a,b) => +periodDate(b) - +periodDate(a));
  return { byPeriod, periods, series: Object.entries(selectedSeries).map(([id,label])=>[id,label,colorFor(id)]) };
}
function tableHTML(model, unit, limit) {
  const shown = model.periods.slice(0, limit);
  const remaining = model.periods.length - shown.length;
  return `<div class="table-view"><div class="table-toolbar"><span>Mostrando ${shown.length.toLocaleString('es-AR')} de ${model.periods.length.toLocaleString('es-AR')} períodos</span><button class="table-download" type="button">Descargar CSV ↓</button></div><div class="data-table-scroll"><table><thead><tr><th>Período</th>${model.series.map(([id,label,color])=>`<th><i style="background:${color}"></i>${label}</th>`).join('')}</tr></thead><tbody>${shown.map(period=>`<tr><th scope="row">${period}</th>${model.series.map(([id])=>{const point=model.byPeriod.get(period).get(id);return `<td>${point?human(point.value,unit):'—'}</td>`}).join('')}</tr>`).join('')}</tbody></table></div>${remaining>0?`<button class="table-more" type="button">Mostrar ${Math.min(100,remaining).toLocaleString('es-AR')} períodos más</button>`:''}</div>`;
}
function downloadTableCSV(model, title) {
  const escape = value => `"${String(value ?? '').replaceAll('"','""')}"`;
  const records = [['Período', ...model.series.map(([,label])=>label)], ...model.periods.map(period=>[period, ...model.series.map(([id])=>model.byPeriod.get(period).get(id)?.rawValue ?? '')])];
  const csv = `\uFEFF${records.map(record=>record.map(escape).join(',')).join('\r\n')}`;
  const link = document.createElement('a');
  link.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  link.download = `${title.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/(^-|-$)/g,'')}.csv`;
  document.body.append(link); link.click(); link.remove(); setTimeout(()=>URL.revokeObjectURL(link.href),1000);
}
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, character => ({
  '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
})[character]);
const maturityCategories = {
  loans: { label: 'Préstamos', color: '#59a7ff' },
  bcra_advances: { label: 'Adelantos BCRA', color: '#47d4f5' },
  securities: { label: 'Títulos y Letras', color: '#8b83ff' },
};
function downloadMaturityCSV(rows, title) {
  const escape = value => `"${String(value ?? '').replaceAll('"','""')}"`;
  const records = [
    ['Fecha de corte','Período','Servicio','Grupo','Renglón oficial','Millones de USD'],
    ...rows.map(row=>[row.snapshot_date,row.period,row.service_type==='capital'?'Capital':'Intereses',maturityCategories[row.category]?.label||row.category,row.instrument,row.value])
  ];
  const link=document.createElement('a');
  link.href=URL.createObjectURL(new Blob([`\uFEFF${records.map(record=>record.map(escape).join(',')).join('\r\n')}`],{type:'text/csv;charset=utf-8'}));
  link.download=`${title}.csv`;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(link.href),1000);
}
function renderMaturityChart(container, rows, chart) {
  const snapshots=[...new Set(rows.map(row=>row.snapshot_date))].sort();
  const snapshot=container.dataset.snapshot||snapshots.at(-1);
  const service=container.dataset.service||'total';
  const view=container.dataset.view||'chart';
  const snapshotRows=rows.filter(row=>row.snapshot_date===snapshot);
  const periods=[...new Set(snapshotRows.map(row=>row.period))].sort();
  const detailPeriod=container.dataset.detailPeriod||periods.find(period=>period>=new Date().toISOString().slice(0,7))||periods[0];
  const categories=Object.keys(maturityCategories);
  const categoryRows=snapshotRows.filter(row=>row.detail_level==='category'&&(service==='total'||row.service_type===service));
  const values=new Map();
  categoryRows.forEach(row=>{
    const key=`${row.period}\0${row.category}`;
    values.set(key,(values.get(key)||0)+Number(row.value));
  });
  const totals=periods.map(period=>({
    period,
    categories:Object.fromEntries(categories.map(category=>[category,values.get(`${period}\0${category}`)||0])),
  })).map(row=>({...row,total:Object.values(row.categories).reduce((sum,value)=>sum+value,0)}));
  const next=totals.find(row=>row.period>=new Date().toISOString().slice(0,7))||totals[0];
  const detailRows=snapshotRows.filter(row=>row.period===detailPeriod&&row.detail_level==='detail'&&Number(row.value)>0&&(service==='total'||row.service_type===service))
    .sort((a,b)=>Number(b.value)-Number(a.value));
  const W=900,H=390,L=94,R=22,T=25,B=70;
  const max=Math.max(...totals.map(row=>row.total),1)*1.12;
  const x=index=>L+index*(W-L-R)/totals.length;
  const barWidth=Math.max(10,(W-L-R)/totals.length*.72);
  const y=value=>T+(max-value)/max*(H-T-B);
  const ticks=Array.from({length:5},(_,index)=>max*index/4);
  let bars='';
  totals.forEach((row,index)=>{
    let bottom=0;
    categories.forEach(category=>{
      const value=row.categories[category];
      if(value<=0)return;
      const top=bottom+value;
      bars+=`<rect class="maturity-bar" data-period="${row.period}" x="${x(index).toFixed(1)}" y="${y(top).toFixed(1)}" width="${barWidth.toFixed(1)}" height="${Math.max(1,y(bottom)-y(top)).toFixed(1)}" fill="${maturityCategories[category].color}"/>`;
      bottom=top;
    });
  });
  const serviceOptions={total:'Capital + intereses',capital:'Capital',interest:'Intereses'};
  const snapshotLabel=value=>value.split('-').reverse().join('/');
  const selectors=`<div class="chart-selectors"><label>Servicio<select class="maturity-service">${Object.entries(serviceOptions).map(([key,label])=>`<option value="${key}" ${service===key?'selected':''}>${label}</option>`).join('')}</select></label><label>Informe al<select class="maturity-snapshot">${snapshots.map(value=>`<option value="${value}" ${snapshot===value?'selected':''}>${snapshotLabel(value)}</option>`).join('')}</select></label></div>`;
  const viewControls=`<div class="view-toggle" role="group"><button data-view="chart" class="${view==='chart'?'active':''}">Gráfico</button><button data-view="table" class="${view==='table'?'active':''}">Instrumentos</button></div>`;
  const visual=view==='chart'?`<div class="chart-wrap maturity-chart"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${chart.title}">
    ${ticks.map(value=>`<line x1="${L}" x2="${W-R}" y1="${y(value)}" y2="${y(value)}"/><text x="${L-10}" y="${y(value)+4}" text-anchor="end">${Math.round(value).toLocaleString('es-AR')}</text>`).join('')}
    ${bars}
    ${totals.map((row,index)=>index%3===0||index===totals.length-1?`<text x="${x(index)+barWidth/2}" y="${H-18}" text-anchor="middle">${row.period.slice(5)}/${row.period.slice(2,4)}</text>`:'').join('')}
  </svg><div class="tooltip"></div></div>`:`<div class="maturity-table-controls"><label>Mes<select class="maturity-period">${periods.map(period=>`<option value="${period}" ${period===detailPeriod?'selected':''}>${period}</option>`).join('')}</select></label><button class="maturity-download">Descargar CSV ↓</button></div>
  <div class="data-table-scroll maturity-table"><table><thead><tr><th>Tipo</th><th>Grupo</th><th>Renglón oficial</th><th>USD M</th></tr></thead><tbody>${detailRows.map(row=>`<tr><td>${row.service_type==='capital'?'Capital':'Intereses'}</td><td>${maturityCategories[row.category]?.label||'—'}</td><td>${escapeHTML(row.instrument)}</td><td>${Number(row.value).toLocaleString('es-AR',{maximumFractionDigits:1})}</td></tr>`).join('')}</tbody></table></div><p class="maturity-note">La apertura reproduce los renglones del informe oficial; algunos son subtotales jerárquicos y no deben sumarse entre sí.</p>`;
  const source=snapshotRows[0];
  container.innerHTML=`<div class="chart-head"><div><h3>${chart.title}</h3><p>${chart.subtitle}</p></div><div class="chart-actions">${selectors}${viewControls}</div></div>
    <div class="latest-row maturity-summary"><div><i style="background:#59a7ff"></i><span>${next.period}</span><strong>${human(next.total,'USD M')}</strong><small>Próximo mes del cronograma</small></div><div class="maturity-cutoff"><span>Fecha de corte</span><strong>${snapshotLabel(snapshot)}</strong><small>Stock y tipo de cambio del informe</small></div></div>
    ${visual}
    <div class="chart-foot"><div class="legend">${categories.map(category=>`<span><i style="background:${maturityCategories[category].color}"></i>${maturityCategories[category].label}</span>`).join('')}</div></div>
    <div class="source-citation"><span>Fuente:</span><a href="${source.source_url}" target="_blank" rel="noreferrer">Ministerio de Economía ↗</a></div>`;
  container.querySelector('.maturity-service').onchange=event=>{container.dataset.service=event.target.value;renderMaturityChart(container,rows,chart)};
  container.querySelector('.maturity-snapshot').onchange=event=>{container.dataset.snapshot=event.target.value;delete container.dataset.detailPeriod;renderMaturityChart(container,rows,chart)};
  container.querySelectorAll('[data-view]').forEach(button=>button.onclick=()=>{container.dataset.view=button.dataset.view;renderMaturityChart(container,rows,chart)});
  const periodSelect=container.querySelector('.maturity-period');if(periodSelect)periodSelect.onchange=event=>{container.dataset.detailPeriod=event.target.value;renderMaturityChart(container,rows,chart)};
  const download=container.querySelector('.maturity-download');if(download)download.onclick=()=>downloadMaturityCSV(detailRows,'vencimientos-tesoro');
  const svg=container.querySelector('svg'),tip=container.querySelector('.tooltip');
  if(svg)svg.onpointermove=event=>{const target=event.target.closest('.maturity-bar');if(!target){tip.style.opacity=0;return}const row=totals.find(item=>item.period===target.dataset.period);tip.innerHTML=`<b>${row.period}</b>${categories.map(category=>`<span>${maturityCategories[category].label}: ${human(row.categories[category],'USD M')}</span>`).join('')}<strong>Total: ${human(row.total,'USD M')}</strong>`;tip.style.opacity=1;tip.style.left=`${Math.min(78,Math.max(8,event.offsetX/svg.clientWidth*100))}%`};
  if(svg)svg.onpointerleave=()=>{tip.style.opacity=0};
}

function interpolateYield(rows, days) {
  const sorted=[...rows].sort((a,b)=>+a.days_to_maturity-+b.days_to_maturity);
  if(!sorted.length||days<+sorted[0].days_to_maturity||days>+sorted.at(-1).days_to_maturity)return null;
  const exact=sorted.find(row=>+row.days_to_maturity===days);if(exact)return +exact.annual_yield;
  const upperIndex=sorted.findIndex(row=>+row.days_to_maturity>days);const lower=sorted[upperIndex-1],upper=sorted[upperIndex];
  return +lower.annual_yield+(+upper.annual_yield-+lower.annual_yield)*(days-+lower.days_to_maturity)/(+upper.days_to_maturity-+lower.days_to_maturity);
}
function renderYieldCurves(container, rows, chart) {
  if(!rows.length){container.innerHTML=`<div class="chart-head"><div><h3>${chart.title}</h3><p>${chart.subtitle}</p></div></div><div class="yield-pending"><strong>Sin cierre disponible</strong><p>Las fuentes públicas todavía no devolvieron instrumentos válidos para construir la curva.</p></div><div class="source-citation"><span>Fuentes:</span><a href="https://api.argentinadatos.com/v1/finanzas/letras" target="_blank" rel="noreferrer">ArgentinaDatos ↗</a></div>`;return}
  const mode=container.dataset.curve||'nominal',view=container.dataset.view||'chart';
  const nominalSnapshots=[...new Set(rows.filter(row=>row.curve_type==='nominal').map(row=>row.snapshot_date))];
  const cerSnapshots=[...new Set(rows.filter(row=>row.curve_type==='cer').map(row=>row.snapshot_date))];
  const snapshots=(mode==='nominal'?nominalSnapshots:mode==='cer'?cerSnapshots:nominalSnapshots.filter(value=>cerSnapshots.includes(value))).sort();
  const requestedSnapshot=container.dataset.snapshot;const snapshot=snapshots.includes(requestedSnapshot)?requestedSnapshot:snapshots.at(-1);
  const snapshotRows=snapshot?rows.filter(row=>row.snapshot_date===snapshot):[];
  const nominal=snapshotRows.filter(row=>row.curve_type==='nominal').sort((a,b)=>+a.days_to_maturity-+b.days_to_maturity);
  const cer=snapshotRows.filter(row=>row.curve_type==='cer').sort((a,b)=>+a.days_to_maturity-+b.days_to_maturity);
  const curveRows=mode==='breakeven'?nominal.map(row=>{const real=interpolateYield(cer,+row.days_to_maturity);return real===null?null:{...row,raw_nominal_yield:+row.annual_yield,real_yield:real,annual_yield:((1+ +row.annual_yield/100)/(1+real/100)-1)*100}}).filter(Boolean):(mode==='cer'?cer:nominal);
  const modeLabels={nominal:'Curva nominal (LECAP/BONCAP)',cer:'Curva CER',breakeven:'Inflación breakeven'};
  const selectors=`<div class="chart-selectors"><label>Vista<select class="yield-mode">${Object.entries(modeLabels).map(([key,label])=>`<option value="${key}" ${key===mode?'selected':''}>${label}</option>`).join('')}</select></label><label>Cierre<select class="yield-snapshot" ${snapshots.length?'':'disabled'}>${snapshots.map(value=>`<option value="${value}" ${value===snapshot?'selected':''}>${value.split('-').reverse().join('/')}</option>`).join('')}</select></label></div>`;
  const viewControls=`<div class="view-toggle"><button data-view="chart" class="${view==='chart'?'active':''}">Gráfico</button><button data-view="table" class="${view==='table'?'active':''}">Tabla</button></div>`;
  if(!curveRows.length){const reason=mode==='cer'?'Las fuentes públicas CER están temporalmente sin precios, índice o flujos contractuales válidos.':'No existe un cierre común de las curvas nominal y CER para calcular el breakeven.';container.innerHTML=`<div class="chart-head"><div><h3>${chart.title}</h3><p>${chart.subtitle}</p></div><div class="chart-actions">${selectors}${viewControls}</div></div><div class="yield-pending"><strong>Datos no disponibles</strong><p>${reason}</p></div><div class="source-citation"><span>Fuente:</span><a href="https://rendimientos.co/" target="_blank" rel="noreferrer">Rendimientos.co ↗</a></div>`;container.querySelector('.yield-mode').onchange=event=>{container.dataset.curve=event.target.value;delete container.dataset.snapshot;renderYieldCurves(container,rows,chart)};return}
  const W=900,H=390,L=100,R=28,T=28,B=68;const xs=curveRows.map(row=>+row.days_to_maturity),ys=curveRows.map(row=>+row.annual_yield);
  let minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);if(minX===maxX){minX=0;maxX+=1}if(minY===maxY){minY-=1;maxY+=1}const pad=(maxY-minY)*.12;minY-=pad;maxY+=pad;
  const x=value=>L+(value-minX)/(maxX-minX)*(W-L-R),y=value=>T+(maxY-value)/(maxY-minY)*(H-T-B);const ticks=Array.from({length:5},(_,i)=>minY+(maxY-minY)*i/4);
  const color=mode==='cer'?'#47d4f5':mode==='breakeven'?'#f6c85f':'#59a7ff';
  const visual=view==='chart'?`<div class="chart-wrap yield-chart"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${modeLabels[mode]}">${ticks.map(value=>`<line x1="${L}" x2="${W-R}" y1="${y(value)}" y2="${y(value)}"/><text x="${L-10}" y="${y(value)+5}" text-anchor="end">${value.toLocaleString('es-AR',{maximumFractionDigits:1})}%</text>`).join('')}<path class="series-line" stroke="${color}" d="${curveRows.map((row,index)=>`${index?'L':'M'}${x(+row.days_to_maturity).toFixed(1)},${y(+row.annual_yield).toFixed(1)}`).join(' ')}"/>${curveRows.map(row=>`<circle class="yield-point" data-ticker="${escapeHTML(row.ticker)}" cx="${x(+row.days_to_maturity)}" cy="${y(+row.annual_yield)}" r="5" fill="${color}"/>`).join('')}<text x="${L}" y="${H-18}">${Math.round(minX)} días</text><text x="${W-R}" y="${H-18}" text-anchor="end">${Math.round(maxX)} días</text></svg><div class="tooltip"></div></div>`:`<div class="data-table-scroll yield-table"><table><thead><tr>${mode==='breakeven'?'<th>Vencimiento</th><th>Instrumento nominal</th><th>Plazo</th><th>TIR nominal</th><th>TIR CER interpolada</th><th>Breakeven</th>':'<th>Ticker</th><th>Instrumento</th><th>Vencimiento</th><th>Plazo</th><th>Precio</th><th>TIR EA</th><th>TEM</th><th>Duración</th><th>Volumen</th>'}</tr></thead><tbody>${curveRows.map(row=>mode==='breakeven'?`<tr><td>${row.maturity_date}</td><td>${row.ticker}</td><td>${row.days_to_maturity} días</td><td>${Number(row.raw_nominal_yield||row.annual_yield).toLocaleString('es-AR',{maximumFractionDigits:2})}%</td><td>${Number(row.real_yield).toLocaleString('es-AR',{maximumFractionDigits:2})}%</td><td>${Number(row.annual_yield).toLocaleString('es-AR',{maximumFractionDigits:2})}%</td></tr>`:`<tr><td>${row.ticker}</td><td>${escapeHTML(row.instrument_name)}</td><td>${row.maturity_date}</td><td>${row.days_to_maturity} días</td><td>${Number(row.price).toLocaleString('es-AR',{maximumFractionDigits:4})}</td><td>${Number(row.annual_yield).toLocaleString('es-AR',{maximumFractionDigits:2})}%</td><td>${Number(row.monthly_yield).toLocaleString('es-AR',{maximumFractionDigits:2})}%</td><td>${Number(row.duration_years).toLocaleString('es-AR',{maximumFractionDigits:2})} años</td><td>${Number(row.volume).toLocaleString('es-AR',{maximumFractionDigits:0})}</td></tr>`).join('')}</tbody></table></div>`;
  const citations=mode==='cer'?`<a href="https://rendimientos.co/" target="_blank" rel="noreferrer">Rendimientos.co ↗</a><a href="https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables_datos.asp" target="_blank" rel="noreferrer">BCRA ↗</a>`:`<a href="https://api.argentinadatos.com/v1/finanzas/letras" target="_blank" rel="noreferrer">ArgentinaDatos ↗</a><a href="https://data912.com/" target="_blank" rel="noreferrer">Data912 ↗</a>`;
  container.innerHTML=`<div class="chart-head"><div><h3>${chart.title}</h3><p>${chart.subtitle}</p></div><div class="chart-actions">${selectors}${viewControls}</div></div><div class="latest-row"><div><i style="background:${color}"></i><span>${modeLabels[mode]}</span><strong>${curveRows.length} instrumentos</strong><small>${snapshot}</small></div></div>${visual}<p class="yield-note">TIR efectiva anual con días reales/365. La curva nominal combina valores finales contractuales con cotizaciones demoradas; CER se calcula con precio, CER oficial y flujos contractuales. El breakeven aplica Fisher e interpola sólo dentro de plazos observados.</p><div class="source-citation"><span>Fuentes:</span>${citations}</div>`;
  container.querySelector('.yield-mode').onchange=event=>{container.dataset.curve=event.target.value;delete container.dataset.snapshot;renderYieldCurves(container,rows,chart)};container.querySelector('.yield-snapshot').onchange=event=>{container.dataset.snapshot=event.target.value;renderYieldCurves(container,rows,chart)};container.querySelectorAll('[data-view]').forEach(button=>button.onclick=()=>{container.dataset.view=button.dataset.view;renderYieldCurves(container,rows,chart)});
  const svg=container.querySelector('svg'),tip=container.querySelector('.tooltip');if(svg)svg.onpointermove=event=>{const point=event.target.closest('.yield-point');if(!point){tip.style.opacity=0;return}const row=curveRows.find(item=>item.ticker===point.dataset.ticker);tip.innerHTML=`<b>${row.ticker}</b><span>${row.maturity_date} · ${row.days_to_maturity} días</span><strong>${Number(row.annual_yield).toLocaleString('es-AR',{maximumFractionDigits:2})}%</strong>`;tip.style.opacity=1;tip.style.left=`${Math.min(80,Math.max(12,event.offsetX/svg.clientWidth*100))}%`};if(svg)svg.onpointerleave=()=>tip.style.opacity=0;
}
function renderChart(container, rows, chart) {
  const availableSeries = chartSeries(chart); const range = container.dataset.range || chart.defaultRange || 'ALL';
  const seriesEntries = Object.entries(availableSeries);
  const colorFor = id => COLORS[Math.max(0, seriesEntries.findIndex(([seriesId])=>seriesId===id)) % COLORS.length];
  const toggleMetric = chart.metricToggle ? (state.get(chart) || chart.metricToggle.default) : null;
  const defaultVisible = chart.defaultVisibleByMetric?.[toggleMetric] || chart.defaultVisible || Object.keys(availableSeries);
  if (!visibility.has(chart)) visibility.set(chart, new Set(defaultVisible.filter(id=>availableSeries[id])));
  const visible = visibility.get(chart); const availableIds = new Set(Object.keys(availableSeries));
  for (const id of [...visible]) if (!availableIds.has(id)) visible.delete(id);
  if (![...visible].some(id=>availableIds.has(id))) Object.keys(availableSeries).forEach(id=>visible.add(id));
  const selectedSeries = Object.fromEntries(Object.entries(availableSeries).filter(([id])=>visible.has(id)));
  const compositeState = chart.composite ? (state.get(chart) || { sector: chart.composite.defaultSector, metric: chart.composite.defaultMetric }) : null;
  const displayUnit = chart.metricToggle?.units?.[toggleMetric] || chart.composite?.units?.[compositeState?.metric] || ((chart.composite && compositeState.metric === 'yoy') || toggleMetric === 'mom' ? '%' : chart.unit);
  const allSelectedPoints = rows.filter(r => selectedSeries[r.series_id]).map(r => ({...r, rawValue:r.value, date:+periodDate(r.period), value:+r.value})).filter(r=>Number.isFinite(r.value)).sort((a,b)=>a.date-b.date);
  const coverageDates = [...new Set(allSelectedPoints.map(p=>p.date))];
  const periodByDate = new Map(allSelectedPoints.map(point=>[point.date,point.period]));
  const points = filterRange(allSelectedPoints, range, container.dataset.from, container.dataset.to);
  const viewMode = container.dataset.view || 'chart';
  const tableLimit = Math.max(100, +(container.dataset.tableLimit || 100));
  const tableModel = buildTableModel(points, selectedSeries, colorFor);
  const latest = Object.keys(selectedSeries).map(id => { const list=points.filter(p=>p.series_id===id).sort((a,b)=>a.date-b.date); return {id,label:selectedSeries[id],color:colorFor(id),row:list.at(-1)}; }).filter(x=>x.row);
  const xs=points.map(p=>p.date), ys=points.map(p=>p.value); let minX=Math.min(...xs), maxX=Math.max(...xs), minY=Math.min(...ys), maxY=Math.max(...ys);
  if (!points.length) { container.innerHTML='<p class="empty">Sin datos disponibles.</p>'; return; }
  if (minX===maxX) { minX-=1; maxX+=1; } if (chart.includeZero) { minY=Math.min(minY,0); maxY=Math.max(maxY,0); } if(minY===maxY){minY-=1;maxY+=1} const pad=(maxY-minY)*.12; minY-=pad;maxY+=pad;
  const W=900,H=390,L=126,R=22,T=30,B=66; const x=v=>L+(v-minX)/(maxX-minX)*(W-L-R), y=v=>T+(maxY-v)/(maxY-minY)*(H-T-B);
  const ticks=Array.from({length:5},(_,i)=>minY+(maxY-minY)*i/4);
  const visuals=chart.type==='bar'
    ? latest.map(s=>{const list=points.filter(p=>p.series_id===s.id).sort((a,b)=>a.date-b.date);const width=Math.max(.8,Math.min(18,(W-L-R)/Math.max(1,list.length)*.76));const zero=y(0);return list.map(p=>`<rect class="series-bar" fill="${s.color}" x="${(x(p.date)-width/2).toFixed(1)}" y="${Math.min(y(p.value),zero).toFixed(1)}" width="${width.toFixed(1)}" height="${Math.max(1,Math.abs(zero-y(p.value))).toFixed(1)}"/>`).join('')}).join('')
    : latest.map(s=>{const list=points.filter(p=>p.series_id===s.id).sort((a,b)=>a.date-b.date);return `<path class="series-line" stroke="${s.color}" d="${list.map((p,i)=>`${i?'L':'M'}${x(p.date).toFixed(1)},${y(p.value).toFixed(1)}`).join(' ')}"/>`;}).join('');
  const titleControls = chart.composite ? `<div class="chart-selectors"><label>Vista<select class="metric-select">${Object.entries(chart.composite.metrics).map(([k,v])=>`<option value="${k}" ${compositeState.metric===k?'selected':''}>${v}</option>`).join('')}</select></label><label>${chart.composite.dimensionLabel || 'Rama'}<select class="sector-select">${Object.entries(chart.composite.sectors).map(([k,v])=>`<option value="${k}" ${compositeState.sector===k?'selected':''}>${v}</option>`).join('')}</select></label></div>` : chart.metricToggle ? `<div class="chart-selectors"><label>Vista<select class="toggle-metric-select">${Object.entries(chart.metricToggle.labels).map(([k,v])=>`<option value="${k}" ${toggleMetric===k?'selected':''}>${v}</option>`).join('')}</select></label></div>` : chart.selector ? `<select class="chart-select">${Object.entries(chart.selector).map(([k,v])=>`<option value="${k}" ${(state.get(chart)||chart.selected)===k?'selected':''}>${v}</option>`).join('')}</select>` : chart.regionSelector ? `<select class="chart-select">${Object.entries(chart.regionSelector).map(([k,v])=>`<option value="${k}" ${(state.get(chart)||chart.region)===k?'selected':''}>${v}</option>`).join('')}</select>`:'';
  const viewControls = `<div class="view-toggle" role="group" aria-label="Formato de visualización"><button type="button" data-view="chart" class="${viewMode==='chart'?'active':''}" aria-pressed="${viewMode==='chart'}">Gráfico</button><button type="button" data-view="table" class="${viewMode==='table'?'active':''}" aria-pressed="${viewMode==='table'}">Tabla</button></div>`;
  const sources = chart.sources || [...new Map(allSelectedPoints.map(row => [sourceName(row), {label:sourceName(row),url:row.source_url}])).values()].filter(row=>row.url);
  const firstCoverage = coverageDates[0], lastCoverage = coverageDates.at(-1);
  const activeFrom = container.dataset.from ? Number(container.dataset.from) : (points[0]?.date ?? firstCoverage);
  const activeTo = container.dataset.to ? Number(container.dataset.to) : (points.at(-1)?.date ?? lastCoverage);
  const fromIndex = Math.max(0, coverageDates.findIndex(d=>d>=activeFrom));
  const toCandidate = coverageDates.findLastIndex(d=>d<=activeTo); const toIndex = toCandidate<0?coverageDates.length-1:toCandidate;
  const periodLabel = date => precisePeriodLabel(periodByDate.get(date) || new Date(date).toISOString().slice(0,10));
  const visualContent = viewMode === 'table' ? tableHTML(tableModel, displayUnit, tableLimit) : `<div class="chart-wrap"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${chart.title}">
      ${ticks.map(v=>`<line x1="${L}" x2="${W-R}" y1="${y(v)}" y2="${y(v)}"/><text x="${L-10}" y="${y(v)+4}" text-anchor="end">${human(v,displayUnit).replace('USD ','')}</text>`).join('')}
      ${visuals}<rect class="hover-zone" x="${L}" y="${T}" width="${W-L-R}" height="${H-T-B}"/><line class="crosshair" y1="${T}" y2="${H-B}"/><circle class="hover-dot" r="4"/>
      <text x="${L}" y="${H-15}">${new Date(minX).getUTCFullYear()}</text><text x="${W-R}" y="${H-15}" text-anchor="end">${new Date(maxX).getUTCFullYear()}</text>
    </svg><div class="tooltip"></div></div>`;
  container.innerHTML=`<div class="chart-head"><div><h3>${chart.title}</h3><p>${chart.subtitle}</p></div><div class="chart-actions">${titleControls}${viewControls}</div></div>
    <div class="latest-row">${latest.map(s=>`<div><i style="background:${s.color}"></i><span>${s.label}</span><strong>${human(s.row.value,displayUnit)}</strong><small>${s.row.period}</small></div>`).join('')}</div>
    ${visualContent}
    <div class="chart-foot"><div class="legend series-toggle">${Object.entries(availableSeries).map(([id,label],i)=>`<button class="${visible.has(id)?'visible':'muted'}" data-series="${id}"><i style="background:${COLORS[i]}"></i><span>${label}</span><b>${visible.has(id)?'✓':'+'}</b></button>`).join('')}</div><div class="ranges">${['1Y','5Y','10Y','ALL'].map(r=>`<button class="${!container.dataset.from&&!container.dataset.to&&range===r?'active':''}" data-range="${r}">${r==='ALL'?'Todo':r}</button>`).join('')}</div></div>
    <div class="range-segment"><div class="range-copy"><span>PERÍODO VISIBLE</span></div><div class="range-steppers"><div class="range-stepper"><span>Inicio</span><div><button type="button" data-range-step="from-prev" aria-label="Mover el inicio un período hacia atrás">‹</button><strong class="range-from-label">${periodLabel(coverageDates[fromIndex])}</strong><button type="button" data-range-step="from-next" aria-label="Mover el inicio un período hacia adelante">›</button></div></div><i>—</i><div class="range-stepper"><span>Final</span><div><button type="button" data-range-step="to-prev" aria-label="Mover el final un período hacia atrás">‹</button><strong class="range-to-label">${periodLabel(coverageDates[toIndex])}</strong><button type="button" data-range-step="to-next" aria-label="Mover el final un período hacia adelante">›</button></div></div></div><div class="dual-range"><div class="range-track"></div><div class="range-fill"></div><input class="range-from" type="range" min="0" max="${coverageDates.length-1}" value="${fromIndex}" aria-label="Inicio del período visible"><input class="range-to" type="range" min="0" max="${coverageDates.length-1}" value="${toIndex}" aria-label="Final del período visible"></div><div class="coverage-labels"><span>${periodLabel(firstCoverage)}</span><span>${periodLabel(lastCoverage)}</span></div></div>
    <div class="source-citation"><span>Fuente${sources.length>1?'s':''}:</span>${sources.map(source=>`<a href="${source.url}" target="_blank" rel="noreferrer">${source.label} ↗</a>`).join('')}</div>`;
  container.querySelectorAll('[data-view]').forEach(button=>button.onclick=()=>{container.dataset.view=button.dataset.view;delete container.dataset.tableLimit;renderChart(container,rows,chart)});
  const moreButton=container.querySelector('.table-more'); if(moreButton) moreButton.onclick=()=>{container.dataset.tableLimit=tableLimit+100;renderChart(container,rows,chart)};
  const downloadButton=container.querySelector('.table-download'); if(downloadButton) downloadButton.onclick=()=>downloadTableCSV(tableModel,chart.title);
  container.querySelectorAll('[data-range]').forEach(b=>b.onclick=()=>{container.dataset.range=b.dataset.range;delete container.dataset.from;delete container.dataset.to;renderChart(container,rows,chart)});
  container.querySelectorAll('[data-series]').forEach(b=>b.onclick=()=>{const id=b.dataset.series;if(visible.has(id)){if(visible.size>1)visible.delete(id)}else visible.add(id);renderChart(container,rows,chart)});
  const fromSlider=container.querySelector('.range-from'),toSlider=container.querySelector('.range-to'),fill=container.querySelector('.range-fill');
  const lastIndex=coverageDates.length-1;
  const paintRange=()=>{let a=+fromSlider.value,b=+toSlider.value;if(lastIndex>0&&a>b-1){if(document.activeElement===fromSlider)a=Math.max(0,b-1);else b=Math.min(lastIndex,a+1)}fromSlider.value=a;toSlider.value=b;const divisor=Math.max(1,lastIndex);fill.style.left=`${a/divisor*100}%`;fill.style.right=`${100-b/divisor*100}%`;container.querySelector('.range-from-label').textContent=periodLabel(coverageDates[a]);container.querySelector('.range-to-label').textContent=periodLabel(coverageDates[b]);container.querySelector('[data-range-step="from-prev"]').disabled=a<=0;container.querySelector('[data-range-step="from-next"]').disabled=a>=b-(lastIndex>0?1:0);container.querySelector('[data-range-step="to-prev"]').disabled=b<=a+(lastIndex>0?1:0);container.querySelector('[data-range-step="to-next"]').disabled=b>=lastIndex;};
  paintRange(); fromSlider.oninput=toSlider.oninput=paintRange;
  const applySlider=()=>{const a=coverageDates[+fromSlider.value],b=coverageDates[+toSlider.value];container.dataset.from=String(a);container.dataset.to=String(b);renderChart(container,rows,chart)};
  fromSlider.onchange=toSlider.onchange=applySlider;
  container.querySelectorAll('[data-range-step]').forEach(button=>button.onclick=()=>{let a=+fromSlider.value,b=+toSlider.value;if(button.dataset.rangeStep==='from-prev')a=Math.max(0,a-1);if(button.dataset.rangeStep==='from-next')a=Math.min(b-1,a+1);if(button.dataset.rangeStep==='to-prev')b=Math.max(a+1,b-1);if(button.dataset.rangeStep==='to-next')b=Math.min(lastIndex,b+1);fromSlider.value=a;toSlider.value=b;paintRange();applySlider()});
  const select=container.querySelector('.chart-select'); if(select) select.onchange=()=>{state.set(chart,select.value);visibility.delete(chart);renderChart(container,rows,chart)};
  const metricSelect=container.querySelector('.metric-select'),sectorSelect=container.querySelector('.sector-select');
  if(metricSelect&&sectorSelect){const updateComposite=()=>{state.set(chart,{metric:metricSelect.value,sector:sectorSelect.value});visibility.delete(chart);delete container.dataset.from;delete container.dataset.to;renderChart(container,rows,chart)};metricSelect.onchange=sectorSelect.onchange=updateComposite;}
  const toggleMetricSelect=container.querySelector('.toggle-metric-select'); if(toggleMetricSelect) toggleMetricSelect.onchange=()=>{state.set(chart,toggleMetricSelect.value);visibility.delete(chart);delete container.dataset.from;delete container.dataset.to;renderChart(container,rows,chart)};
  const svg=container.querySelector('svg'), tip=container.querySelector('.tooltip'), cross=container.querySelector('.crosshair'), dot=container.querySelector('.hover-dot');
  if(svg){svg.onpointermove=e=>{const rect=svg.getBoundingClientRect(), px=(e.clientX-rect.left)/rect.width*W, target=minX+Math.max(0,Math.min(1,(px-L)/(W-L-R)))*(maxX-minX); const nearest=points.reduce((a,b)=>Math.abs(b.date-target)<Math.abs(a.date-target)?b:a); cross.setAttribute('x1',x(nearest.date));cross.setAttribute('x2',x(nearest.date));dot.setAttribute('cx',x(nearest.date));dot.setAttribute('cy',y(nearest.value));cross.style.opacity=dot.style.opacity=1; tip.innerHTML=`<b>${nearest.period}</b><span>${selectedSeries[nearest.series_id]}</span><strong>${human(nearest.value,displayUnit)}</strong>`;tip.style.opacity=1;tip.style.left=`${Math.min(78,Math.max(8,(x(nearest.date)/W)*100))}%`;};
  svg.onpointerleave=()=>{tip.style.opacity=cross.style.opacity=dot.style.opacity=0};}
}

function sectionHTML(section){return `<section id="${section.id}" class="data-section"><header class="section-title"><span>${section.eyebrow}</span><h2>${section.title}</h2><p>${section.intro}</p>${section.warning?`<aside>${section.warning}</aside>`:''}</header><div class="charts">${section.charts.map(()=>'<article class="chart-card loading">Cargando datos…</article>').join('')}</div></section>`}

document.querySelector('#app').innerHTML=`<header class="topbar"><a class="brand" href="#inicio" aria-label="DatArg — volver al inicio"><span class="brand-logo"><img src="/datarg-logo.png" alt="DatArg"></span></a><div class="graph-picker"><button type="button" aria-expanded="false" aria-controls="graph-menu">Seleccionar gráfico <span>⌄</span></button><nav id="graph-menu" aria-label="Indicadores"><label class="graph-search"><span>Buscar gráfico</span><input type="search" placeholder="Escribí para filtrar…" autocomplete="off" spellcheck="false"></label>${sections.map(s=>`<a href="#${s.id}">${s.title}</a>`).join('')}<p class="graph-search-empty" hidden>Sin coincidencias</p></nav></div><div class="live"><i></i>Datos públicos</div></header>
<main><section id="inicio" class="hero"><div class="hero-grid"></div><div class="hero-copy"><p class="kicker">UN MAPA ABIERTO DE LA ECONOMÍA ARGENTINA</p><h1>Los datos detrás<br>de <em>la economía.</em></h1><p class="lead">Una lectura integrada, trazable y actualizada de los principales indicadores del país.</p><div class="hero-actions"><a href="#precios">Explorar indicadores ↓</a><span><b>${sections.length}</b> áreas temáticas</span><span><b>50k+</b> observaciones</span></div></div></section>
<section class="manifesto"><span>UNA SOLA PÁGINA</span><p>De la inflación al empleo, del dólar a la producción: desplazate para entender cómo se conectan las distintas dimensiones de la economía argentina.</p></section>
${sections.map(sectionHTML).join('')}</main><footer><div class="brand"><span class="brand-logo"><img src="/datarg-logo.png" alt="DatArg"></span></div><p>Datos públicos, metodología visible y fuentes trazables.</p><div class="footer-actions"><button id="notification-toggle" type="button" aria-pressed="false" hidden>Activar alertas</button><button id="install-app" type="button" hidden>Instalar DatArg ↓</button><a class="contact-link" href="mailto:maximiliano.lineiro@gmail.com">Contacto · maximiliano.lineiro@gmail.com</a><a href="/privacidad.html" target="_blank" rel="noreferrer">Privacidad</a><a href="#inicio">Volver arriba ↑</a></div></footer>`;

const sectionLoads=new WeakMap();
const loadSection=sectionElement=>{if(sectionLoads.has(sectionElement))return sectionLoads.get(sectionElement);const section=sections.find(item=>item.id===sectionElement.id);if(!section)return Promise.resolve();sectionElement.dataset.loaded='loading';const cards=[...sectionElement.querySelectorAll('.chart-card')];const pending=Promise.all(cards.map(async(card,index)=>{const chart=section.charts[index];try{const rows=await loadDataset(chart.file||section.file);card.classList.remove('loading');const renderer=chart.renderer||section.renderer;if(renderer==='maturities')renderMaturityChart(card,rows,chart);else if(renderer==='yield-curves')renderYieldCurves(card,rows,chart);else renderChart(card,rows,chart)}catch(error){console.error(error);card.classList.remove('loading');card.innerHTML='<p class="empty">No se pudo cargar este conjunto de datos.</p>'}})).finally(()=>{sectionElement.dataset.loaded='1';observer.unobserve(sectionElement)});sectionLoads.set(sectionElement,pending);return pending};
const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting)void loadSection(entry.target)}),{rootMargin:'400px'});
document.querySelectorAll('.data-section').forEach(s=>observer.observe(s));
const picker=document.querySelector('.graph-picker'),pickerButton=picker.querySelector('button'),navLinks=[...picker.querySelectorAll('nav a')];
const graphSearch=picker.querySelector('.graph-search input'),graphSearchEmpty=picker.querySelector('.graph-search-empty');
const normalizeSearch=value=>value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('es-AR').trim();
const filterGraphs=()=>{const query=normalizeSearch(graphSearch.value);let matches=0;navLinks.forEach(link=>{const visible=!query||normalizeSearch(link.textContent).includes(query);link.hidden=!visible;if(visible)matches+=1});graphSearchEmpty.hidden=matches>0};
const resetGraphSearch=()=>{graphSearch.value='';filterGraphs()};
const closePicker=()=>{picker.classList.remove('open');pickerButton.setAttribute('aria-expanded','false');resetGraphSearch()};
pickerButton.onclick=()=>{const open=picker.classList.toggle('open');pickerButton.setAttribute('aria-expanded',String(open));if(open)requestAnimationFrame(()=>graphSearch.focus());else resetGraphSearch()};
graphSearch.oninput=filterGraphs;
graphSearch.onkeydown=event=>{if(event.key==='Enter'){const first=navLinks.find(link=>!link.hidden);if(first){event.preventDefault();first.click()}}};
const scrollToGraph=async(event,link)=>{event.preventDefault();const target=document.querySelector(link.hash);if(!target)return;closePicker();const previous=target.previousElementSibling?.classList.contains('data-section')?target.previousElementSibling:null;await Promise.all([previous?loadSection(previous):Promise.resolve(),loadSection(target)]);history.pushState(null,'',link.hash);requestAnimationFrame(()=>requestAnimationFrame(()=>target.scrollIntoView({behavior:'smooth',block:'start'})))};
navLinks.forEach(link=>link.onclick=event=>void scrollToGraph(event,link));
document.addEventListener('click',event=>{if(!picker.contains(event.target))closePicker()});
document.addEventListener('keydown',event=>{if(event.key==='Escape'){closePicker();pickerButton.focus()}});
const activeObserver=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){navLinks.forEach(a=>a.classList.toggle('active',a.hash===`#${e.target.id}`))}}),{threshold:.25});document.querySelectorAll('.data-section').forEach(s=>activeObserver.observe(s));
const { announce = () => {} } = setupPWA() || {};
void setupNotifications({ announce });
