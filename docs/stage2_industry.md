# Etapa 2 — industria manufacturera

## Alcance

Se publica el Índice de producción industrial manufacturero (IPI manufacturero) oficial del INDEC, base 2004=100 y frecuencia mensual. Incluye el nivel general y 16 divisiones de la clasificación CLaNAE 2004.

Para cada apertura se conservan tres series oficiales: número índice original, variación interanual y variación acumulada del año respecto del mismo acumulado del año anterior. La cobertura comienza en enero de 2016 y llega a mayo de 2026 en la corrida del 11 de julio de 2026.

Las divisiones incluyen alimentos y bebidas; tabaco; textiles; prendas, cuero y calzado; madera, papel e impresión; refinación de petróleo; químicos; caucho y plástico; minerales no metálicos; metales básicos; productos de metal; maquinaria; otros equipos e instrumentos; automotores; otro equipo de transporte; y muebles y otras manufacturas.

## Fuente y controles

La fuente es `sh_ipi_manufacturero_2026.xls`, publicado en la página oficial del IPI. Se validan las hojas 2, 3 y 4, la clasificación exacta de divisiones, calendario, cobertura, valores positivos de los índices y claves únicas. Cada variación interanual se reconstruye desde los índices y cada acumulada se contrasta usando los promedios enero–mes de ambos años.

El libro queda versionado con sello UTC y SHA-256. La promoción es atómica y rechaza pérdidas de observaciones. La URL del archivo cambia por año y debe verificarse desde la página oficial.

