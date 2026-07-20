import { readFile } from 'node:fs/promises';
import { cert, getApps, initializeApp } from 'firebase-admin/app';
import { getMessaging } from 'firebase-admin/messaging';

const source = process.argv[2];
if (!source) throw new Error('Uso: node send-data-notification.mjs <archivo.json>');
if (!process.env.FIREBASE_SERVICE_ACCOUNT_JSON) throw new Error('Falta FIREBASE_SERVICE_ACCOUNT_JSON');

const payload = JSON.parse(await readFile(source, 'utf8'));
const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT_JSON);
if (!getApps().length) initializeApp({ credential: cert(serviceAccount) });

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
