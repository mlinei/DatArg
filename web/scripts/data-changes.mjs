import { execFileSync } from 'node:child_process';
import { readdir, readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

export const DATASETS = {
  'consolidated_debt.csv': { label: 'deuda estatal neta', section: 'deuda-neta' },
  'country_risk.csv': { label: 'riesgo país', section: 'riesgo' },
  'emae.csv': { label: 'actividad económica', section: 'actividad' },
  'exchange_rates.csv': { label: 'tipos de cambio', section: 'dolar' },
  'fiscal.csv': { label: 'recaudación y resultado fiscal', section: 'fiscal' },
  'gdp.csv': { label: 'producto interno bruto', section: 'pbi' },
  'industry.csv': { label: 'industria manufacturera', section: 'industria' },
  'inflation.csv': { label: 'inflación', section: 'precios' },
  'interest_rates.csv': { label: 'tasas de interés', section: 'tasas' },
  'labor.csv': { label: 'mercado laboral', section: 'trabajo' },
  'registered_employment.csv': { label: 'empleo privado registrado', section: 'empleo-sector' },
  'markets.csv': { label: 'S&P Merval en dólares', section: 'mercados' },
  'monetary_aggregates.csv': { label: 'base y agregados monetarios', section: 'agregados-monetarios' },
  'net_reserves.csv': { label: 'reservas netas', section: 'reservas-netas' },
  'poverty.csv': { label: 'pobreza e indigencia', section: 'pobreza' },
  'private_fx_deposits.csv': { label: 'depósitos privados en dólares', section: 'depositos-dolares' },
  'profit_dividends.csv': { label: 'giros de utilidades y dividendos', section: 'dividendos' },
  'public_debt.csv': { label: 'deuda pública', section: 'deuda' },
  'public_investment.csv': { label: 'inversión pública', section: 'inversion-publica' },
  'public_spending.csv': { label: 'gasto público consolidado', section: 'gasto-publico' },
  'reserve_requirements.csv': { label: 'encajes bancarios', section: 'tasas' },
  'treasury_maturities.csv': { label: 'vencimientos del Tesoro', section: 'vencimientos' },
  'treasury_liquidity.csv': { label: 'liquidez del Tesoro', section: 'liquidez-tesoro' },
  'reserves.csv': { label: 'reservas brutas', section: 'reservas' },
  'trade.csv': { label: 'comercio exterior', section: 'comercio' },
  'wages.csv': { label: 'salarios', section: 'salarios' }
};

function parseCsvLine(line) {
  const fields = [];
  let field = '';
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];
    if (character === '"') {
      if (quoted && line[index + 1] === '"') {
        field += '"';
        index += 1;
      } else {
        quoted = !quoted;
      }
    } else if (character === ',' && !quoted) {
      fields.push(field);
      field = '';
    } else {
      field += character;
    }
  }
  fields.push(field);
  return fields;
}

function economicRows(text, file = '') {
  const lines = text.trim().split(/\r?\n/).slice(1);
  return new Map(lines.filter(Boolean).map(line => {
    const fields = parseCsvLine(line);
    if (file === 'treasury_maturities.csv') {
      const key = [fields[0], fields[1], fields[2], fields[4], fields[7]].join('\u0000');
      return [key, fields.slice(0, 13).join('\u0000')];
    }
    return [
      `${fields[0]}\u0000${fields[1]}\u0000${fields[2]}`,
      fields.slice(0, 6).join('\u0000')
    ];
  }));
}

export function compareDataset(currentText, previousText, file = '') {
  const current = economicRows(currentText, file);
  const previous = economicRows(previousText, file);
  let added = 0;
  let revised = 0;
  let removed = 0;
  for (const [key, row] of current) {
    if (!previous.has(key)) added += 1;
    else if (previous.get(key) !== row) revised += 1;
  }
  for (const key of previous.keys()) if (!current.has(key)) removed += 1;
  return { added, revised, removed, changed: added + revised + removed > 0 };
}

export async function repositoryChanges(directory = resolve('data/processed')) {
  const files = (await readdir(directory)).filter(file => file.endsWith('.csv')).sort();
  const changes = [];
  for (const file of files) {
    const current = await readFile(resolve(directory, file), 'utf8');
    let previous = '';
    try {
      previous = execFileSync('git', ['show', `HEAD:data/processed/${file}`], {
        encoding: 'utf8', maxBuffer: 100 * 1024 * 1024
      });
    } catch {
      // A newly added dataset is entirely new economic content.
    }
    const comparison = compareDataset(current, previous, file);
    if (comparison.changed) changes.push({ file, ...(DATASETS[file] || { label: file.replace('.csv', ''), section: 'inicio' }), ...comparison });
  }
  return changes;
}

function listLabels(labels) {
  if (labels.length < 2) return labels[0] || 'indicadores económicos';
  return `${labels.slice(0, -1).join(', ')} y ${labels.at(-1)}`;
}

export function notificationPayload(changes) {
  const additions = changes.reduce((sum, change) => sum + change.added, 0);
  const labels = changes.map(change => change.label);
  const onlyRevisions = additions === 0;
  return {
    topic: 'economic-updates',
    title: onlyRevisions ? 'DatArg · Datos revisados' : 'DatArg · Nuevos datos',
    body: onlyRevisions ? `Se actualizaron ${listLabels(labels)}.` : `Ya están disponibles ${listLabels(labels)}.`,
    section: changes[0]?.section || 'inicio',
    datasets: changes.map(change => change.file.replace('.csv', '')).join(','),
    url: `https://dat-arg.vercel.app/#${changes[0]?.section || 'inicio'}`,
    additions,
    revisions: changes.reduce((sum, change) => sum + change.revised, 0),
    removals: changes.reduce((sum, change) => sum + change.removed, 0)
  };
}
