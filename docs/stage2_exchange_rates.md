# Etapa 2 — tipos de cambio

## Alcance y fuente

Se publican cuatro cotizaciones diarias en ARS por USD: oficial minorista, blue, MEP y contado con liquidación (CCL). Se utiliza la API histórica de ArgentinaDatos, proyecto público no oficial que declara DolarApi como fuente.

Por lo tanto, estas observaciones tienen `status=aggregated_quote`: no deben presentarse como estadísticas oficiales del BCRA. En particular, `official_retail` es la cotización minorista denominada “oficial” por el agregador y no el Tipo de Cambio de Referencia mayorista de la Comunicación A 3500.

Se conserva una sola línea comparable por mercado: el campo `venta` reportado. Los JSON originales preservan también `compra` para auditoría, pero ese campo no se promueve porque el histórico contiene anomalías de orden compra/venta que impedirían construir spreads confiables sin alterar la fuente.

## Cobertura

- Oficial minorista y blue: desde 3 de enero de 2011.
- CCL: desde 2 de enero de 2013.
- MEP: desde 29 de octubre de 2018.

La corrida del 11 de julio de 2026 llega al cierre del 10 de julio de 2026. Las series incluyen días repetidos por arrastre de la última cotización informada; son observaciones calendarias reportadas por la fuente, no necesariamente ruedas con operaciones.

## Controles

Se validan esquema y mercado de cada JSON, fechas ISO únicas, precios positivos y umbrales mínimos de cobertura. Cada respuesta se guarda de forma inmutable con fecha UTC y SHA-256. La promoción es atómica y rechaza pérdidas de observaciones.

Para análisis institucional del dólar oficial mayorista deberá incorporarse por separado la serie A 3500 del BCRA, sin empalmarla ni sustituir silenciosamente esta cotización minorista.

