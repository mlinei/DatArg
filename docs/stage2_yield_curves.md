# Curvas de rendimiento en pesos

## Alcance

El pipeline conserva una observación por instrumento y fecha de cierre para dos familias:

- `nominal`: LECAP, BONCAP y otros instrumentos nominales elegibles.
- `cer`: títulos cuyo capital se ajusta por CER.

La entrada normalizada contiene precio de cierre, fecha de liquidación, vencimiento y todos los flujos futuros. Para CER, DatArg convierte el precio nominal a VN real mediante `precio × CER de emisión / CER vigente` y reconstruye cupones y amortizaciones sobre el capital residual.

## Cálculos

- TIR: tasa efectiva anual que iguala precio y valor presente de los flujos con días reales/365.
- TEM: `(1 + TIR)^(1/12) - 1`.
- Duración: Macaulay sobre los mismos flujos descontados.
- Breakeven: `(1 + TIR nominal) / (1 + TIR real) - 1`.

Para el breakeven, la interfaz interpola linealmente la TIR CER entre dos plazos observados y no extrapola fuera de la curva. Por eso es una expectativa de inflación implícita aproximada, afectada también por liquidez, riesgo, impuestos y diferencias entre instrumentos; no es un pronóstico.

## Fuente y activación

La curva nominal combina metadatos de ArgentinaDatos con cotizaciones demoradas de Data912. La curva CER usa precios y cronogramas públicos de Rendimientos.co y el CER oficial del BCRA que ese servicio identifica con su fecha de referencia T-10. La TIR CER no se toma de la interfaz del proveedor: DatArg la calcula con días reales/365 y rechaza valores de CER vencidos, flujos inconsistentes o resultados fuera de rangos de sanidad. El endpoint de ArgentinaDatos queda sólo como respaldo si vuelve a publicar TIR válidas.

Los precios demorados, diferencias de liquidez, impuestos y la interpolación entre instrumentos hacen que el breakeven sea una medida aproximada, no una predicción puntual de inflación.

La salida `data/processed/yield_curves.csv` se importa mediante Drizzle a `yield_curve_instruments` y se expone con el mismo contrato CSV en `/api/data/yield_curves.csv`.
