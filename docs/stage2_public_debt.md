# Deuda del Tesoro y pasivos remunerados del BCRA

Se publican dos series mensuales separadas; no se las suma ni se las denomina deuda consolidada.

- `mecon_gross_central_government_debt`: deuda bruta de la Administración Central, en millones de USD, tomada de la fila total del boletín mensual de la Secretaría de Finanzas.
- `bcra_interest_bearing_liabilities`: pasivos financieros remunerados del BCRA convertidos a millones de USD al tipo de cambio mayorista de fin de mes.

La segunda serie suma letras del BCRA en pesos y moneda extranjera, LELIQ/NOTALIQ, pases pasivos en pesos y pases pasivos en dólares con el exterior. Sus componentes oficiales son las variables BCRA 1258, 1259, 1260, 1262 y 76; la variable 5 se usa exclusivamente para convertir los componentes expresados en ARS.

El valor del BCRA tiene estado `calculated`, ya que agrega instrumentos y convierte moneda, aunque todos sus insumos son oficiales. Se toma la última observación disponible de cada mes. La deuda del Tesoro conserva estado `official`.

La estimación neta de Econosignal permanece en `consolidated_debt.csv` como referencia metodológica independiente y no se mezcla en esta salida.
