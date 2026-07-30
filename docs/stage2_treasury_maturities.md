# Esquema de vencimientos del Tesoro

## Alcance

DatArg importa el perfil mensual proyectado de servicios de la deuda de la Administración Central publicado por la Secretaría de Finanzas. El indicador separa capital e intereses y conserva el detalle oficial por instrumento.

No representa pagos efectivamente realizados. Es una foto del cronograma vigente a la fecha de corte del informe, por lo que una reestructuración, licitación, recompra o nueva operación de deuda puede modificar vencimientos futuros.

## Fuente y cobertura

- Índice oficial: `https://www.argentina.gob.ar/economia/finanzas/datos-trimestrales-de-la-deuda`
- Libro utilizado por el pipeline: la planilla trimestral más reciente cuyo nombre responde a `deuda_publica_DD-MM-YYYY.xlsx`.
- Hojas: `A.3.2`, `A.3.3`, `A.3.4` y `A.3.5`.
- Unidad: millones de USD, valuados con los tipos de cambio de la fecha de corte indicada en el libro.

Cada ejecución descubre el último libro disponible. Al publicar una nueva foto no elimina las anteriores: `snapshot_date` permite comparar qué cronograma se conocía en cada cierre trimestral.

## Validaciones

Antes de publicar, el pipeline comprueba:

1. que la cobertura comience en el mes posterior a la fecha de corte y llegue hasta diciembre del año siguiente;
2. que existan capital e intereses para todos los meses cubiertos;
3. que préstamos, adelantos transitorios del BCRA y títulos públicos/Letras del Tesoro sumen el total mensual oficial;
4. que no haya claves duplicadas dentro de la misma foto.

Las filas jerárquicas del libro se conservan para trazabilidad. Los subtotales y sus componentes no deben sumarse entre sí.

## Ejecución

```bash
aed debt-maturities
```

Para reproducir la extracción desde un archivo ya descargado:

```bash
aed debt-maturities --source-file deuda_publica_31-03-2026.xlsx
```

La salida canónica es `data/processed/treasury_maturities.csv`. Drizzle la migra a la tabla `treasury_maturities`, y la API mantiene el mismo contrato CSV para la web y las aplicaciones móviles.
