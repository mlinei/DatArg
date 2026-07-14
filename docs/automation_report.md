# Reporte de automatización — Etapa 1

## Resultado

- **Automáticas:** IPC general/núcleo/regulados/estacionales, IPIM (sujeto a fijar CSV exacto), reservas brutas y buena parte de los pasivos BCRA.
- **Semiautomáticas:** EMAE general/sectorial, pobreza regional/nacional y deuda del Tesoro. Son archivos oficiales estructurados, pero requieren descubrimiento de enlace y validación estricta del libro.
- **Manual controlada:** swap activado, otros pasivos de reservas, reservas netas/líquidas y deuda consolidada.

## Política de operación recomendada

1. Descargar a una ruta inmutable con sello UTC y hash SHA-256.
2. Validar MIME, tamaño, esquema, hojas, columnas, claves y cobertura antes de promover.
3. Comparar con la versión anterior y generar un log de altas, bajas y modificaciones.
4. Fallar de forma visible ante un esquema desconocido; nunca producir un CSV vacío “exitoso”.
5. Requerir archivo de aprobación para entradas manuales o metodologías complejas.

## Alertas específicas

- Migrar directamente a API BCRA v4; v3 figura depreciada desde 2026-02-28.
- Tratar la URL de cada informe mensual como descubrimiento, no como contrato estable.
- Para EMAE, distinguir revisión ordinaria de pérdida de observaciones.
- Para pobreza, usar clave `(indicador, universo, geografía, período)`; no sólo fecha.
- No completar automáticamente componentes faltantes de reservas o consolidación.

