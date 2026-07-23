import 'dotenv/config';
import { createHash } from 'node:crypto';
import { readFile, readdir } from 'node:fs/promises';
import { basename, resolve } from 'node:path';
import { eq, sql } from 'drizzle-orm';
import { createDatabase } from '../../db/client';
import { datasets, observations, series } from '../../db/schema';
import { parseCsv } from './csv';

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

try {
  for (const fileName of files) {
    const datasetId = fileName.replace(/\.csv$/, '');
    const file = await readFile(resolve(sourceDirectory, fileName), 'utf8');
    const rows = parseCsv(file);
    if (!rows.length) throw new Error(`${fileName} no contiene observaciones`);

    const checksum = createHash('sha256').update(file).digest('hex');
    const canonicalSeries = new Map<string, (typeof rows)[number]>();
    rows.forEach(row => canonicalSeries.set(row.series_id, row));

    const datasetStatement = db.insert(datasets).values({
      id: datasetId,
      fileName,
      contentSha256: checksum,
      rowCount: rows.length,
      importStatus: 'importing',
      updatedAt: importedAt,
    }).onConflictDoUpdate({
      target: datasets.id,
      set: { fileName, importStatus: 'importing', updatedAt: importedAt },
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

    await db.batch([
      datasetStatement,
      ...seriesStatements,
      db.delete(observations).where(
        sql`${observations.seriesId} in (select ${series.id} from ${series} where ${series.datasetId} = ${datasetId})`
      ),
    ] as [typeof datasetStatement, ...typeof seriesStatements]);

    for (let offset = 0; offset < rows.length; offset += 250) {
      const chunk = rows.slice(offset, offset + 250).map(row => ({
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
    console.log(`${fileName}: ${rows.length} observaciones, ${canonicalSeries.size} series`);
  }
} finally {
  client.close();
}
