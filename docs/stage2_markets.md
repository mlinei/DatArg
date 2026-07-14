# S&P Merval en dólares

## Definición

DatArg calcula el nivel diario en dólares financieros como:

`cierre del S&P Merval en ARS / dólar MEP vendedor en ARS/USD`

La serie comienza el 11 de enero de 2019, fecha base de la historia publicada para el índice oficial S&P MERVAL (MEP). Es un índice de precios: no incorpora dividendos.

## Fuentes

- El cierre diario de `^MERV` se obtiene de Yahoo Finance.
- El dólar MEP vendedor proviene de ArgentinaDatos y ya se normaliza en `exchange_rates.csv`.
- La definición y la fecha base se contrastaron con la metodología de S&P Dow Jones Indices y BYMA.
- Los cierres de Yahoo se contrastaron en el período superpuesto con la serie diaria del IAMC publicada en Datos Argentina.

La serie resultante se identifica como `datarg_sp_merval_mep_usd`, lleva estado `calculated` y conserva la URL, fecha y hash del archivo de mercado descargado. No debe presentarse como la serie oficial licenciada S&P MERVAL (MEP).

## Ejecución

```bash
aed exchange-rates
aed markets
```

La actualización automática respeta ese orden para calcular cada rueda con la cotización MEP más reciente disponible.
