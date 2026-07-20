import { FirebaseMessaging, Importance, Visibility } from '@capacitor-firebase/messaging';
import { Capacitor } from '@capacitor/core';
import { sections } from './config.js';

const TOPIC = 'economic-updates';
const CHANNEL_ID = 'datarg_updates';
const STORAGE_KEY = 'datarg:notifications-enabled';
const validSections = new Set(sections.map(section => section.id));

function notificationSection(notification) {
  const data = notification?.data;
  if (!data || typeof data !== 'object') return 'inicio';
  const section = String(data.section || '').replace(/^#/, '');
  return validSections.has(section) ? section : 'inicio';
}

function openNotification(notification) {
  const section = notificationSection(notification);
  window.location.hash = section;
  window.setTimeout(() => document.getElementById(section)?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 80);
}

export async function setupNotifications({ announce = () => {} } = {}) {
  const button = document.querySelector('#notification-toggle');
  if (!button || !Capacitor.isNativePlatform()) return;

  button.hidden = false;
  let enabled = localStorage.getItem(STORAGE_KEY) === 'true';

  const paint = () => {
    button.textContent = enabled ? 'Alertas activadas ✓' : 'Activar alertas';
    button.classList.toggle('active', enabled);
    button.setAttribute('aria-pressed', String(enabled));
  };

  const createAndroidChannel = async () => {
    if (Capacitor.getPlatform() !== 'android') return;
    await FirebaseMessaging.createChannel({
      id: CHANNEL_ID,
      name: 'Nuevos datos económicos',
      description: 'Avisos cuando DatArg incorpora un dato nuevo o una revisión.',
      importance: Importance.High,
      visibility: Visibility.Public,
      vibration: true,
      lights: true,
      lightColor: '#59A7FF'
    });
  };

  const subscribe = async (requestPermission = false) => {
    let permission = await FirebaseMessaging.checkPermissions();
    if (requestPermission && permission.receive === 'prompt') permission = await FirebaseMessaging.requestPermissions();
    if (permission.receive !== 'granted') throw new Error('permission-denied');
    await createAndroidChannel();
    await FirebaseMessaging.getToken();
    await FirebaseMessaging.subscribeToTopic({ topic: TOPIC });
  };

  await FirebaseMessaging.addListener('notificationActionPerformed', event => openNotification(event.notification));
  await FirebaseMessaging.addListener('notificationReceived', event => {
    const message = [event.notification?.title, event.notification?.body].filter(Boolean).join(' · ');
    if (message) announce(message, true);
  });
  await FirebaseMessaging.addListener('tokenReceived', () => {
    if (localStorage.getItem(STORAGE_KEY) === 'true') {
      void FirebaseMessaging.subscribeToTopic({ topic: TOPIC }).catch(() => {});
    }
  });

  paint();
  if (enabled) {
    try {
      await subscribe(false);
    } catch {
      enabled = false;
      localStorage.removeItem(STORAGE_KEY);
      paint();
    }
  }

  button.addEventListener('click', async () => {
    button.disabled = true;
    try {
      if (enabled) {
        await FirebaseMessaging.unsubscribeFromTopic({ topic: TOPIC });
        enabled = false;
        localStorage.removeItem(STORAGE_KEY);
        announce('Alertas desactivadas');
      } else {
        await subscribe(true);
        enabled = true;
        localStorage.setItem(STORAGE_KEY, 'true');
        announce('Te avisaremos cuando haya nuevos datos');
      }
    } catch (error) {
      if (error?.message === 'permission-denied') announce('Las notificaciones están desactivadas en los ajustes del teléfono', true);
      else announce('No se pudieron configurar las alertas. Intentá nuevamente.', true);
    } finally {
      button.disabled = false;
      paint();
    }
  });
}
