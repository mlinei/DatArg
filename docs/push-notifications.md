# Notificaciones de DatArg

DatArg usa Firebase Cloud Messaging (FCM) para avisar cuando el pipeline incorpora observaciones nuevas o revisa datos existentes. Las aplicaciones se suscriben, con permiso explícito del usuario, al tema `economic-updates`. Al tocar un aviso se abre directamente la sección del indicador actualizado.

## Archivos de las aplicaciones

El proyecto de Firebase debe registrar las dos aplicaciones con el mismo identificador ya usado por Capacitor: `com.mlinei.datarg`.

- Android: descargar `google-services.json` y guardarlo en `android/app/google-services.json`.
- iOS: descargar `GoogleService-Info.plist`, guardarlo en `ios/App/App/GoogleService-Info.plist` y añadirlo al target **App** desde Xcode.
- iOS: en Firebase, subir una clave APNs del equipo de Apple Developer. El proyecto ya incluye la capacidad Push Notifications y sus entitlements.

Estos dos archivos identifican las aplicaciones pero no contienen la clave privada con la que se envían mensajes. Pueden versionarse junto con los proyectos nativos.

Después de añadirlos, ejecutar:

```bash
npm run native:sync
```

La recepción real en iOS debe probarse en un iPhone físico; el simulador no sustituye la validación de APNs.

## Credencial de GitHub Actions

El workflow usa Workload Identity Federation para obtener credenciales temporales de Google Cloud. No se descargan claves privadas ni se guardan secretos JSON en GitHub.

La configuración de Google Cloud es:

- Cuenta de servicio: `datarg-notifications@datarg.iam.gserviceaccount.com`.
- Rol de la cuenta: **Firebase Cloud Messaging API Admin**.
- Pool: `github-actions`.
- Proveedor OIDC: `github`.
- Repositorio autorizado: `mlinei/DatArg`, limitado a la rama `main`.

GitHub solicita un token OIDC de corta duración en cada ejecución y luego suplanta únicamente esa cuenta de servicio. No se debe crear ni descargar una clave JSON para este flujo.

## Prueba controlada

El generador local puede verificarse sin credenciales con:

```bash
npm run test:notifications
```

El envío solo ocurre después de que el pipeline detecta cambios económicos reales, completa las pruebas, reconstruye la web y publica el commit de datos.
