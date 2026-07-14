# Etapa 2 — producto interno bruto

## Alcance

El módulo publica exclusivamente estimaciones oficiales de cuentas nacionales del INDEC, base 2004. No mezcla ni completa observaciones con estimaciones del Banco Mundial u otros organismos.

Series trimestrales:

- PIB original en millones de ARS a precios de 2004;
- variación interanual oficial;
- PIB a precios corrientes;
- PIB desestacionalizado a precios de 2004;
- variación contra el trimestre anterior oficial.

Series anuales:

- PIB en millones de ARS a precios de 2004;
- crecimiento anual oficial;
- PIB en millones de ARS a precios corrientes.

La cobertura base 2004 comienza en 2004. La corrida del 11 de julio de 2026 llega a `2026-Q1` para datos trimestrales y a 2025 para datos anuales completos.

## Fuentes y controles

Se utilizan los libros `sh_oferta_demanda_06_26.xls` y `sh_oferta_demanda_desest_06_26.xls`, publicados en la página de agregados macroeconómicos del INDEC. Las URL cambian con la edición trimestral y deben actualizarse desde la página oficial.

Se validan hojas, dimensiones, fila del código `B1b`, calendario, cobertura, duplicados, correspondencia entre precios constantes y corrientes y consistencia de las variaciones interanuales, anuales y desestacionalizadas contra los niveles publicados. Los libros quedan versionados con fecha UTC y SHA-256; la promoción es atómica y rechaza truncamientos.

Los valores trimestrales de nivel siguen la convención publicada por INDEC. El valor anual `Total` se conserva directamente del cuadro oficial; no se lo reemplaza por un cálculo propio.

