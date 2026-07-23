import { asc, eq } from 'drizzle-orm';
import { createDatabase } from '../../db/client.js';
import { datasets, observations, series } from '../../db/schema.js';
import { rowsToCsv, type CsvRow } from '../../scripts/db/csv.js';

const FILE_PATTERN = /^[a-z0-9_-]+\.csv$/;
const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export function OPTIONS() {
  return new Response(null, { status: 204, headers: CORS_HEADERS });
}

export async function GET(request: Request) {
  const fileName = decodeURIComponent(new URL(request.url).pathname.split('/').at(-1) || '');
  if (!FILE_PATTERN.test(fileName)) {
    return Response.json({ error: 'Dataset inválido' }, { status: 400, headers: CORS_HEADERS });
  }

  let client: ReturnType<typeof createDatabase>['client'] | undefined;
  try {
    const database = createDatabase();
    client = database.client;
    const [dataset] = await database.db.select().from(datasets).where(eq(datasets.fileName, fileName));
    if (!dataset) {
      return Response.json({ error: 'Dataset inexistente' }, { status: 404, headers: CORS_HEADERS });
    }
    if (dataset.importStatus !== 'ready') {
      return Response.json({ error: 'Dataset en actualización' }, {
        status: 503,
        headers: { ...CORS_HEADERS, 'Cache-Control': 'no-store', 'Retry-After': '60' },
      });
    }

    const stored = await database.db.select({
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

    return new Response(rowsToCsv(stored.map(row =>
      Object.fromEntries(Object.entries(row).map(([key, value]) => [key, String(value)]))
    ) as CsvRow[]), {
      headers: {
        ...CORS_HEADERS,
        'Content-Type': 'text/csv; charset=utf-8',
        'Cache-Control': 'public, max-age=300, s-maxage=300, stale-while-revalidate=86400',
        ETag: `"${dataset.contentSha256}"`,
      },
    });
  } catch (error) {
    console.error('No se pudo consultar Turso', error);
    return Response.json({ error: 'Base de datos temporalmente no disponible' }, {
      status: 503,
      headers: { ...CORS_HEADERS, 'Cache-Control': 'no-store' },
    });
  } finally {
    client?.close();
  }
}

export async function HEAD(request: Request) {
  const response = await GET(request);
  return new Response(null, { status: response.status, headers: response.headers });
}
