import 'dotenv/config';
import { defineConfig } from 'drizzle-kit';

const url = process.env.TURSO_DATABASE_URL;
const authToken = process.env.TURSO_AUTH_TOKEN;

if (!url) throw new Error('Falta TURSO_DATABASE_URL');
if (!authToken) throw new Error('Falta TURSO_AUTH_TOKEN');

export default defineConfig({
  dialect: 'turso',
  schema: './db/schema.ts',
  out: './drizzle',
  dbCredentials: { url, authToken },
  migrations: { table: '__drizzle_migrations', prefix: 'timestamp' },
  strict: true,
});
