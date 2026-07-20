import assert from 'node:assert/strict';
import test from 'node:test';
import { compareDataset, notificationPayload } from './data-changes.mjs';

const header = 'series_id,period,frequency,value,unit,status,source_id,retrieved_at';

test('detecta observaciones nuevas e ignora metadatos posteriores', () => {
  const previous = `${header}\nserie,2026-06,monthly,2.0,percent,official,source,old\n`;
  const current = `${header}\nserie,2026-06,monthly,2.0,percent,official,source,new\nserie,2026-07,monthly,1.9,percent,official,source,new\n`;
  assert.deepEqual(compareDataset(current, previous), { added: 1, revised: 0, removed: 0, changed: true });
});

test('distingue revisiones económicas', () => {
  const previous = `${header}\nserie,2026-06,monthly,2.0,percent,official,source,old\n`;
  const current = `${header}\nserie,2026-06,monthly,2.1,percent,official,source,new\n`;
  assert.deepEqual(compareDataset(current, previous), { added: 0, revised: 1, removed: 0, changed: true });
});

test('genera un destino de navegación válido', () => {
  const payload = notificationPayload([{ file: 'inflation.csv', label: 'inflación', section: 'precios', added: 1, revised: 0, removed: 0 }]);
  assert.equal(payload.topic, 'economic-updates');
  assert.equal(payload.section, 'precios');
  assert.equal(payload.url, 'https://dat-arg.vercel.app/#precios');
  assert.match(payload.body, /inflación/);
});
