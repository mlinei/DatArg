# Metodologías candidatas — no aprobadas

Este documento registra propuestas de Etapa 1. Ninguna serie calculada se publicará hasta aprobar componentes, frecuencia y reglas de valuación.

## Reservas internacionales

### Brutas

Usar el saldo oficial diario del BCRA en millones de USD. Estado: `official`. No recalcular desde el balance.

### Netas — candidato RIN corriente

```text
RIN_corriente = reservas_brutas
              - swap_y_lineas_de_liquidez_utilizadas
              - encajes_sobre_depositos_en_moneda_extranjera
              - pasivos_con_SEDESA
              - pasivos_ALADI_BIS_y_otros_pasivos_de_reservas
              - repos_y_otras_obligaciones_con_garantia_sobre_reservas
              + ajustes_explicitos_aprobados
```

Esta lista concuerda conceptualmente con la definición citada por BCRA y FMI, pero **no constituye aún una serie**. Cada componente debe tener fuente, fecha, moneda, signo y regla de valuación. El swap no activado no se suma a reservas brutas ni se resta; el tramo activado incluido en brutas se resta como pasivo. Estado futuro: `calculated`, nunca `official`.

### RIN del programa FMI

Debe ser otra serie, porque usa tipos de cambio de programa, adjustors y tratamiento específico del crédito neto FMI. No debe mezclarse con RIN corriente. Identificador sugerido: `bcra_nir_imf_program_definition`.

### Líquidas — escenarios para aprobación

- `liquid_a`: RIN corriente menos oro.
- `liquid_b`: RIN corriente menos oro y DEG.
- `liquid_c`: activos de disponibilidad inmediata identificados positivamente, netos de pasivos exigibles inmediatos.

Se recomienda `liquid_c` sólo si estados contables/notas permiten identificar restricciones; en caso contrario, publicar A y B como escenarios, no como un único dato verdadero. Estado: `estimated`.

## Deuda consolidada

### Perímetro propuesto

1. Deuda bruta de la Administración Central/Tesoro por instrumento y acreedor.
2. Pasivos financieros del BCRA frente al sector privado y no residentes.
3. Eliminación de posiciones recíprocas Tesoro–BCRA y, si el perímetro se amplía, posiciones con otros organismos incluidos.

```text
consolidada = deuda_tesoro_bruta
            + pasivos_financieros_bcra_incluidos
            - deuda_tesoro_en_poder_del_bcra
            - otros_activos_pasivos_cruzados_dentro_del_perimetro
```

No sumar base monetaria por defecto. Reportarla como pasivo monetario en una variante analítica separada. No restar reservas hasta tener una medición consolidada bruta validada; luego publicar `consolidada_neta_reservas` como derivada separada, con la variante de reservas indicada.

### Unidades

- Stock nominal en moneda original para auditoría.
- Millones de USD al tipo de cambio oficial de fin de período, con serie de TC identificada.
- Porcentaje del PIB sólo con PIB nominal y regla de ventana documentados.
- ARS constantes como vista adicional, indicando deflactor y base.

La frecuencia inicial recomendada es trimestral, porque es la intersección más defendible entre composición por acreedor del Tesoro, estados del BCRA y datos de PIB. Una versión mensual sólo debe publicarse si todos los cruces pueden actualizarse mensualmente.

