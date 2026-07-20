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

En Firebase/GCP se debe crear una cuenta de servicio con permiso para enviar mensajes de Firebase Cloud Messaging. Guardar su JSON completo como secreto del repositorio GitHub con este nombre exacto:

```text
FIREBASE_SERVICE_ACCOUNT_JSON
```

Nunca se debe guardar ese JSON privado en el repositorio. Si el secreto todavía no existe, la automatización publica los datos normalmente y deja una nota en el workflow, pero omite el aviso móvil.

## Prueba controlada

El generador local puede verificarse sin credenciales con:

```bash
npm run test:notifications
```

El envío solo ocurre después de que el pipeline detecta cambios económicos reales, completa las pruebas, reconstruye la web y publica el commit de datos.
