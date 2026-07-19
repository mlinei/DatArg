# Base móvil de DatArg

DatArg mantiene una sola aplicación web y una sola fuente de datos. La primera capa móvil se implementa como PWA instalable y deja preparado el acceso a los mismos CSV desde un contenedor nativo futuro.

## Componentes

- `web/public/manifest.webmanifest`: nombre, colores, iconos y accesos directos de la aplicación.
- `web/public/sw.js`: conserva la interfaz y los datos consultados para permitir una lectura sin conexión.
- `web/src/data-client.js`: usa `/data` en la web y `https://dat-arg.vercel.app/data` en un entorno Capacitor. Guarda la última versión válida de cada CSV en IndexedDB.
- `web/src/pwa.js`: registra el service worker sólo en compilaciones de producción, expone la instalación y comunica el estado de conexión.
- `vercel.json`: habilita lectura de los CSV desde el futuro contenedor móvil y controla la actualización del service worker.

## Estrategia de publicación segura

La versión web anterior al trabajo móvil quedó marcada en Git como `pre-mobile-v1`. Cada etapa móvil se compila, se prueba en una URL de preview y se integra a `main` sólo después de validar la web. Si hubiera una regresión, ese tag permite identificar y restaurar exactamente la versión anterior.

## Siguiente etapa nativa

Cuando la PWA quede validada en dispositivos reales, se puede agregar Capacitor al mismo repositorio para generar los proyectos iOS y Android. La interfaz seguirá siendo compartida; solamente se agregarán los contenedores, permisos, splash screens y configuración específica de las tiendas.
