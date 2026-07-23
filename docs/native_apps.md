# Aplicaciones nativas de DatArg

DatArg usa Capacitor 8 para envolver el mismo bundle Vite en iOS y Android. La web, la PWA y las aplicaciones comparten interfaz y lógica; los contenedores nativos viven en `ios/` y `android/`.

## Identidad y datos

- Nombre: `DatArg`
- Identificador de publicación: `ar.fausto.datarg`
- Bundle web: `dist/`
- Datos remotos nativos: `https://dat-arg.vercel.app/data`
- Última copia válida de cada CSV: IndexedDB del dispositivo

Los enlaces a fuentes se abren en el navegador del sistema. La aplicación detecta la conectividad con el plugin nativo y respeta las áreas seguras del dispositivo.

## Flujo habitual

1. Ejecutar `npm run native:sync` después de cada cambio web.
2. Ejecutar `npm run native:assets` cuando cambien el icono o el splash.
3. Abrir con `npm run native:ios` o `npm run native:android`.

`native:sync` compila Vite, copia el bundle a ambos contenedores y sincroniza los plugins.

## Requisitos de compilación

- iOS: Xcode 26 o posterior. La instalación local actual de Xcode 15.3 permite conservar el proyecto, pero no compilar una entrega aceptada por App Store Connect en 2026.
- Android: Android Studio 2025.2.1 o posterior y Android SDK API 24 o superior.

Los recursos fuente viven en `assets/`: `icon-only.png`, `splash.png` y `splash-dark.png`.
