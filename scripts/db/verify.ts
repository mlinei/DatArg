import 'dotenv/config';
import { createHash } from 'node:crypto';
import { readFile, readdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import { asc, eq } from 'drizzle-orm';
import { createDatabase } from '../../db/client.js';
import { datasets, observations, series, treasuryMaturities, yieldCurveInstruments } from '../../db/schema.js';
import { CSV_COLUMNS, MATURITY_CSV_COLUMNS, YIELD_CURVE_CSV_COLUMNS, parseCsv, parseMaturityCsv, parseYieldCurveCsv } from './csv.js';

const sourceDirectory = resolve(process.argv[2] || 'data/processed');
const files = (await readdir(sourceDirectory)).filter(file => file.endsWith('.csv')).sort();
const { client, db } = createDatabase();
let verifiedRows = 0;

// SQLite stores numeric observations as IEEE-754 REAL values. libSQL can return
// the same value with a slightly different decimal rendering, so strict
// equality between the CSV string and the database round-trip is too brittle.
// This tolerance is far below the precision of any published economic series,
// while still detecting material changes.
function numericValuesMatch(sourceValue: unknown, storedValue: unknown): boolean {
  const source = Number(sourceValue);
  const stored = Number(storedValue);
  if (!Number.isFinite(source) || !Number.isFinite(stored)) return source === stored;
  if (source === stored) return true;
  const scale = Math.max(1, Math.abs(source), Math.abs(stored));
  return Math.abs(source - stored) <= scale * 1e-12;
}

function mismatch(fileName: string, index: number, column: string, sourceValue: unknown, storedValue: unknown): Error {
  return new Error(`${fileName}: diferencia en fila ${index + 2}, columna ${column} (CSV=${sourceValue}, Turso=${storedValue})`);
}

try {
  for (const fileName of files) {
    const sourceText = await readFile(resolve(sourceDirectory, fileName), 'utf8');
    if (fileName === 'yield_curves.csv') {
      const sourceRows = parseYieldCurveCsv(sourceText);
      const [dataset] = await db.select().from(datasets).where(eq(datasets.fileName, fileName));
      if (!dataset || dataset.importStatus !== 'ready') throw new Error(`${fileName}: dataset ausente o incompleto`);
      const checksum = createHash('sha256').update(sourceText).digest('hex');
      if (dataset.rowCount !== sourceRows.length || dataset.contentSha256 !== checksum) throw new Error(`${fileName}: metadatos no coinciden`);
      const stored = await db.select({
        snapshot_date: yieldCurveInstruments.snapshotDate, ticker: yieldCurveInstruments.ticker,
        instrument_name: yieldCurveInstruments.instrumentName, curve_type: yieldCurveInstruments.curveType,
        instrument_type: yieldCurveInstruments.instrumentType, settlement_date: yieldCurveInstruments.settlementDate,
        maturity_date: yieldCurveInstruments.maturityDate, days_to_maturity: yieldCurveInstruments.daysToMaturity,
        price: yieldCurveInstruments.price, annual_yield: yieldCurveInstruments.annualYield,
        monthly_yield: yieldCurveInstruments.monthlyYield, duration_years: yieldCurveInstruments.durationYears,
        volume: yieldCurveInstruments.volume, status: yieldCurveInstruments.status, source_id: yieldCurveInstruments.sourceId,
        source_url: yieldCurveInstruments.sourceUrl, source_sha256: yieldCurveInstruments.sourceSha256,
        retrieved_at: yieldCurveInstruments.retrievedAt,
      }).from(yieldCurveInstruments).where(eq(yieldCurveInstruments.datasetId, dataset.id))
        .orderBy(asc(yieldCurveInstruments.snapshotDate), asc(yieldCurveInstruments.curveType), asc(yieldCurveInstruments.daysToMaturity), asc(yieldCurveInstruments.ticker));
      if (stored.length !== sourceRows.length) throw new Error(`${fileName}: cantidad de filas no coincide`);
      for (let index = 0; index < sourceRows.length; index += 1) for (const column of YIELD_CURVE_CSV_COLUMNS) {
        const numeric = ['days_to_maturity','price','annual_yield','monthly_yield','duration_years','volume'].includes(column);
        const sourceValue = sourceRows[index][column];
        const storedValue = stored[index][column];
        if (numeric ? !numericValuesMatch(sourceValue, storedValue) : sourceValue !== String(storedValue)) {
          throw mismatch(fileName, index, column, sourceValue, storedValue);
        }
      }
      verifiedRows += stored.length;
      console.log(`${fileName}: verificado`);
      continue;
    }
    if (fileName === 'treasury_maturities.csv') {
      const sourceRows = parseMaturityCsv(sourceText);
      const [dataset] = await db.select().from(datasets).where(eq(datasets.fileName, fileName));
      if (!dataset || dataset.importStatus !== 'ready') throw new Error(`${fileName}: dataset ausente o incompleto`);
      const checksum = createHash('sha256').update(sourceText).digest('hex');
      if (dataset.rowCount !== sourceRows.length || dataset.contentSha256 !== checksum) {
        throw new Error(`${fileName}: metadatos no coinciden`);
      }
      const stored = await db.select({
        series_id: treasuryMaturities.seriesId,
        snapshot_date: treasuryMaturities.snapshotDate,
        period: treasuryMaturities.period,
        frequency: treasuryMaturities.frequency,
        service_type: treasuryMaturities.serviceType,
        category: treasuryMaturities.category,
        detail_level: treasuryMaturities.detailLevel,
        source_row: treasuryMaturities.sourceRow,
        instrument: treasuryMaturities.instrument,
        value: treasuryMaturities.value,
        unit: treasuryMaturities.unit,
        status: treasuryMaturities.status,
        source_id: treasuryMaturities.sourceId,
        source_url: treasuryMaturities.sourceUrl,
        source_sha256: treasuryMaturities.sourceSha256,
        retrieved_at: treasuryMaturities.retrievedAt,
      }).from(treasuryMaturities)
        .where(eq(treasuryMaturities.datasetId, dataset.id))
        .orderBy(
          asc(treasuryMaturities.snapshotDate), asc(treasuryMaturities.period),
          asc(treasuryMaturities.serviceType), asc(treasuryMaturities.sourceRow),
        );
      if (stored.length !== sourceRows.length) throw new Error(`${fileName}: cantidad de filas no coincide`);
      for (let index = 0; index < sourceRows.length; index += 1) {
        for (const column of MATURITY_CSV_COLUMNS) {
          const sourceValue = sourceRows[index][column];
          const storedValue = String(stored[index][column]);
          const matches = ['value', 'source_row'].includes(column)
            ? numericValuesMatch(sourceValue, storedValue)
            : sourceValue === storedValue;
          if (!matches) throw mismatch(fileName, index, column, sourceValue, storedValue);
        }
      }
      verifiedRows += stored.length;
      console.log(`${fileName}: verificado`);
      continue;
    }
    const sourceRows = parseCsv(sourceText);
    const [dataset] = await db.select().from(datasets).where(eq(datasets.fileName, fileName));
    if (!dataset) throw new Error(`${fileName}: dataset ausente en Turso`);
    if (dataset.importStatus !== 'ready') throw new Error(`${fileName}: importación incompleta`);
    if (dataset.rowCount !== sourceRows.length) throw new Error(`${fileName}: row_count no coincide`);
    const checksum = createHash('sha256').update(sourceText).digest('hex');
    if (dataset.contentSha256 !== checksum) throw new Error(`${fileName}: checksum no coincide`);

    const stored = await db.select({
      series_id: observations.seriesId,
      period: observations.period,
      frequency: observations.frequency,
      value: observations.value,
      unit: observations.unit,
      status: observations.status,
      source_id: observations.sourceId,
      source_url: observations.sourceUrl,
      source_sha256: observations.sourceSha256,
      retrieved_at: observations.retrievedAt,
    }).from(observations)
      .innerJoin(series, eq(observations.seriesId, series.id))
      .where(eq(series.datasetId, dataset.id))
      .orderBy(asc(observations.seriesId), asc(observations.period));

    const normalizedSource = [...sourceRows].sort((a, b) =>
      a.series_id.localeCompare(b.series_id) || a.period.localeCompare(b.period)
    );
    for (let index = 0; index < normalizedSource.length; index += 1) {
      const sourceRow = normalizedSource[index];
      const storedRow = stored[index];
      for (const column of CSV_COLUMNS) {
        const sourceValue = sourceRow[column];
        const storedValue = String(storedRow[column]);
        const matches = column === 'value'
          ? numericValuesMatch(sourceValue, storedValue)
          : sourceValue === storedValue;
        if (!matches) {
          throw mismatch(fileName, index, column, sourceValue, storedValue);
        }
      }
    }
    verifiedRows += stored.length;
    console.log(`${fileName}: verificado`);
  }
  console.log(`${files.length} datasets y ${verifiedRows} observaciones verificados`);
} finally {
  client.close();
}
