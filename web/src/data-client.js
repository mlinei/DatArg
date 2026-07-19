import { Capacitor } from '@capacitor/core';

const memory = new Map();
const DB_NAME = 'datarg-data-cache';
const STORE_NAME = 'datasets';
const nativeRuntime = Capacitor.isNativePlatform();
const configuredBase = import.meta.env.VITE_DATA_BASE_URL?.replace(/\/$/, '');
const DATA_BASE = configuredBase || (nativeRuntime ? 'https://dat-arg.vercel.app/data' : '/data');

export function parseCSV(text) {
  const lines = text.trim().split(/\r?\n/);
  const headers = lines.shift()?.split(',') || [];
  return lines.map(line => {
    const cells = line.split(',');
    return Object.fromEntries(headers.map((header, index) => [header, cells[index]]));
  });
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

function endpoint(file) {
  if (!/^[a-z0-9_-]+\.csv$/.test(file)) throw new Error(`Nombre de dataset inválido: ${file}`);
  return `${DATA_BASE}/${encodeURIComponent(file)}`;
}

async function fetchText(file) {
  try {
    const response = await fetch(endpoint(file), { cache: 'no-store' });
    if (!response.ok) throw new Error(`${file}: HTTP ${response.status}`);
    const text = await response.text();
    if (!text.startsWith('series_id,') || text.trim().split(/\r?\n/).length < 2) throw new Error(`${file}: contenido inválido`);
    void store(file, text);
    window.dispatchEvent(new CustomEvent('datarg:data-source', { detail: { file, source: 'network' } }));
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

export const dataClientInfo = Object.freeze({ baseUrl: DATA_BASE, nativeRuntime });
