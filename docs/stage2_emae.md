# Etapa 2 — pipeline de EMAE

## Fuentes y cobertura

El pipeline descubre conceptualmente los dos recursos publicados en la página oficial de EMAE y fija sus URLs estructuradas:

- `sh_emae_mensual_base2004.xls`: agregado mensual desde enero de 2004.
- `sh_emae_actividad_base2004.xls`: índices sectoriales desde enero de 2004 e interanuales desde enero de 2005.

La corrida del 11 de julio de 2026 importó datos hasta abril de 2026.

## Series

El agregado publica seis series oficiales: índice original e interanual; índice desestacionalizado y mensual; índice tendencia-ciclo y mensual. El libro sectorial publica índice e interanual para las ramas A–O y para impuestos netos de subsidios. En total se promueven 38 series.

La salida `data/processed/emae.csv` comparte el contrato largo de inflación: una clave `(series_id, period)`, frecuencia, valor, unidad, estado oficial y trazabilidad completa de la fuente.

## Controles

Se validan nombres de hojas, dimensiones, encabezados, orden y cantidad de sectores, calendario mensual, cobertura mínima, claves únicas, ausencia de huecos y positividad de índices. Las variaciones oficiales mensuales e interanuales se contrastan contra los índices con precisión de los libros.

Las fuentes se conservan con sello UTC, tamaño y SHA-256. La promoción es atómica y se rechaza si una nueva fuente elimina observaciones previamente publicadas. Las revisiones históricas normales del EMAE se informan como modificaciones en `data/logs/emae/`.

