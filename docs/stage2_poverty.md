# Etapa 2 — pobreza e indigencia

## Alcance

Se importan las tasas oficiales de personas bajo la línea de pobreza y bajo la línea de indigencia, expresadas como porcentaje de personas. El universo nacional es el total de 31 aglomerados urbanos relevados por la EPH; no representa a toda la población del país.

Las geografías publicadas son el total y seis regiones: Gran Buenos Aires, Cuyo, Noreste, Noroeste, Pampeana y Patagonia. La cobertura comparable del libro histórico comienza en `2016-S2` y llega hasta `2025-S2` en la corrida del 11 de julio de 2026. El dato extraordinario de `2016-T2` no se incorpora a esta serie semestral ni se renombra como `2016-S1`.

## Contrato

`data/processed/poverty.csv` contiene 14 series y utiliza una clave `(series_id, period)`. La frecuencia es `semiannual`, la unidad `percent_of_persons` y el estado `official`. Cada observación conserva URL, fecha de recuperación y SHA-256 del libro de origen.

## Controles y advertencias

Se validan las hojas históricas `Cuadro 4.3` y `Cuadro 4.4`, la secuencia exacta de semestres, columnas de personas, siete geografías, porcentajes entre 0 y 100 y claves únicas. La promoción es atómica y rechaza pérdidas de observaciones.

- `2019-S2` no incluye Gran Resistencia.
- `2020-S2` no incluye Ushuaia–Río Grande.

Estas excepciones se preservan en el reporte de cada corrida. La URL del libro cambia con cada publicación, por lo que debe actualizarse desde la página oficial y validarse antes de ejecutar una nueva edición.

