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

La variante de Facimex citada por Bloomberg Línea es más restrictiva: también descuenta depósitos del Tesoro en pesos y dólares y ajusta el universo de BOPREAL. Se publica como una serie distinta con un corte por año desde 2023: `2023-Q3`, `2024-Q4`, `2025-Q4` y `2026-Q1`. No se empalma con la serie de Chequeado porque el perímetro no es idéntico.

Los niveles y cocientes de 2025 y 2026 fueron publicados directamente por Facimex/Bloomberg. El corte 2023 surge del nivel 2026 y la diferencia publicada contra 2023. Para 2024, Facimex publicó el cociente de 37,7% del PIB pero no el nivel tabular: DatArg lo deriva aplicando ese cociente al PIB 2024 en dólares corrientes del Banco Mundial (USD 638.365,5 millones), obteniendo USD 240.663,6 millones. Este punto queda identificado como derivado y no como una observación directa.

## Controles

El proceso conserva el PDF y su SHA-256, exige los siete componentes, recalcula el total, lo compara con el valor publicado (tolerancia de USD 0,01 millones) y promueve atómicamente sólo si la identidad cierra.
