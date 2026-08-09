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

Importa el PIB trimestral original y desestacionalizado, y el PIB anual oficial del INDEC, a precios constantes de 2004 y corrientes. También incorpora el consumo privado agregado: nivel real, variaciones trimestral desestacionalizada e interanual, resultado anual y participación en el PIB. La salida queda en `data/processed/gdp.csv`.

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

## Intervención cambiaria

```bash
aed fx-intervention
```

Importa las compras y ventas netas de divisas del BCRA en el mercado de cambios y calcula sus acumulados por mes y año calendario. También extrae de la Planilla de Reservas Internacionales y de Liquidez en Moneda Extranjera las posiciones mensuales cortas y largas en futuros liquidados en pesos y calcula `compras spot − variación de la posición neta vendida`. La interfaz permite alternar entre intervención ajustada, cambio mensual de la posición vendida y posición abierta al cierre. En la vista de futuros, un valor positivo indica que aumentó la posición vendida y uno negativo que se redujo. La medición ajustada es una estimación de DatArg, no un flujo de reservas ni una serie oficial consolidada; excluye al Tesoro y otros instrumentos del sector público. No se atribuye al BCRA el interés abierto diario del mercado porque la fuente pública no identifica titulares. La salida queda en `data/processed/fx_intervention.csv`.

## Giros de utilidades y dividendos

```bash
aed profit-dividends
```

Importa los egresos mensuales por utilidades y dividendos efectivamente cursados en el mercado de cambios desde 2003. El pipeline invierte el signo contable con el que el BCRA publica los egresos y calcula totales anuales únicamente para años calendario completos. No incluye utilidades reinvertidas ni representa el devengamiento contable de la inversión directa. La salida queda en `data/processed/profit_dividends.csv`.

## Liquidez del Tesoro en el BCRA

```bash
aed treasury-liquidity
```

Importa los depósitos del Gobierno Nacional en moneda nacional y extranjera con frecuencia diaria desde `diar_bas.xls` (códigos 8842 y 8843) y conserva la serie mensual del balance del BCRA (series 106 y 107). La cuenta en pesos se expresa en millones de ARS. Como el BCRA valúa contablemente la cuenta extranjera en pesos, el pipeline la divide por el tipo de cambio de valuación oficial (código/serie 271) para reconstruir millones de USD. Calcula variaciones entre saldos diarios y mensuales, controla los totales oficiales 269 y 105, y descarta las filas provisionales que el libro diario publica con saldo cero. La salida queda en `data/processed/treasury_liquidity.csv`.

## Tasas de interés

```bash
aed interest-rates
```

Importa BADLAR y TAMAR de bancos privados, tanto TNA como TEA, desde la API v4 oficial del BCRA. La salida queda en `data/processed/interest_rates.csv`.

### Curvas nominal, CER e inflación breakeven

```bash
aed yield-curves
```

Calcula la TIR efectiva anual, la tasa efectiva mensual y la duración de LECAP/BONCAP combinando las condiciones de emisión recopiladas por ArgentinaDatos con cotizaciones demoradas de Data912. Para títulos CER reconstruye la TIR con precios y cronogramas públicos de Rendimientos.co y el CER oficial fechado por el BCRA; ArgentinaDatos queda como respaldo si vuelve a publicar observaciones válidas. La web deriva la inflación breakeven mediante Fisher sólo cuando ambas curvas comparten fecha y dentro del rango CER observado. La salida canónica es `data/processed/yield_curves.csv`. `--source-file` permite mantener el importador normalizado como alternativa auditable.

## Crédito privado y exposición al sector público

```bash
aed credit
```

Importa del BCRA los préstamos al sector privado no financiero y los préstamos al sector público, separados entre gobiernos y empresas u otros entes públicos. También calcula una exposición pública ampliada que suma esos préstamos y los títulos de los gobiernos nacional, provinciales y municipales en poder de las entidades financieras, excluyendo Letras y Notas del BCRA. Conserva los niveles nominales para trazabilidad y publica dos vistas comparables: índice real deflactado por IPC con base diciembre de 2019 = 100 y saldo como porcentaje del PIB nominal anualizado de los últimos cuatro trimestres. La salida queda en `data/processed/credit.csv`.

## Recaudación y resultado fiscal

```bash
aed fiscal
```

Importa la recaudación tributaria y los resultados primario y financiero mensuales del Sector Público Nacional no Financiero desde 2017. Conserva los niveles nominales, calcula niveles a precios de diciembre de 2025 y variaciones reales con el IPC nacional, y agrega vistas anuales reales y como porcentaje del PIB. La salida queda en `data/processed/fiscal.csv`. La primera reconstrucción completa puede repetirse con `aed fiscal --refresh-history`.

## Inversión pública y gastos de capital

```bash
aed public-investment
```

Importa las series anuales oficiales de inversión pública de la Administración Pública Nacional desde 1995 y de gastos de capital del Sector Público Nacional desde 1997. Publica el nivel real con base 2019=100, el porcentaje del PIB y la composición funcional disponible. Excluye las columnas proyectadas de 2026. La salida queda en `data/processed/public_investment.csv`.

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

## Esquema de vencimientos del Tesoro

```bash
aed debt-maturities
```

Importa de la última planilla trimestral de la Secretaría de Finanzas el cronograma mensual proyectado de capital e intereses de la Administración Central, expresado en millones de USD. Conserva cada fecha de corte, el total, los grupos principales y el detalle por instrumento; por eso no debe interpretarse como pagos efectivamente realizados. La salida queda en `data/processed/treasury_maturities.csv`.

## Reservas internacionales brutas

```bash
aed reserves
```

Importa la serie diaria oficial y provisoria de reservas internacionales brutas del BCRA desde la API v4. La salida queda en `data/processed/reserves.csv`.

```bash
make test
```

## Actualizaciones automáticas

GitHub Actions consulta las series diarias, mensuales y la última planilla anual de inversión pública en días hábiles, y solo guarda cambios reales después de ejecutar las validaciones y reconstruir DatArg. La configuración y la operación manual están documentadas en `docs/automatic_updates.md`.
