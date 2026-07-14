# Etapa 2 — mercado laboral

## Alcance

Se publican las tasas oficiales trimestrales de actividad, empleo y desocupación abierta de la Encuesta Permanente de Hogares. El universo nacional es el total de 31 aglomerados urbanos de la EPH y no toda la población del país.

Además del total se incluyen seis regiones estadísticas: Gran Buenos Aires, Cuyo, Noreste, Noroeste, Pampeana y Patagonia. La serie comparable comienza en `2016-Q2` y llega a `2026-Q1` en la corrida del 11 de julio de 2026.

## Definiciones

- Actividad: población económicamente activa sobre población total.
- Empleo: población ocupada sobre población total.
- Desocupación: población desocupada abierta sobre población económicamente activa.

Las tres se expresan en porcentaje, pero sus denominadores no son iguales. No debe interpretarse desocupación como el complemento directo de empleo.

## Fuente y controles

La fuente es la serie histórica `cuadros_eph_informe_06_26.xls`, en particular los cuadros 1.6, 1.7 y 1.8. La URL cambia con cada publicación trimestral y debe actualizarse desde la página oficial.

Se validan hojas, dimensiones, calendario completo, siete geografías, porcentajes entre 0 y 100, claves únicas y la identidad aproximada `empleo = actividad × (1 − desocupación)`, con tolerancia por el redondeo oficial a un decimal. La descarga queda versionada con SHA-256 y la promoción rechaza truncamientos.

- `2019-Q3` no incluye Gran Resistencia.
- `2020-Q3` no incluye Ushuaia–Río Grande.

