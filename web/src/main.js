import './styles.css';
import { sections, COLORS } from './config.js';

const cache = new Map();
const state = new Map();
const visibility = new Map();

function parseCSV(text) {
  const lines = text.trim().split(/\r?\n/); const headers = lines.shift().split(',');
  return lines.map(line => { const cells = line.split(','); return Object.fromEntries(headers.map((h,i) => [h, cells[i]])); });
}
async function load(file) {
  if (!cache.has(file)) cache.set(file, fetch(`/data/${file}`).then(r => { if (!r.ok) throw new Error(file); return r.text(); }).then(parseCSV));
  return cache.get(file);
}
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
  if (id.startsWith('indec_')) return 'INDEC';
  if (id.startsWith('bcra_')) return 'BCRA';
  if (id.startsWith('datarg_bcra_')) return 'DatArg sobre fuentes BCRA, FMI y BCE';
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
function chartSeries(chart) {
  if (chart.composite) {
    const current = state.get(chart) || { sector: chart.composite.defaultSector, metric: chart.composite.defaultMetric };
    return { [`indec_industry_${current.sector}_${current.metric}`]: chart.composite.sectors[current.sector] };
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
    const min = from ? +new Date(`${from}-01T00:00:00Z`) : -Infinity;
    const max = to ? +new Date(`${to}-28T23:59:59Z`) + 4*864e5 : Infinity;
    return points.filter(p => p.date >= min && p.date <= max);
  }
  if (range === 'ALL' || !points.length) return points;
  const max = Math.max(...points.map(p=>p.date)); const years = range === '1Y' ? 1 : range === '5Y' ? 5 : 10;
  return points.filter(p => p.date >= max - years*365.25*864e5);
}
function renderChart(container, rows, chart) {
  const availableSeries = chartSeries(chart); const range = container.dataset.range || chart.defaultRange || 'ALL';
  if (!visibility.has(chart)) visibility.set(chart, new Set(Object.keys(availableSeries)));
  const visible = visibility.get(chart); const availableIds = new Set(Object.keys(availableSeries));
  for (const id of [...visible]) if (!availableIds.has(id)) visible.delete(id);
  if (![...visible].some(id=>availableIds.has(id))) Object.keys(availableSeries).forEach(id=>visible.add(id));
  const selectedSeries = Object.fromEntries(Object.entries(availableSeries).filter(([id])=>visible.has(id)));
  const compositeState = chart.composite ? (state.get(chart) || { sector: chart.composite.defaultSector, metric: chart.composite.defaultMetric }) : null;
  const toggleMetric = chart.metricToggle ? (state.get(chart) || chart.metricToggle.default) : null;
  const displayUnit = chart.metricToggle?.units?.[toggleMetric] || ((chart.composite && compositeState.metric === 'yoy') || toggleMetric === 'mom' ? '%' : chart.unit);
  const allSelectedPoints = rows.filter(r => selectedSeries[r.series_id]).map(r => ({...r, date:+periodDate(r.period), value:+r.value})).filter(r=>Number.isFinite(r.value)).sort((a,b)=>a.date-b.date);
  const coverageDates = [...new Set(allSelectedPoints.map(p=>p.date))];
  const points = filterRange(allSelectedPoints, range, container.dataset.from, container.dataset.to);
  const latest = Object.keys(selectedSeries).map((id,i) => { const list=points.filter(p=>p.series_id===id).sort((a,b)=>a.date-b.date); return {id,label:selectedSeries[id],color:COLORS[i],row:list.at(-1)}; }).filter(x=>x.row);
  const xs=points.map(p=>p.date), ys=points.map(p=>p.value); let minX=Math.min(...xs), maxX=Math.max(...xs), minY=Math.min(...ys), maxY=Math.max(...ys);
  if (!points.length) { container.innerHTML='<p class="empty">Sin datos disponibles.</p>'; return; }
  if (minX===maxX) { minX-=1; maxX+=1; } if(minY===maxY){minY-=1;maxY+=1} const pad=(maxY-minY)*.12; minY-=pad;maxY+=pad;
  const W=900,H=360,L=62,R=18,T=28,B=46; const x=v=>L+(v-minX)/(maxX-minX)*(W-L-R), y=v=>T+(maxY-v)/(maxY-minY)*(H-T-B);
  const ticks=Array.from({length:5},(_,i)=>minY+(maxY-minY)*i/4);
  const paths=latest.map(s=>{const list=points.filter(p=>p.series_id===s.id).sort((a,b)=>a.date-b.date);return `<path class="series-line" stroke="${s.color}" d="${list.map((p,i)=>`${i?'L':'M'}${x(p.date).toFixed(1)},${y(p.value).toFixed(1)}`).join(' ')}"/>`;}).join('');
  const titleControls = chart.composite ? `<div class="chart-selectors"><label>Vista<select class="metric-select">${Object.entries(chart.composite.metrics).map(([k,v])=>`<option value="${k}" ${compositeState.metric===k?'selected':''}>${v}</option>`).join('')}</select></label><label>Rama<select class="sector-select">${Object.entries(chart.composite.sectors).map(([k,v])=>`<option value="${k}" ${compositeState.sector===k?'selected':''}>${v}</option>`).join('')}</select></label></div>` : chart.metricToggle ? `<div class="chart-selectors"><label>Vista<select class="toggle-metric-select">${Object.entries(chart.metricToggle.labels).map(([k,v])=>`<option value="${k}" ${toggleMetric===k?'selected':''}>${v}</option>`).join('')}</select></label></div>` : chart.selector ? `<select class="chart-select">${Object.entries(chart.selector).map(([k,v])=>`<option value="${k}" ${(state.get(chart)||chart.selected)===k?'selected':''}>${v}</option>`).join('')}</select>` : chart.regionSelector ? `<select class="chart-select">${Object.entries(chart.regionSelector).map(([k,v])=>`<option value="${k}" ${(state.get(chart)||chart.region)===k?'selected':''}>${v}</option>`).join('')}</select>`:'';
  const sources = [...new Map(allSelectedPoints.map(row => [sourceName(row), row])).values()].filter(row=>row.source_url);
  const firstCoverage = coverageDates[0], lastCoverage = coverageDates.at(-1);
  const activeFrom = container.dataset.from ? +new Date(`${container.dataset.from}-01T00:00:00Z`) : (points[0]?.date ?? firstCoverage);
  const activeTo = container.dataset.to ? +new Date(`${container.dataset.to}-28T23:59:59Z`) : (points.at(-1)?.date ?? lastCoverage);
  const fromIndex = Math.max(0, coverageDates.findIndex(d=>d>=activeFrom));
  const toCandidate = coverageDates.findLastIndex(d=>d<=activeTo); const toIndex = toCandidate<0?coverageDates.length-1:toCandidate;
  const periodLabel = d => { const value=new Date(d); return value.getUTCFullYear()===new Date(lastCoverage).getUTCFullYear() ? `${value.getUTCMonth()+1}/${value.getUTCFullYear()}` : `${value.getUTCFullYear()}`; };
  container.innerHTML=`<div class="chart-head"><div><h3>${chart.title}</h3><p>${chart.subtitle}</p></div>${titleControls}</div>
    <div class="latest-row">${latest.map(s=>`<div><i style="background:${s.color}"></i><span>${s.label}</span><strong>${human(s.row.value,displayUnit)}</strong><small>${s.row.period}</small></div>`).join('')}</div>
    <div class="chart-wrap"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${chart.title}">
      ${ticks.map(v=>`<line x1="${L}" x2="${W-R}" y1="${y(v)}" y2="${y(v)}"/><text x="${L-10}" y="${y(v)+4}" text-anchor="end">${human(v,displayUnit).replace('USD ','')}</text>`).join('')}
      ${paths}<rect class="hover-zone" x="${L}" y="${T}" width="${W-L-R}" height="${H-T-B}"/><line class="crosshair" y1="${T}" y2="${H-B}"/><circle class="hover-dot" r="4"/>
      <text x="${L}" y="${H-15}">${new Date(minX).getUTCFullYear()}</text><text x="${W-R}" y="${H-15}" text-anchor="end">${new Date(maxX).getUTCFullYear()}</text>
    </svg><div class="tooltip"></div></div>
    <div class="chart-foot"><div class="legend series-toggle">${Object.entries(availableSeries).map(([id,label],i)=>`<button class="${visible.has(id)?'visible':'muted'}" data-series="${id}"><i style="background:${COLORS[i]}"></i><span>${label}</span><b>${visible.has(id)?'✓':'+'}</b></button>`).join('')}</div><div class="ranges">${['1Y','5Y','10Y','ALL'].map(r=>`<button class="${!container.dataset.from&&!container.dataset.to&&range===r?'active':''}" data-range="${r}">${r==='ALL'?'Todo':r}</button>`).join('')}</div></div>
    <div class="range-segment"><div class="range-copy"><span>PERÍODO VISIBLE</span><strong class="range-from-label">${periodLabel(coverageDates[fromIndex])}</strong><i>—</i><strong class="range-to-label">${periodLabel(coverageDates[toIndex])}</strong></div><div class="dual-range"><div class="range-track"></div><div class="range-fill"></div><input class="range-from" type="range" min="0" max="${coverageDates.length-1}" value="${fromIndex}"><input class="range-to" type="range" min="0" max="${coverageDates.length-1}" value="${toIndex}"></div><div class="coverage-labels"><span>${periodLabel(firstCoverage)}</span><span>${periodLabel(lastCoverage)}</span></div></div>
    <div class="source-citation"><span>Fuente${sources.length>1?'s':''}:</span>${sources.map(row=>`<a href="${row.source_url}" target="_blank" rel="noreferrer">${sourceName(row)} ↗</a>`).join('')}</div>`;
  container.querySelectorAll('[data-range]').forEach(b=>b.onclick=()=>{container.dataset.range=b.dataset.range;delete container.dataset.from;delete container.dataset.to;renderChart(container,rows,chart)});
  container.querySelectorAll('[data-series]').forEach(b=>b.onclick=()=>{const id=b.dataset.series;if(visible.has(id)){if(visible.size>1)visible.delete(id)}else visible.add(id);renderChart(container,rows,chart)});
  const fromSlider=container.querySelector('.range-from'),toSlider=container.querySelector('.range-to'),fill=container.querySelector('.range-fill');
  const paintRange=()=>{let a=+fromSlider.value,b=+toSlider.value;if(a>b-1){if(document.activeElement===fromSlider)a=Math.max(0,b-1);else b=Math.min(coverageDates.length-1,a+1)}fromSlider.value=a;toSlider.value=b;fill.style.left=`${a/(coverageDates.length-1)*100}%`;fill.style.right=`${100-b/(coverageDates.length-1)*100}%`;container.querySelector('.range-from-label').textContent=periodLabel(coverageDates[a]);container.querySelector('.range-to-label').textContent=periodLabel(coverageDates[b]);};
  paintRange(); fromSlider.oninput=toSlider.oninput=paintRange;
  const applySlider=()=>{const a=coverageDates[+fromSlider.value],b=coverageDates[+toSlider.value];container.dataset.from=new Date(a).toISOString().slice(0,7);container.dataset.to=new Date(b).toISOString().slice(0,7);renderChart(container,rows,chart)};
  fromSlider.onchange=toSlider.onchange=applySlider;
  const select=container.querySelector('.chart-select'); if(select) select.onchange=()=>{state.set(chart,select.value);visibility.delete(chart);renderChart(container,rows,chart)};
  const metricSelect=container.querySelector('.metric-select'),sectorSelect=container.querySelector('.sector-select');
  if(metricSelect&&sectorSelect){const updateComposite=()=>{state.set(chart,{metric:metricSelect.value,sector:sectorSelect.value});visibility.delete(chart);delete container.dataset.from;delete container.dataset.to;renderChart(container,rows,chart)};metricSelect.onchange=sectorSelect.onchange=updateComposite;}
  const toggleMetricSelect=container.querySelector('.toggle-metric-select'); if(toggleMetricSelect) toggleMetricSelect.onchange=()=>{state.set(chart,toggleMetricSelect.value);visibility.delete(chart);delete container.dataset.from;delete container.dataset.to;renderChart(container,rows,chart)};
  const svg=container.querySelector('svg'), tip=container.querySelector('.tooltip'), cross=container.querySelector('.crosshair'), dot=container.querySelector('.hover-dot');
  svg.onpointermove=e=>{const rect=svg.getBoundingClientRect(), px=(e.clientX-rect.left)/rect.width*W, target=minX+Math.max(0,Math.min(1,(px-L)/(W-L-R)))*(maxX-minX); const nearest=points.reduce((a,b)=>Math.abs(b.date-target)<Math.abs(a.date-target)?b:a); cross.setAttribute('x1',x(nearest.date));cross.setAttribute('x2',x(nearest.date));dot.setAttribute('cx',x(nearest.date));dot.setAttribute('cy',y(nearest.value));cross.style.opacity=dot.style.opacity=1; tip.innerHTML=`<b>${nearest.period}</b><span>${selectedSeries[nearest.series_id]}</span><strong>${human(nearest.value,displayUnit)}</strong>`;tip.style.opacity=1;tip.style.left=`${Math.min(78,Math.max(8,(x(nearest.date)/W)*100))}%`;};
  svg.onpointerleave=()=>{tip.style.opacity=cross.style.opacity=dot.style.opacity=0};
}

function sectionHTML(section,index){return `<section id="${section.id}" class="data-section"><div class="section-number">${String(index+1).padStart(2,'0')}</div><header class="section-title"><span>${section.eyebrow}</span><h2>${section.title}</h2><p>${section.intro}</p>${section.warning?`<aside>${section.warning}</aside>`:''}</header><div class="charts">${section.charts.map(()=>'<article class="chart-card loading">Cargando datos…</article>').join('')}</div></section>`}

document.querySelector('#app').innerHTML=`<header class="topbar"><a class="brand" href="#inicio"><span>DA</span><b>DatArg</b></a><div class="graph-picker"><button type="button" aria-expanded="false" aria-controls="graph-menu">Seleccionar gráfico <span>⌄</span></button><nav id="graph-menu" aria-label="Indicadores">${sections.map(s=>`<a href="#${s.id}">${s.title}</a>`).join('')}</nav></div><div class="live"><i></i>Datos públicos</div></header>
<main><section id="inicio" class="hero"><div class="hero-grid"></div><div class="hero-copy"><p class="kicker">UN MAPA ABIERTO DE LA ECONOMÍA ARGENTINA</p><h1>Los datos detrás<br>de <em>la economía.</em></h1><p class="lead">Una lectura integrada, trazable y actualizada de los principales indicadores del país.</p><div class="hero-actions"><a href="#precios">Explorar indicadores ↓</a><span><b>${sections.length}</b> áreas temáticas</span><span><b>50k+</b> observaciones</span></div></div></section>
<section class="manifesto"><span>UNA SOLA PÁGINA</span><p>De la inflación al empleo, del dólar a la producción: desplazate para entender cómo se conectan las distintas dimensiones de la economía argentina.</p></section>
${sections.map(sectionHTML).join('')}</main><footer><div class="brand"><span>DA</span><b>DatArg</b></div><p>Datos públicos, metodología visible y fuentes trazables.</p><a href="#inicio">Volver arriba ↑</a></footer>`;

const observer=new IntersectionObserver(entries=>entries.forEach(async entry=>{if(!entry.isIntersecting)return;const section=sections.find(s=>s.id===entry.target.id);if(!section||entry.target.dataset.loaded)return;entry.target.dataset.loaded='1';try{const rows=await load(section.file);entry.target.querySelectorAll('.chart-card').forEach((card,i)=>{card.classList.remove('loading');renderChart(card,rows,section.charts[i])});}catch{entry.target.querySelector('.charts').innerHTML='<p class="empty">No se pudo cargar este conjunto de datos.</p>';}observer.unobserve(entry.target)}),{rootMargin:'400px'});
document.querySelectorAll('.data-section').forEach(s=>observer.observe(s));
const picker=document.querySelector('.graph-picker'),pickerButton=picker.querySelector('button'),navLinks=[...picker.querySelectorAll('nav a')];
const closePicker=()=>{picker.classList.remove('open');pickerButton.setAttribute('aria-expanded','false')};
pickerButton.onclick=()=>{const open=picker.classList.toggle('open');pickerButton.setAttribute('aria-expanded',String(open))};
navLinks.forEach(link=>link.onclick=closePicker);
document.addEventListener('click',event=>{if(!picker.contains(event.target))closePicker()});
document.addEventListener('keydown',event=>{if(event.key==='Escape'){closePicker();pickerButton.focus()}});
const activeObserver=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){navLinks.forEach(a=>a.classList.toggle('active',a.hash===`#${e.target.id}`))}}),{threshold:.25});document.querySelectorAll('.data-section').forEach(s=>activeObserver.observe(s));
