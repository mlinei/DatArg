# Lanzamiento de DatArg en Google Play

## Identidad de la aplicación

- Nombre: **DatArg**
- Nombre del paquete: `com.mlinei.datarg`
- Versión inicial: `1.0` (`versionCode` 1)
- Categoría sugerida: Finanzas
- Correo de soporte: completar con el correo de la cuenta publicadora
- Política de privacidad: `https://dat-arg.vercel.app/privacidad.html`

El nombre del paquete debe confirmarse antes de crear la aplicación en Play Console. No puede cambiarse después de la primera publicación.

## Textos sugeridos para la ficha

### Descripción breve

Indicadores económicos de Argentina, actualizados y con fuentes trazables.

### Descripción completa

DatArg reúne en un solo lugar los principales indicadores de la economía argentina.

Consultá inflación, actividad, producto interno bruto, industria, empleo, salarios, pobreza, comercio exterior, reservas, tipos de cambio, riesgo país, tasas de interés, deuda, recaudación, resultado fiscal e inversión pública.

Cada gráfico permite seleccionar series, comparar componentes y ajustar el período visible. Los datos provienen de organismos públicos y fuentes identificadas en cada indicador. La aplicación conserva la última copia disponible para facilitar la consulta cuando no hay conexión.

Podés activar alertas opcionales para enterarte cuando se incorpora un nuevo dato o una revisión.

DatArg es una herramienta informativa independiente. No brinda asesoramiento financiero ni representa a ningún organismo público.

## Declaraciones para Play Console

- Publicidad: **No contiene anuncios**.
- Acceso a la aplicación: **Todas las funciones están disponibles sin iniciar sesión**.
- Público objetivo: aplicación de información económica general; no está dirigida específicamente a menores.
- Aplicación gubernamental: **No**. Usa datos públicos, pero no representa al Estado.
- Funciones financieras: información económica; no ofrece operaciones, préstamos, inversiones, billetera ni asesoramiento financiero personalizado.

## Seguridad de los datos

Revisar nuevamente al cargar la versión definitiva. Con la implementación actual:

- La app no crea cuentas ni solicita nombre, correo, ubicación, contactos o datos de pago.
- Los CSV económicos y preferencias se almacenan localmente en el dispositivo.
- Al activar alertas, Firebase Cloud Messaging procesa identificadores de dispositivo o de instalación y datos técnicos para la funcionalidad de la aplicación.
- Los datos de mensajería se cifran en tránsito.
- La persona puede desactivar las alertas y desinstalar la aplicación para eliminar los datos locales.
- No se usan datos para publicidad ni para venta a terceros.

La respuesta final del formulario debe contrastarse con la guía de divulgación de Firebase correspondiente a las versiones de SDK incluidas en el bundle.

## Firma segura del bundle

La configuración admite `android/keystore.properties` o variables de entorno. La clave y las contraseñas nunca deben subirse al repositorio.

1. La cuenta publicadora crea y custodia la upload key.
2. Copiar `android/keystore.properties.example` como `android/keystore.properties` y completar los valores, o definir:
   - `DATARG_UPLOAD_STORE_FILE`
   - `DATARG_UPLOAD_STORE_PASSWORD`
   - `DATARG_UPLOAD_KEY_ALIAS`
   - `DATARG_UPLOAD_KEY_PASSWORD`
3. Desde `android/`, ejecutar `./gradlew clean bundleRelease lintRelease`.
4. Verificar la firma antes de subir:

```bash
jarsigner -verify -verbose -certs app/build/outputs/bundle/release/app-release.aab
```

5. Activar Play App Signing al crear la primera versión en Google Play.

## Recursos de la ficha

Los archivos preparados se encuentran en `store-assets/android/`:

- `app-icon-512.png`
- `feature-graphic-1024x500.png`
- `phone-home.png`
- `phone-inflation.png`

Las capturas de teléfono fueron obtenidas desde la compilación Android ejecutada en un emulador Pixel y cumplen la resolución admitida por Play Console (1080 × 2424 px).
