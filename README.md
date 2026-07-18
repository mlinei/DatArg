# argentina-economic-data

La interfaz pública del proyecto se llama **DatArg**.

Pipelines reproducibles de fuentes oficiales para indicadores económicos de Argentina.

## Inflación (Etapa 2)

El primer pipeline implementado descarga y publica las series nacionales mensuales de IPC general, núcleo, regulados y estacionales, y el IPIM general. Conserva cada fuente con sello UTC y SHA-256, valida esquema/cobertura/claves, contrasta la variación mensual publicada del IPC con el índice, registra revisiones y promueve atómicamente una salida larga en UTF-8.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
aed inflation
```

Salida promovida: `data/processed/inflation.csv`. Fuentes inmutables: `data/raw/<source>/<timestamp>/`. Reporte de cambios: `data/logs/inflation/<run>.json`.

Para reproducir una ejecución sin red se pueden fijar ambos insumos:

```bash
aed inflation --ipc-file /ruta/serie_ipc_divisiones.csv --ipim-file /ruta/series_sipm_dic2015.xls
```

El proceso falla antes de promover si recibe HTML, un archivo vacío, un esquema desconocido, claves duplicadas, un panel IPC incompleto, cobertura inesperada o pérdida de observaciones respecto de la versión publicada.

## Actividad económica (EMAE)

```bash
aed emae
```

Importa el EMAE agregado —serie original, desestacionalizada y tendencia-ciclo— y los índices e interanuales de los sectores oficiales. La salida queda en `data/processed/emae.csv`; los libros y reportes de revisiones siguen la misma política inmutable que inflación.

## Pobreza e indigencia

```bash
aed poverty
```

Importa la incidencia semestral sobre personas para el total de 31 aglomerados urbanos y seis regiones estadísticas desde `2016-S2`. La salida queda en `data/processed/poverty.csv`.

## Comercio exterior

```bash
aed trade
```

Importa exportaciones, importaciones y saldo comercial mensual del ICA desde enero de 1986. La salida queda en `data/processed/trade.csv`.

## Producto interno bruto

```bash
aed gdp
```

Importa el PIB trimestral original y desestacionalizado, y el PIB anual oficial del INDEC, a precios constantes de 2004 y corrientes. La salida queda en `data/processed/gdp.csv`.

## Mercado laboral

```bash
aed labor
```

Importa las tasas trimestrales de actividad, empleo y desocupación de la EPH para el total de 31 aglomerados y seis regiones. La salida queda en `data/processed/labor.csv`.

## Industria manufacturera

```bash
aed industry
```

Importa el IPI manufacturero general y sus divisiones, con índice, variación interanual y acumulada. La salida queda en `data/processed/industry.csv`.

## Salarios nominales y reales

```bash
aed wages
```

Importa el índice mensual de salarios total, total registrado, privado registrado, público y privado no registrado. También calcula índices reales dividiendo cada índice salarial por el IPC nacional y reexpresándolos con diciembre de 2016=100. La salida queda en `data/processed/wages.csv`.

## Tipos de cambio

```bash
aed exchange-rates
```

Importa cotizaciones diarias de venta del dólar oficial minorista, blue, MEP y CCL. La salida queda en `data/processed/exchange_rates.csv`.

## Reservas internacionales netas

```bash
aed reserves
aed net-reserves
```

Reconstruye desde diciembre de 2023 las reservas netas descontando encajes, el swap con China, obligaciones con organismos internacionales y repos con vencimiento residual de hasta un año. Publica además cada componente en `data/processed/net_reserves.csv`. Es una serie calculada por DatArg y no una estadística oficial del BCRA.

## S&P Merval en dólares

```bash
aed markets
```

Construye una serie diaria del S&P Merval en dólar MEP desde 2019, dividiendo el cierre en pesos obtenido de Yahoo Finance por la cotización MEP de ArgentinaDatos. La salida queda en `data/processed/markets.csv`. Es un cálculo reproducible de DatArg y no la serie oficial licenciada de S&P Dow Jones Indices.

## Riesgo país

```bash
aed country-risk
```

Importa la evolución diaria reportada del riesgo país argentino, en puntos básicos. La salida queda en `data/processed/country_risk.csv`.

## Tasas de interés

```bash
aed interest-rates
```

Importa BADLAR y TAMAR de bancos privados, tanto TNA como TEA, desde la API v4 oficial del BCRA. La salida queda en `data/processed/interest_rates.csv`.

## Recaudación y resultado fiscal

```bash
aed fiscal
```

Importa la recaudación tributaria y los resultados primario y financiero mensuales del Sector Público Nacional no Financiero desde 2017. Conserva los niveles nominales, calcula niveles a precios de diciembre de 2025 y variaciones reales con el IPC nacional, y agrega vistas anuales reales y como porcentaje del PIB. La salida queda en `data/processed/fiscal.csv`. La primera reconstrucción completa puede repetirse con `aed fiscal --refresh-history`.

## Deuda neta consolidada

```bash
aed consolidated-debt
```

Publica una estimación documentada de deuda estatal neta (Tesoro + BCRA − activos), en millones de USD y porcentaje del PIB. Incluye seis cortes históricos comparables de Chequeado/Aurum, una secuencia anual Facimex desde 2023 y la descomposición de Econosignal para `2025-Q2`. La salida queda en `data/processed/consolidated_debt.csv`; no es una estadística oficial ni se interpolan los períodos faltantes.

## Deuda del Tesoro y pasivos del BCRA

```bash
aed public-debt
```

Publica por separado la deuda bruta de la Administración Central y los pasivos financieros remunerados del BCRA. El nivel del Tesoro incluye cierres anuales desde 2013 y datos mensuales desde 2019; también incorpora la relación oficial deuda/PIB desde 2000. No calcula ni presenta una suma consolidada. La salida queda en `data/processed/public_debt.csv`.

## Reservas internacionales brutas

```bash
aed reserves
```

Importa la serie diaria oficial y provisoria de reservas internacionales brutas del BCRA desde la API v4. La salida queda en `data/processed/reserves.csv`.

```bash
make test
```

## Actualizaciones automáticas

GitHub Actions consulta las series diarias y mensuales —incluidas recaudación y cuentas fiscales— en días hábiles, y solo guarda cambios reales después de ejecutar las validaciones y reconstruir DatArg. La configuración y la operación manual están documentadas en `docs/automatic_updates.md`.
