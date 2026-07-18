# Deuda del Tesoro y pasivos remunerados del BCRA

Se publican dos conceptos separados; no se los suma ni se los denomina deuda consolidada.

- `mecon_gross_central_government_debt`: deuda bruta de la Administración Central, en millones de USD. Incluye cierres anuales oficiales de 2013 a 2018 y la serie mensual desde enero de 2019.
- `mecon_gross_central_government_debt_gdp_ratio`: la misma definición de deuda como porcentaje del PIB, según la relación oficial de la Secretaría de Finanzas; cubre cierres anuales desde 2000 y el último trimestre publicado.
- `bcra_interest_bearing_liabilities`: pasivos financieros remunerados del BCRA convertidos a millones de USD al tipo de cambio mayorista de fin de mes.

La segunda serie suma letras del BCRA en pesos y moneda extranjera, LELIQ/NOTALIQ, pases pasivos en pesos y pases pasivos en dólares con el exterior. Sus componentes oficiales son las variables BCRA 1258, 1259, 1260, 1262 y 76; la variable 5 se usa exclusivamente para convertir los componentes expresados en ARS.

El valor del BCRA tiene estado `calculated`, ya que agrega instrumentos y convierte moneda, aunque todos sus insumos son oficiales. Se toma la última observación disponible de cada mes. La deuda del Tesoro conserva estado `official`.

Los niveles anteriores a 2013 no se empalman porque los archivos históricos disponibles no forman una secuencia continua y comparable para todo el período. No se interpolan faltantes.
