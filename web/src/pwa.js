import { Browser } from '@capacitor/browser';
import { Capacitor, SystemBars, SystemBarsStyle } from '@capacitor/core';
import { Network } from '@capacitor/network';
import { StatusBar, Style } from '@capacitor/status-bar';

function standalone() {
  return Capacitor.isNativePlatform() || window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
}

function connectionBanner() {
  const banner = document.createElement('div');
  banner.className = 'connection-status';
  banner.setAttribute('role', 'status');
  banner.setAttribute('aria-live', 'polite');
  document.body.append(banner);
  let timer;
  return (message, persistent = false) => {
    window.clearTimeout(timer);
    banner.textContent = message;
    banner.classList.add('show');
    if (!persistent) timer = window.setTimeout(() => banner.classList.remove('show'), 3200);
  };
}

export function setupPWA() {
  const announce = connectionBanner();
  const installButton = document.querySelector('#install-app');
  const nativeRuntime = Capacitor.isNativePlatform();
  let installPrompt;

  const updateConnection = (connected = navigator.onLine) => {
    if (connected) announce('Conexión restablecida');
    else announce('Sin conexión · usando los últimos datos guardados', true);
  };

  if (nativeRuntime) {
    document.documentElement.classList.add('native-app');
    if (Capacitor.getPlatform() === 'android') {
      void SystemBars.setStyle({ style: SystemBarsStyle.Dark }).catch(() => {});
    } else {
      void StatusBar.setStyle({ style: Style.Light }).catch(() => {});
      void StatusBar.setBackgroundColor({ color: '#06101f' }).catch(() => {});
      void StatusBar.setOverlaysWebView({ overlay: false }).catch(() => {});
    }
    void Network.getStatus().then(status => updateConnection(status.connected));
    void Network.addListener('networkStatusChange', status => updateConnection(status.connected));
    document.addEventListener('click', event => {
      const target = event.target instanceof Element ? event.target : null;
      const link = target?.closest('a[target="_blank"]');
      if (!link || !/^https?:/.test(link.href)) return;
      event.preventDefault();
      void Browser.open({ url: link.href });
    });
  } else {
    window.addEventListener('online', () => updateConnection(true));
    window.addEventListener('offline', () => updateConnection(false));
    if (!navigator.onLine) updateConnection(false);
  }

  window.addEventListener('datarg:data-source', event => {
    if (event.detail?.source === 'device') announce('Mostrando la última copia guardada en este dispositivo', true);
  });

  if (!nativeRuntime && 'serviceWorker' in navigator && import.meta.env.PROD) {
    window.addEventListener('load', () => navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(() => {}));
  }

  if (!installButton || standalone()) return;
  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    installPrompt = event;
    installButton.hidden = false;
  });
  window.addEventListener('appinstalled', () => {
    installPrompt = null;
    installButton.hidden = true;
    announce('DatArg quedó instalada');
  });

  const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
  if (isIOS) installButton.hidden = false;
  installButton.addEventListener('click', async () => {
    if (installPrompt) {
      await installPrompt.prompt();
      await installPrompt.userChoice;
      installPrompt = null;
      installButton.hidden = true;
      return;
    }
    if (isIOS) announce('En iPhone: tocá Compartir y luego “Agregar a inicio”', true);
  });
}
