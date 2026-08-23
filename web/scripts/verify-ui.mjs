import { sections } from '../src/config.js';
import { AREAS } from '../src/areas.js';
import { readFile } from 'node:fs/promises';

const main = await readFile(new URL('../src/main.js', import.meta.url), 'utf8');
const styles = await readFile(new URL('../src/styles.css', import.meta.url), 'utf8');
const errors = [];
if (!main.includes('data-ui-version="sectioned-v1"')) errors.push('falta el marcador de la interfaz por secciones');
if (!main.includes('area-grid')) errors.push('falta la grilla de cuatro áreas');
if (main.includes('UNA SOLA PÁGINA')) errors.push('reapareció la interfaz antigua de scroll infinito');
if (main.includes('class="ranges"')) errors.push('reaparecieron los accesos rápidos de período 1Y/5Y/10Y/Todo');
if (!main.includes("section.charts.length===1")) errors.push('falta identificar las secciones de un solo gráfico');
if (!styles.includes('.charts.single-chart{width:clamp(720px,56.25%,1180px);max-width:100%;margin-inline:auto')) errors.push('falta el ancho compacto para gráficos individuales');

const assignments = AREAS.flatMap(area => area.sections.map(section => [section, area.id]));
const known = new Set(sections.map(section => section.id));
const counts = new Map();
for (const [id] of assignments) counts.set(id, (counts.get(id) || 0) + 1);
for (const id of known) {
  if (!counts.has(id)) errors.push(`el indicador "${id}" no fue asignado a ninguna área`);
  if ((counts.get(id) || 0) > 1) errors.push(`el indicador "${id}" está asignado a más de un área`);
}
for (const [id, area] of assignments) if (!known.has(id)) errors.push(`el área "${area}" referencia un indicador inexistente: "${id}"`);

if (errors.length) {
  console.error(`\nValidación de interfaz fallida:\n- ${errors.join('\n- ')}\n`);
  process.exit(1);
}
console.log(`Interfaz por secciones validada: ${AREAS.length} áreas, ${known.size} indicadores.`);
