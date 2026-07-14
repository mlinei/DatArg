import { cp, mkdir, readdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const source = resolve('data/processed');
const target = resolve('web/public/data');
await mkdir(target, { recursive: true });
const files = (await readdir(source)).filter((file) => file.endsWith('.csv'));
for (const file of files) await cp(resolve(source, file), resolve(target, file));
await writeFile(resolve(target, 'manifest.json'), JSON.stringify({ files, generatedAt: new Date().toISOString() }, null, 2));
console.log(`Sincronizados ${files.length} datasets.`);
