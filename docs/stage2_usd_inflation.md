# Inflación en dólares

El pipeline `aed usd-inflation` combina dos datasets ya normalizados por DatArg:

- el índice de precios al consumidor nacional, nivel general, publicado por INDEC;
- la cotización diaria de venta del dólar oficial minorista recopilada por ArgentinaDatos.

Para cada mes calcula el promedio aritmético de las cotizaciones diarias disponibles y
construye el nivel de precios expresado en dólares:

`nivel_usd(t) = IPC(t) / dólar_oficial_promedio(t)`

A partir de ese cociente publica tres series desde enero de 2024:

- índice de nivel, con enero de 2024 = 100;
- variación mensual exacta: `nivel_usd(t) / nivel_usd(t-1) - 1`;
- variación interanual exacta: `nivel_usd(t) / nivel_usd(t-12) - 1`.

La variación mensual es algebraicamente equivalente a
`(1 + inflación_en_pesos) / (1 + variación_del_dólar) - 1`; no se usa la resta de
porcentajes, que es solamente una aproximación. El resultado mide el cambio del nivel
general de precios locales convertido al dólar oficial minorista. No representa el costo
de vida de un consumidor estadounidense ni incorpora dólar MEP, CCL o blue.

La salida canónica es `data/processed/usd_inflation.csv`. Cada observación queda marcada
como calculada y conserva una huella conjunta de los dos archivos de entrada.
