# Etapa 2 — riesgo país

## Alcance y fuente

Se publica la evolución diaria del indicador denominado “riesgo país” para Argentina, expresado en puntos básicos. La fuente estructurada es ArgentinaDatos, que declara a Ámbito como origen de esta serie.

La serie se marca `aggregated_index`: no es una estadística oficial del INDEC, BCRA o Tesoro, ni una publicación primaria contratada directamente con J.P. Morgan. En el uso financiero argentino, “riesgo país” suele referirse al índice EMBI de J.P. Morgan, pero el pipeline conserva la denominación y los valores provistos por la fuente sin atribuir una licencia o metodología primaria que la API no documenta.

## Cobertura y controles

La cobertura comienza el 22 de enero de 1999 y llega al 10 de julio de 2026 en la corrida del 11 de julio de 2026. Sólo se publican las fechas informadas: no se completan fines de semana, feriados ni huecos mediante arrastre o interpolación.

Se valida el esquema JSON, orden y unicidad de fechas, valores positivos y un rango máximo defensivo de 20.000 puntos. La respuesta original se conserva con sello UTC y SHA-256. La promoción es atómica y rechaza truncamientos.

