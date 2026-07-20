import { readFile } from 'node:fs/promises';
import { getApps, initializeApp } from 'firebase-admin/app';
import { getMessaging } from 'firebase-admin/messaging';

const source = process.argv[2];
if (!source) throw new Error('Uso: node send-data-notification.mjs <archivo.json>');

const payload = JSON.parse(await readFile(source, 'utf8'));
if (!getApps().length) initializeApp();

const messageId = await getMessaging().send({
  topic: payload.topic,
  notification: { title: payload.title, body: payload.body },
  data: {
    section: payload.section,
    datasets: payload.datasets,
    url: payload.url
  },
  android: {
    priority: 'high',
    notification: {
      channelId: 'datarg_updates',
      icon: 'ic_stat_datarg',
      color: '#59A7FF',
      sound: 'default'
    }
  },
  apns: {
    payload: {
      aps: { sound: 'default', 'thread-id': 'economic-updates' }
    }
  }
});

console.log(`Notificación enviada: ${messageId}`);
