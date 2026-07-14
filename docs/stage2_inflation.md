# Etapa 2 — pipeline de inflación

## Alcance

| Familia | Series publicadas | Fuente oficial |
|---|---|---|
| IPC nacional | general, núcleo, regulados y estacionales; índice, mensual e interanual | `serie_ipc_divisiones.csv` |
| IPIM | nivel general; índice y mensual calculada desde el índice oficial | hoja `IPIM`, fila `NG`, de `series_sipm_dic2015.xls` |

Corrección a la Etapa 1: `serie_ipc_aperturas.csv` contiene aperturas regionales, pero no las cuatro categorías nacionales. El contrato automático correcto para este alcance es `serie_ipc_divisiones.csv`.

## Contrato de salida

`data/processed/inflation.csv` usa una observación por `(series_id, period)` y las columnas:

- `series_id`, `period` (`AAAA-MM`), `frequency`, `value`, `unit`, `status`;
- `source_id`, `source_url`, `source_sha256`, `retrieved_at`.

Los índices y variaciones IPC son oficiales (`status=official`). Para IPIM, el índice es oficial y la variación mensual se deriva sin redondeo intermedio del índice publicado (`status=calculated`).

No se empalma el IPC nacional con IPCNu o IPC-GBA. Diciembre de 2016 se conserva como base y la variación mensual comienza en enero de 2017. IPIM comienza en diciembre de 2015.

## Controles y promoción

Cada descarga se almacena en una ruta inmutable con manifiesto, fecha UTC, tamaño y SHA-256. Los extractores validan esquema, hoja, fila, calendario, cobertura, unicidad y valores positivos. En IPC se exige un panel balanceado de cuatro categorías y se acepta como máximo 0,16 puntos porcentuales entre la variación oficial redondeada y la reconstruida desde índices.

La salida se escribe primero a un archivo temporal, se sincroniza y se reemplaza atómicamente. Cada corrida registra altas, bajas y modificaciones; una baja respecto de la versión promovida detiene el proceso para evitar truncamientos silenciosos.
