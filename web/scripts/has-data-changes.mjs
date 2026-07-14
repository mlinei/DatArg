import { execFileSync } from 'node:child_process';
import { readdir, readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const directory = resolve('data/processed');
const files = (await readdir(directory)).filter(file => file.endsWith('.csv')).sort();
const economicFields = text => text.trim().split(/\r?\n/).map(line => line.split(',').slice(0, 6).join(',')).join('\n');

let changed = false;
for (const file of files) {
  const current = economicFields(await readFile(resolve(directory, file), 'utf8'));
  let previous;
  try {
    previous = economicFields(execFileSync('git', ['show', `HEAD:data/processed/${file}`], { encoding: 'utf8' }));
  } catch {
    changed = true;
    break;
  }
  if (current !== previous) {
    changed = true;
    break;
  }
}

process.exit(changed ? 0 : 1);
