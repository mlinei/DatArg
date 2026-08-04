# Intervención cambiaria y crédito del BCRA

## Intervención cambiaria

La serie diaria corresponde a la variable 78 de la API estadística v4 del BCRA y está expresada en millones de dólares. Un valor positivo indica una compra neta de divisas del Banco Central y uno negativo, una venta neta. La definición oficial excluye las operaciones directas con el Tesoro Nacional.

DatArg conserva el dato diario oficial y calcula dos vistas adicionales:

- acumulado mensual: suma de las observaciones diarias de cada mes calendario;
- acumulado anual: suma de las observaciones diarias de cada año calendario.

Los períodos mensuales y anuales en curso son parciales y cambian con cada nueva observación.

### Ajuste por futuros de dólar

Para aproximar la dirección conjunta de la intervención del propio BCRA, DatArg incorpora la posición nocional mensual en futuros de moneda publicada en la sección IV.1.b de la Planilla de Reservas Internacionales y de Liquidez en Moneda Extranjera del BCRA. La fuente informa por separado las posiciones cortas y largas denominadas en moneda extranjera y liquidadas por otros medios, principalmente en pesos.

La posición neta vendida se define como posición corta menos posición larga. La intervención mensual ajustada se calcula así:

`compras spot del BCRA − variación mensual de la posición neta vendida en futuros`

Por lo tanto:

- un aumento de la posición vendida resta a las compras spot, porque representa presión vendedora de dólares futuros;
- una reducción de la posición vendida suma, porque desarma esa presión;
- en la vista específica de futuros se muestra el cambio sin invertir el signo: positivo equivale a aumento de la posición vendida y negativo a reducción;
- un resultado positivo representa una fuerza neta compradora o alcista sobre el dólar y uno negativo, una fuerza neta vendedora o de contención, manteniendo constantes los demás factores.

La serie calculada comienza en enero de 2023 y solo llega hasta el último cierre mensual publicado en la planilla, que tiene mayor rezago que la intervención spot diaria. No se imputan meses todavía no publicados. La interfaz permite ver tanto el flujo mensual atribuible al cambio de la posición como el último stock abierto oficial, con apertura entre posiciones cortas y largas.

No se presenta una falsa intervención diaria del BCRA en futuros. A3 Mercados divulga volumen e interés abierto diario para el conjunto del mercado, pero esa información no identifica al titular de cada posición. La única frecuencia pública que permite atribuir la exposición específicamente al BCRA es el cierre mensual de esta planilla.

Esta medición no equivale a un flujo de caja ni a una variación de reservas: los contratos relevados se liquidan en pesos. Tampoco es todavía una medición consolidada del sector público, porque excluye operaciones del Tesoro, emisión o recompra de instrumentos dólar linked y otras intervenciones gubernamentales. Es una estimación reproducible de la dirección de la intervención del BCRA bajo una metodología explícita.

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
