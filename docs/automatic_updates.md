# Actualizaciones automáticas

El workflow `.github/workflows/update-data.yml` consulta las fuentes de lunes a viernes a las 20:30 de Argentina. Esto permite incorporar las series diarias y detectar el IPC y el IPIM sin depender de que INDEC publique siempre el mismo día del mes. Puede ejecutarse manualmente desde **Actions > Actualizar datos de DatArg > Run workflow**.

Antes de publicar, la tarea ejecuta todos los tests y reconstruye el sitio. Si una fuente falla, cambia de formato o produce datos inválidos, no crea un commit y Vercel conserva la última versión válida. Si no existen observaciones nuevas, la ejecución termina sin generar un deployment innecesario.

Para que funcione, el repositorio conectado a Vercel debe contener el proyecto fuente completo, no solo el contenido de `dist`. Vercel debe usar el preset Vite, `npm run build` como comando de compilación y `dist` como directorio de salida.
