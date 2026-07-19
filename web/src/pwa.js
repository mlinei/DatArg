function standalone() {
  return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
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
  let installPrompt;

  const updateConnection = () => {
    if (navigator.onLine) announce('Conexión restablecida');
    else announce('Sin conexión · usando los últimos datos guardados', true);
  };
  window.addEventListener('online', updateConnection);
  window.addEventListener('offline', updateConnection);
  if (!navigator.onLine) updateConnection();

  window.addEventListener('datarg:data-source', event => {
    if (event.detail?.source === 'device') announce('Mostrando la última copia guardada en este dispositivo', true);
  });

  if ('serviceWorker' in navigator && import.meta.env.PROD) {
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
