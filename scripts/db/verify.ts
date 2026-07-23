import 'dotenv/config';
import { createHash } from 'node:crypto';
import { readFile, readdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import { asc, eq } from 'drizzle-orm';
import { createDatabase } from '../../db/client';
import { datasets, observations, series } from '../../db/schema';
import { CSV_COLUMNS, parseCsv } from './csv';

const sourceDirectory = resolve(process.argv[2] || 'data/processed');
const files = (await readdir(sourceDirectory)).filter(file => file.endsWith('.csv')).sort();
const { client, db } = createDatabase();
let verifiedRows = 0;

try {
  for (const fileName of files) {
    const sourceText = await readFile(resolve(sourceDirectory, fileName), 'utf8');
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
          ? Number(sourceValue) === Number(storedValue)
          : sourceValue === storedValue;
        if (!matches) {
          throw new Error(`${fileName}: diferencia en fila ${index + 2}, columna ${column}`);
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
