# Etapa 2 — TAMAR y BADLAR

## Series

Se publican cuatro series diarias oficiales del BCRA para bancos privados:

- BADLAR, tasa nominal anual (TNA), desde el 4 de enero de 1999;
- BADLAR, tasa efectiva anual (TEA), desde el 23 de enero de 2020;
- TAMAR, TNA, desde el 1 de octubre de 2024;
- TAMAR, TEA, desde el 1 de octubre de 2024.

TNA y TEA se conservan como observaciones oficiales separadas. La interfaz no debe graficarlas juntas como si fueran la misma unidad.

## Definiciones

BADLAR es una tasa promedio ponderada de depósitos a plazo fijo mayoristas en pesos, con el alcance definido por el BCRA. TAMAR es la tasa promedio ponderada por monto de depósitos mayoristas en pesos a 30–35 días. Para TAMAR, el monto mínimo fue de $1.000 millones hasta fines de 2025 y pasó a $1.300 millones en 2026; el umbral se actualiza anualmente según la metodología.

## Fuente y controles

La fuente es la API oficial `Estadísticas Monetarias v4.0`, variables 7, 35, 44 y 45. El extractor pagina explícitamente en bloques de 1.000 registros porque la API trunca silenciosamente la respuesta predeterminada.

Se validan identificador, esquema, fechas ISO únicas, cobertura inicial y valores entre 0% y 1.000%. Cada página se preserva con fecha UTC y SHA-256. La promoción es atómica y rechaza pérdidas de observaciones.

