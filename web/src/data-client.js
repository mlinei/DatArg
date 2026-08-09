import { Capacitor } from '@capacitor/core';

const memory = new Map();
const DB_NAME = 'datarg-data-cache';
const STORE_NAME = 'datasets';
const nativeRuntime = Capacitor.isNativePlatform();
const configuredBase = import.meta.env.VITE_DATA_BASE_URL?.replace(/\/$/, '');
const DATA_BASE = configuredBase || (nativeRuntime ? 'https://dat-arg.vercel.app/api/data' : '/api/data');
const FALLBACK_DATA_BASE = nativeRuntime ? 'https://dat-arg.vercel.app/data' : '/data';
const REQUIRED_SERIES_BY_FILE = Object.freeze({
  'emae.csv': [
    'indec_emae_sector_manufacturing_index_jan_2020_100',
    'indec_emae_sector_manufacturing_yoy',
  ],
  'fx_intervention.csv': [
    'bcra_fx_futures_net_short_change',
    'bcra_fx_futures_net_short_position',
    'bcra_fx_intervention_adjusted_monthly',
  ],
  'gdp.csv': [
    'indec_private_consumption_sa_constant_2004',
    'indec_private_consumption_sa_qoq',
    'indec_private_consumption_gdp_share_quarterly',
  ],
  'public_debt.csv': [
    'bcra_interest_bearing_liabilities',
    'bcra_broad_financial_liabilities',
    'bcra_total_accounting_liabilities',
  ],
  'treasury_liquidity.csv': [
    'bcra_treasury_deposits_ars_daily',
    'bcra_treasury_deposits_ars_daily_change',
    'bcra_treasury_deposits_usd_daily',
    'bcra_treasury_deposits_usd_daily_change',
  ],
});

export function parseCSV(text) {
  const records = [];
  let record = [], cell = '', quoted = false;
  const source = text.replace(/^\uFEFF/, '').trim();
  for (let index = 0; index <= source.length; index += 1) {
    const character = source[index] ?? '\n';
    if (character === '"') {
      if (quoted && source[index + 1] === '"') { cell += '"'; index += 1; }
      else quoted = !quoted;
    } else if (character === ',' && !quoted) {
      record.push(cell); cell = '';
    } else if ((character === '\n' || character === '\r') && !quoted) {
      if (character === '\r' && source[index + 1] === '\n') index += 1;
      record.push(cell); cell = '';
      if (record.some(value => value !== '')) records.push(record);
      record = [];
    } else {
      cell += character;
    }
  }
  const headers = records.shift() || [];
  return records.map(cells => Object.fromEntries(headers.map((header, index) => [header, cells[index] ?? ''])));
}

function openDatabase() {
  if (!('indexedDB' in window)) return Promise.resolve(null);
  return new Promise(resolve => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE_NAME, { keyPath: 'file' });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => resolve(null);
  });
}

async function readStored(file) {
  const database = await openDatabase();
  if (!database) return null;
  return new Promise(resolve => {
    const request = database.transaction(STORE_NAME).objectStore(STORE_NAME).get(file);
    request.onsuccess = () => resolve(request.result?.text || null);
    request.onerror = () => resolve(null);
  });
}

async function store(file, text) {
  const database = await openDatabase();
  if (!database) return;
  await new Promise(resolve => {
    const request = database.transaction(STORE_NAME, 'readwrite').objectStore(STORE_NAME).put({ file, text, savedAt: Date.now() });
    request.onsuccess = request.onerror = () => resolve();
  });
}

function endpoint(file, base = DATA_BASE) {
  if (!/^[a-z0-9_-]+\.csv$/.test(file)) throw new Error(`Nombre de dataset inválido: ${file}`);
  return `${base}/${encodeURIComponent(file)}`;
}

async function download(file, base) {
  const response = await fetch(endpoint(file, base), { cache: 'no-store' });
  if (!response.ok) throw new Error(`${file}: HTTP ${response.status}`);
  const text = await response.text();
  const supportedHeader = text.startsWith('series_id,')
    || text.startsWith('snapshot_date,ticker,instrument_name,curve_type,');
  if (!supportedHeader || text.trim().split(/\r?\n/).length < 2) {
    throw new Error(`${file}: contenido inválido`);
  }
  return text;
}

function containsRequiredSeries(file, text) {
  const required = REQUIRED_SERIES_BY_FILE[file];
  if (!required) return true;
  const available = new Set(parseCSV(text).map(row => row.series_id));
  return required.every(seriesId => available.has(seriesId));
}

async function fetchText(file) {
  try {
    let text;
    let source = 'database';
    try {
      text = await download(file, DATA_BASE);
      if (!containsRequiredSeries(file, text)) {
        throw new Error(`${file}: la base todavía no contiene todas las series requeridas`);
      }
    } catch (databaseError) {
      console.warn(`Turso no disponible para ${file}; se usa el respaldo CSV`, databaseError);
      text = await download(file, FALLBACK_DATA_BASE);
      source = 'csv-fallback';
    }
    void store(file, text);
    window.dispatchEvent(new CustomEvent('datarg:data-source', { detail: { file, source } }));
    return text;
  } catch (error) {
    const stored = await readStored(file);
    if (!stored) throw error;
    window.dispatchEvent(new CustomEvent('datarg:data-source', { detail: { file, source: 'device' } }));
    return stored;
  }
}

export function loadDataset(file) {
  if (!memory.has(file)) {
    const request = fetchText(file).then(parseCSV).catch(error => {
      memory.delete(file);
      throw error;
    });
    memory.set(file, request);
  }
  return memory.get(file);
}

export function clearDatasetMemory() {
  memory.clear();
}

export const dataClientInfo = Object.freeze({ baseUrl: DATA_BASE, fallbackBaseUrl: FALLBACK_DATA_BASE, nativeRuntime });
