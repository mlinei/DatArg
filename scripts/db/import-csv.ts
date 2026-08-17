import 'dotenv/config';
import { createHash } from 'node:crypto';
import { readFile, readdir } from 'node:fs/promises';
import { basename, resolve } from 'node:path';
import { eq, sql } from 'drizzle-orm';
import { createDatabase } from '../../db/client.js';
import { datasets, observations, series, treasuryMaturities, yieldCurveInstruments } from '../../db/schema.js';
import { parseCsv, parseMaturityCsv, parseYieldCurveCsv } from './csv.js';

const sourceDirectory = resolve(process.argv[2] || 'data/processed');
const requestedFiles = process.argv.slice(3);
const availableFiles = (await readdir(sourceDirectory))
  .filter(file => file.endsWith('.csv'))
  .sort();
const files = requestedFiles.length
  ? requestedFiles.map(file => basename(file)).filter(file => availableFiles.includes(file))
  : availableFiles;

if (!files.length) throw new Error('No se encontraron datasets CSV para importar');

const { client, db } = createDatabase();
const importedAt = new Date().toISOString();

const INSERT_CHUNK_SIZE = 250;
const DELETE_CHUNK_SIZE = 500;

function observationKey(row: { seriesId: string; period: string } | { series_id: string; period: string }) {
  return 'seriesId' in row ? `${row.seriesId}|${row.period}` : `${row.series_id}|${row.period}`;
}

try {
  for (const fileName of files) {
    const datasetId = fileName.replace(/\.csv$/, '');
    const file = await readFile(resolve(sourceDirectory, fileName), 'utf8');
    const checksum = createHash('sha256').update(file).digest('hex');

    const [existing] = await db
      .select({ contentSha256: datasets.contentSha256, importStatus: datasets.importStatus })
      .from(datasets)
      .where(eq(datasets.id, datasetId));

    if (existing && existing.contentSha256 === checksum && existing.importStatus === 'ready') {
      console.log(`${fileName}: sin cambios, se omite`);
      continue;
    }

    if (fileName === 'yield_curves.csv') {
      const rows = parseYieldCurveCsv(file);
      if (!rows.length) throw new Error(`${fileName} no contiene instrumentos`);
      const datasetStatement = db.insert(datasets).values({
        id: datasetId, fileName, contentSha256: checksum, rowCount: rows.length,
        importStatus: 'importing', updatedAt: importedAt,
      }).onConflictDoUpdate({
        target: datasets.id,
        set: { fileName, contentSha256: checksum, rowCount: rows.length, importStatus: 'importing', updatedAt: importedAt },
      });
      await db.batch([datasetStatement, db.delete(yieldCurveInstruments).where(eq(yieldCurveInstruments.datasetId, datasetId))]);
      for (let offset = 0; offset < rows.length; offset += INSERT_CHUNK_SIZE) {
        const chunk = rows.slice(offset, offset + INSERT_CHUNK_SIZE).map(row => ({
          datasetId, snapshotDate: row.snapshot_date, ticker: row.ticker, instrumentName: row.instrument_name,
          curveType: row.curve_type as 'nominal' | 'cer', instrumentType: row.instrument_type,
          settlementDate: row.settlement_date, maturityDate: row.maturity_date, daysToMaturity: Number(row.days_to_maturity),
          price: Number(row.price), annualYield: Number(row.annual_yield), monthlyYield: Number(row.monthly_yield),
          durationYears: Number(row.duration_years), volume: Number(row.volume), status: row.status,
          sourceId: row.source_id, sourceUrl: row.source_url, sourceSha256: row.source_sha256,
          retrievedAt: row.retrieved_at, ingestedAt: importedAt,
        }));
        if (chunk.some(row => !Number.isInteger(row.daysToMaturity) || [row.price, row.annualYield, row.monthlyYield, row.durationYears, row.volume].some(value => !Number.isFinite(value)))) {
          throw new Error(`${fileName} contiene valores no numéricos`);
        }
        await db.insert(yieldCurveInstruments).values(chunk);
      }
      const [{ count }] = await db.select({ count: sql<number>`count(*)` }).from(yieldCurveInstruments).where(eq(yieldCurveInstruments.datasetId, datasetId));
      if (Number(count) !== rows.length) throw new Error(`${fileName}: Turso tiene ${count} filas y el CSV ${rows.length}`);
      await db.update(datasets).set({ contentSha256: checksum, rowCount: rows.length, importStatus: 'ready', updatedAt: importedAt }).where(eq(datasets.id, datasetId));
      console.log(`${fileName}: ${rows.length} instrumentos`);
      continue;
    }

    if (fileName === 'treasury_maturities.csv') {
      const rows = parseMaturityCsv(file);
      if (!rows.length) throw new Error(`${fileName} no contiene vencimientos`);
      const datasetStatement = db.insert(datasets).values({
        id: datasetId, fileName, contentSha256: checksum, rowCount: rows.length,
        importStatus: 'importing', updatedAt: importedAt,
      }).onConflictDoUpdate({
        target: datasets.id,
        set: { fileName, contentSha256: checksum, rowCount: rows.length, importStatus: 'importing', updatedAt: importedAt },
      });
      await db.batch([
        datasetStatement,
        db.delete(treasuryMaturities).where(eq(treasuryMaturities.datasetId, datasetId)),
      ]);
      for (let offset = 0; offset < rows.length; offset += INSERT_CHUNK_SIZE) {
        const chunk = rows.slice(offset, offset + INSERT_CHUNK_SIZE).map(row => ({
          datasetId,
          seriesId: row.series_id,
          snapshotDate: row.snapshot_date,
          period: row.period,
          frequency: row.frequency,
          serviceType: row.service_type as 'capital' | 'interest',
          category: row.category,
          detailLevel: row.detail_level as 'total' | 'term' | 'category' | 'detail',
          sourceRow: Number(row.source_row),
          instrument: row.instrument,
          value: Number(row.value),
          unit: row.unit,
          status: row.status,
          sourceId: row.source_id,
          sourceUrl: row.source_url,
          sourceSha256: row.source_sha256,
          retrievedAt: row.retrieved_at,
          ingestedAt: importedAt,
        }));
        if (chunk.some(row => !Number.isFinite(row.value) || !Number.isInteger(row.sourceRow))) {
          throw new Error(`${fileName} contiene valores no numéricos`);
        }
        await db.insert(treasuryMaturities).values(chunk);
      }
      const [{ count }] = await db.select({ count: sql<number>`count(*)` })
        .from(treasuryMaturities).where(eq(treasuryMaturities.datasetId, datasetId));
      if (Number(count) !== rows.length) throw new Error(`${fileName}: Turso tiene ${count} filas y el CSV ${rows.length}`);
      await db.update(datasets).set({ contentSha256: checksum, rowCount: rows.length, importStatus: 'ready', updatedAt: importedAt }).where(eq(datasets.id, datasetId));
      console.log(`${fileName}: ${rows.length} vencimientos`);
      continue;
    }

    const rows = parseCsv(file);
    if (!rows.length) throw new Error(`${fileName} no contiene observaciones`);

    const canonicalSeries = new Map<string, (typeof rows)[number]>();
    rows.forEach(row => canonicalSeries.set(row.series_id, row));

    await db.insert(datasets).values({
      id: datasetId,
      fileName,
      contentSha256: checksum,
      rowCount: rows.length,
      importStatus: 'importing',
      updatedAt: importedAt,
    }).onConflictDoUpdate({
      target: datasets.id,
      set: {
        fileName,
        contentSha256: checksum,
        rowCount: rows.length,
        importStatus: 'importing',
        updatedAt: importedAt,
      },
    });

    const seriesStatements = [...canonicalSeries.values()].map(row =>
      db.insert(series).values({
        id: row.series_id,
        datasetId,
        frequency: row.frequency,
        unit: row.unit,
        sourceId: row.source_id,
        sourceUrl: row.source_url,
        createdAt: importedAt,
        updatedAt: importedAt,
      }).onConflictDoUpdate({
        target: series.id,
        set: {
          datasetId,
          frequency: row.frequency,
          unit: row.unit,
          sourceId: row.source_id,
          sourceUrl: row.source_url,
          updatedAt: importedAt,
        },
      })
    );
    if (seriesStatements.length) await db.batch(seriesStatements);

    const stored = await db.select({
      seriesId: observations.seriesId,
      period: observations.period,
      frequency: observations.frequency,
      value: observations.value,
      unit: observations.unit,
      status: observations.status,
      sourceId: observations.sourceId,
      sourceUrl: observations.sourceUrl,
      sourceSha256: observations.sourceSha256,
      retrievedAt: observations.retrievedAt,
    })
      .from(observations)
      .innerJoin(series, eq(observations.seriesId, series.id))
      .where(eq(series.datasetId, datasetId));

    const storedMap = new Map(stored.map(s => [observationKey(s), s]));
    const csvKeySet = new Set(rows.map(row => observationKey(row)));

    const toDelete: Array<{ seriesId: string; period: string }> = [];
    for (const storedRow of stored) {
      const key = observationKey(storedRow);
      if (!csvKeySet.has(key)) {
        toDelete.push({ seriesId: storedRow.seriesId, period: storedRow.period });
      }
    }

    const toUpsert: typeof rows = [];
    for (const row of rows) {
      const key = observationKey(row);
      const storedRow = storedMap.get(key);
      if (!storedRow) {
        toUpsert.push(row);
        continue;
      }
      const changed =
        storedRow.frequency !== row.frequency ||
        storedRow.value !== Number(row.value) ||
        storedRow.unit !== row.unit ||
        storedRow.status !== row.status ||
        storedRow.sourceId !== row.source_id ||
        storedRow.sourceUrl !== row.source_url ||
        storedRow.sourceSha256 !== row.source_sha256 ||
        storedRow.retrievedAt !== row.retrieved_at;
      if (changed) toUpsert.push(row);
    }

    for (let offset = 0; offset < toDelete.length; offset += DELETE_CHUNK_SIZE) {
      const chunk = toDelete.slice(offset, offset + DELETE_CHUNK_SIZE);
      const tuples = sql.join(chunk.map(r => sql`(${r.seriesId}, ${r.period})`), sql`, `);
      await db.delete(observations).where(sql`(${observations.seriesId}, ${observations.period}) IN (${tuples})`);
    }

    for (let offset = 0; offset < toUpsert.length; offset += INSERT_CHUNK_SIZE) {
      const chunk = toUpsert.slice(offset, offset + INSERT_CHUNK_SIZE).map(row => ({
        seriesId: row.series_id,
        period: row.period,
        frequency: row.frequency,
        value: Number(row.value),
        unit: row.unit,
        status: row.status,
        sourceId: row.source_id,
        sourceUrl: row.source_url,
        sourceSha256: row.source_sha256,
        retrievedAt: row.retrieved_at,
        ingestedAt: importedAt,
      }));
      if (chunk.some(row => !Number.isFinite(row.value))) throw new Error(`${fileName} contiene valores no numéricos`);
      await db.insert(observations).values(chunk).onConflictDoUpdate({
        target: [observations.seriesId, observations.period],
        set: {
          frequency: sql`excluded.frequency`,
          value: sql`excluded.value`,
          unit: sql`excluded.unit`,
          status: sql`excluded.status`,
          sourceId: sql`excluded.source_id`,
          sourceUrl: sql`excluded.source_url`,
          sourceSha256: sql`excluded.source_sha256`,
          retrievedAt: sql`excluded.retrieved_at`,
          ingestedAt: importedAt,
        },
      });
    }

    const [{ count }] = await db.select({ count: sql<number>`count(*)` })
      .from(observations)
      .innerJoin(series, eq(observations.seriesId, series.id))
      .where(eq(series.datasetId, datasetId));
    if (Number(count) !== rows.length) {
      throw new Error(`${fileName}: Turso tiene ${count} filas y el CSV ${rows.length}`);
    }

    await db.update(datasets).set({
      contentSha256: checksum,
      rowCount: rows.length,
      importStatus: 'ready',
      updatedAt: importedAt,
    }).where(eq(datasets.id, datasetId));

    console.log(`${fileName}: ${rows.length} observaciones, ${canonicalSeries.size} series, +${toUpsert.length} escritas, -${toDelete.length} eliminadas`);
  }
} finally {
  client.close();
}
