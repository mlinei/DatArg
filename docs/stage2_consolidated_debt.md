# Deuda neta consolidada — Etapa 2

## Definición publicada

La serie sigue la estimación de Econosignal/Deloitte basada en la guía *Public Sector Debt Statistics* del FMI. No se confunde con la deuda consolidada **bruta** difundida en otros gráficos.

```text
deuda neta del gobierno central = deuda bruta
                                  - FGS de ANSES
                                  - depósitos del Tesoro en el BCRA

deuda neta consolidada del sector público = deuda neta del gobierno central
                                             - adelantos transitorios
                                             - títulos del Tesoro en poder del BCRA
                                             + pasivos remunerados del BCRA
                                             - reservas netas
```

Las reservas netas del informe son reservas brutas menos encajes, swap con China, SEDESA, Bopreal a 12 meses y líneas de crédito. El pipeline no reconstruye silenciosamente esa subserie: importa el componente publicado y valida la identidad completa.

## Cobertura y estado

- Frecuencia: trimestral.
- Cobertura estructurada inicial: `2025-Q2`.
- Estado: `estimated` en todas las filas.
- Unidades: millones de USD y porcentaje del PBI.
- Fuente primaria de la estimación: informe *Diagnóstico macro, noviembre de 2025* de Econosignal/Deloitte, elaborado con datos de MECON y Banco Mundial.

El gráfico histórico 2013–2025 del informe no expone sus observaciones como tabla. Esos puntos no se digitalizan: sólo se incorporarán cuando exista una fuente tabular o sea posible reconstruir cada componente con fuentes oficiales y reglas de valuación equivalentes.

## Serie comparable de largo plazo

DatArg agrega una segunda medición, identificada como `estimated_comparable_net_public_debt`, basada en la planilla abierta que acompaña el análisis metodológico de Chequeado:

```text
deuda estatal neta comparable = deuda de la Administración Central con privados y organismos
                               + pasivos financieros seleccionados del BCRA
                               - reservas netas
```

Se publican solamente los seis cortes tabulados por la fuente (`2003-Q2`, `2007-Q3`, `2015-Q3`, `2019-11`, `2023-11` y `2026-05`); no se interpola entre ellos. El porcentaje del PIB se deriva del PIB implícito en la deuda bruta y el cociente deuda bruta/PIB de la misma planilla, de modo que numerador y denominador respetan un único corte metodológico.

La variante de Facimex citada por Bloomberg Línea es más restrictiva: también descuenta depósitos del Tesoro en pesos y dólares y ajusta el universo de BOPREAL. Su control publicado para `2026-Q1` es USD 254.000 millones, o 36,9% del PIB. Se documenta como contraste, pero no se empalma con la serie de Chequeado porque el perímetro no es idéntico.

## Controles

El proceso conserva el PDF y su SHA-256, exige los siete componentes, recalcula el total, lo compara con el valor publicado (tolerancia de USD 0,01 millones) y promueve atómicamente sólo si la identidad cierra.
