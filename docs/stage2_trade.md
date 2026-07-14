# Etapa 2 — comercio exterior

## Alcance

Se publican exportaciones, importaciones y saldo comercial de bienes del Intercambio comercial argentino (ICA), en millones de USD corrientes y frecuencia mensual. La serie histórica oficial comienza en enero de 1986 y llega a mayo de 2026 en la corrida del 11 de julio de 2026.

La fuente estructurada es `plot_agregado.json`, el recurso oficial que alimenta el gráfico histórico del informe digital del ICA. Esto evita unir manualmente cuadros de sucesivos informes. La URL contiene el identificador de cada edición y deberá actualizarse desde el último informe oficial.

## Contrato y controles

`data/processed/trade.csv` contiene tres series oficiales:

- `indec_trade_exports`;
- `indec_trade_imports`;
- `indec_trade_balance`.

Se validan el esquema JSON, nombres de series, calendario, cobertura mínima, panel balanceado, claves únicas, flujos no negativos y, para cada mes, la identidad `saldo = exportaciones - importaciones` con precisión de la fuente. La promoción conserva el JSON y su SHA-256, es atómica y rechaza truncamientos.

El saldo positivo representa superávit y el negativo, déficit. No es una serie “neta” distinta: es la balanza comercial de bienes publicada por INDEC.

