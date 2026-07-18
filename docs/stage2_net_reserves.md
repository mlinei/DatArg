# Reservas internacionales netas

## Definición

```text
reservas netas = reservas brutas
               - encajes en moneda extranjera (t-3)
               - swap con China
               - obligaciones con organismos internacionales
               - repos con vencimiento residual de hasta un año
```

Es una reconstrucción de mercado y lleva estado `calculated`. No debe confundirse con la meta de RIN de un programa del FMI, que aplica tipos de cambio y ajustadores propios.

## Componentes

- Reservas brutas: serie diaria oficial del BCRA.
- Encajes: `Cuentas corrientes en otras monedas` del Estado Resumido semanal, convertida por el tipo de cambio del propio balance. Entre balances se aplica el flujo diario de efectivo mínimo (variable 81) y cada nuevo balance vuelve a fijar el nivel.
- OOII: `Obligaciones con organismos internacionales`, netas de la `Contrapartida del uso del tramo de reservas`, del Estado Resumido semanal. El libro está en miles de pesos y se convierte por su tipo de cambio contable.
- Swap China: RMB 130.000 millones convertidos diariamente mediante los tipos CNY/EUR y USD/EUR del Banco Central Europeo.
- Repos: `Egresos relacionados con recompras` de la sección II.3 de la Planilla de Reservas Internacionales y Liquidez en Moneda Extranjera BCRA/FMI, con vencimiento residual total de hasta un año.

Los repos anteriores a junio de 2024 se retroproyectan con el primer saldo oficial recuperado. Esta porción debe considerarse estimada hasta recuperar las planillas archivadas faltantes.

## Controles externos

| Fecha | Brutas | Encajes | Swap | OOII | Repos | Netas |
|---|---:|---:|---:|---:|---:|---:|
| 2026-06-30 | 44.873 | 12.335 | 19.143 | 120 | 8.385 | 4.890 |
| 2026-07-17 | 48.784 | 16.526 | 19.180 | 123 | 2.385 | 10.570 |

Ambas identidades coinciden exactamente con los cuadros publicados por Federico Machado. Los valores preliminares todavía ausentes de la API se preservan como puntos de control explícitos en `data/reference/net_reserves_adjustments.csv`.
