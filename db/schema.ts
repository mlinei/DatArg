import { index, integer, primaryKey, real, sqliteTable, text, uniqueIndex } from 'drizzle-orm/sqlite-core';

export const datasets = sqliteTable('datasets', {
  id: text('id').primaryKey(),
  fileName: text('file_name').notNull(),
  contentSha256: text('content_sha256').notNull(),
  rowCount: integer('row_count').notNull(),
  importStatus: text('import_status', { enum: ['importing', 'ready'] }).notNull().default('ready'),
  updatedAt: text('updated_at').notNull(),
}, table => [
  uniqueIndex('datasets_file_name_unique').on(table.fileName),
]);

export const series = sqliteTable('series', {
  id: text('id').primaryKey(),
  datasetId: text('dataset_id')
    .notNull()
    .references(() => datasets.id, { onDelete: 'cascade', onUpdate: 'cascade' }),
  frequency: text('frequency').notNull(),
  unit: text('unit').notNull(),
  sourceId: text('source_id').notNull(),
  sourceUrl: text('source_url').notNull(),
  createdAt: text('created_at').notNull(),
  updatedAt: text('updated_at').notNull(),
}, table => [
  index('series_dataset_id_idx').on(table.datasetId),
]);

export const observations = sqliteTable('observations', {
  seriesId: text('series_id')
    .notNull()
    .references(() => series.id, { onDelete: 'cascade', onUpdate: 'cascade' }),
  period: text('period').notNull(),
  frequency: text('frequency').notNull(),
  value: real('value').notNull(),
  unit: text('unit').notNull(),
  status: text('status').notNull(),
  sourceId: text('source_id').notNull(),
  sourceUrl: text('source_url').notNull(),
  sourceSha256: text('source_sha256').notNull(),
  retrievedAt: text('retrieved_at').notNull(),
  ingestedAt: text('ingested_at').notNull(),
}, table => [
  primaryKey({ name: 'observations_series_period_pk', columns: [table.seriesId, table.period] }),
  index('observations_period_idx').on(table.period),
  index('observations_retrieved_at_idx').on(table.retrievedAt),
]);
