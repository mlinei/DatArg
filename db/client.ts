import { createClient } from '@libsql/client';
import { drizzle } from 'drizzle-orm/libsql';
import * as schema from './schema';

export function databaseConfig() {
  const url = process.env.TURSO_DATABASE_URL;
  const authToken = process.env.TURSO_AUTH_TOKEN;
  if (!url) throw new Error('Falta TURSO_DATABASE_URL');
  if (!authToken) throw new Error('Falta TURSO_AUTH_TOKEN');
  return { url, authToken };
}

export function createDatabase() {
  const client = createClient(databaseConfig());
  return { client, db: drizzle(client, { schema }) };
}
