# Intervención cambiaria y crédito del BCRA

## Intervención cambiaria

La serie diaria corresponde a la variable 78 de la API estadística v4 del BCRA y está expresada en millones de dólares. Un valor positivo indica una compra neta de divisas del Banco Central y uno negativo, una venta neta. La definición oficial excluye las operaciones directas con el Tesoro Nacional.

DatArg conserva el dato diario oficial y calcula dos vistas adicionales:

- acumulado mensual: suma de las observaciones diarias de cada mes calendario;
- acumulado anual: suma de las observaciones diarias de cada año calendario.

Los períodos mensuales y anuales en curso son parciales y cambian con cada nueva observación.

## Crédito al sector privado no financiero

El nivel corresponde al saldo mensual de préstamos de las entidades financieras al sector privado no financiero publicado por el BCRA. Los archivos originales están expresados en miles de pesos y DatArg los convierte a millones de pesos corrientes.

La interfaz prioriza dos transformaciones:

- índice real con base diciembre de 2019 = 100: divide cada saldo nominal por el IPC nacional y compara el resultado con diciembre de 2019;
- porcentaje del PIB: divide el saldo de fin de mes por el PIB nominal anualizado de los últimos cuatro trimestres disponibles. Como la serie trimestral corriente del INDEC está anualizada, DatArg utiliza el promedio de esos cuatro trimestres.

Los niveles nominales y sus variaciones interanuales se conservan en el archivo procesado para auditoría, pero no son la vista principal. Cuando todavía no se publicó un trimestre nuevo del PIB se mantiene el último denominador disponible.

Los préstamos en moneda extranjera están incluidos en los saldos del BCRA y valuados en pesos al tipo de cambio de cada período. Por eso el índice real también puede registrar efectos de valuación cambiaria y no debe interpretarse como una medida pura de cantidades.

## Préstamos y exposición al sector público

Los préstamos al sector público se presentan con la apertura disponible:

- gobiernos;
- empresas y otros entes públicos;
- total calculado como suma de ambos componentes.

La exposición ampliada suma los préstamos anteriores y los títulos emitidos por los gobiernos nacional, provinciales y municipales que mantienen las entidades financieras. Se excluyen expresamente las Letras y Notas emitidas por el BCRA para evitar presentar pasivos del Banco Central como crédito al sector público no financiero.

Esta medición sirve para observar la composición de los activos bancarios, pero no demuestra por sí sola desplazamiento o impulso del crédito privado. Para analizar *crowding out* o *crowding in* deben considerarse además inflación, actividad, tasas, demanda de crédito y cambios regulatorios.
