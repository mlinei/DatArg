# Base de datos de DatArg

DatArg usa Turso (LibSQL) como fuente de datos principal y Drizzle como fuente de
verdad del esquema y de sus migraciones. Los CSV de `data/processed` se mantienen
temporalmente como respaldo y como formato intermedio de los pipelines.

## Arquitectura

1. Los pipelines producen datasets normalizados en `data/processed`.
2. `npm run db:migrate` aplica únicamente migraciones pendientes de `drizzle/`.
3. `npm run db:import` reemplaza en Turso las observaciones de cada dataset.
4. `npm run db:verify` compara conteos, checksums y cada campo contra el origen.
5. `/api/data/:archivo.csv` consulta Turso sin exponer sus credenciales.
6. La web y las apps consultan esa API. Si no responde, usan `/data` y luego la
   copia persistida en el dispositivo.

Cada dataset queda marcado como `importing` durante su actualización y solo
vuelve a `ready` después de validar el total de observaciones. Mientras tanto,
la API responde `503` y el cliente utiliza el CSV de respaldo.

## Variables secretas

Nunca deben incorporarse tokens al repositorio. Se requieren:

- `TURSO_DATABASE_URL`
- `TURSO_AUTH_TOKEN`

Deben configurarse tanto en Vercel como en GitHub Actions. `.env.example` solo
documenta los nombres y `.gitignore` excluye cualquier `.env` real.

## Migraciones

Modificar `db/schema.ts` y ejecutar:

```sh
npm run db:generate -- --name descripcion_del_cambio
npm run db:migrate
```

No usar `drizzle-kit push` en producción: las modificaciones deben quedar
representadas por archivos SQL versionados.

## Importación y verificación

```sh
npm run db:import
npm run db:verify
```

El workflow automático ejecuta migración, importación y verificación antes de
publicar nuevos datos. Si cualquiera falla, no hace commit ni envía alertas.

## Recuperación

Mientras dure la transición, los CSV siguen desplegados. Si Turso o la función
de Vercel fallan, el cliente cambia automáticamente a esos archivos y, como
última alternativa, a la copia almacenada en el dispositivo.

El estado inmediatamente anterior a esta migración también está respaldado en
`.checkpoints/datarg-before-turso-2026-07-23.tar.gz` en la máquina de desarrollo.
El SHA-256 del archivo es:

```text
960a0db1cd0f1ff60b43e6e9615d312a689962f3b8c94785985129a41a19c690
```
