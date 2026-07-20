import { writeFile } from 'node:fs/promises';
import { notificationPayload, repositoryChanges } from './data-changes.mjs';

const destination = process.argv[2];
if (!destination) throw new Error('Uso: node create-data-notification.mjs <archivo.json>');

const changes = await repositoryChanges();
if (!changes.length) process.exit(1);

const payload = notificationPayload(changes);
await writeFile(destination, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
console.log(`${changes.length} conjunto(s) con cambios económicos: ${changes.map(change => change.file).join(', ')}`);
