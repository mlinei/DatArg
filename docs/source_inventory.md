# Inventario de fuentes — Etapa 1

**Corte de investigación:** 2026-07-10  
**Alcance:** investigación y viabilidad. No se descargaron ni transformaron observaciones en esta etapa.

## Criterios

- Se prioriza fuente oficial primaria y recurso estructurado estable.
- `Automática`: API o URL estable y legible por máquina.
- `Semiautomática`: archivo oficial estructurado, pero con URL, libro o esquema susceptible de cambiar.
- `Manual controlada`: PDF, dato no publicado con granularidad suficiente o decisión metodológica que requiere aprobación.
- “Nacional” en pobreza significa **total de 31 aglomerados urbanos de la EPH**, no toda la población del país.
- El “último dato” es lo observado al corte y debe ser verificado por el futuro extractor en cada ejecución.

## Matriz de viabilidad

| Módulo | Serie | Fuente | Desde comparable | Frecuencia | Formato | Automatización | Viabilidad | Riesgos |
|---|---|---:|---:|---|---|---|---|---|
| Inflación | IPC general, mensual | INDEC | 2016-12 (variación desde 2017-01) | Mensual | CSV/XLS | Automática | Alta | Revisiones; cambio de base/esquema |
| Inflación | IPC núcleo | INDEC | 2016-12 | Mensual | CSV/XLS | Automática | Alta | Etiquetas y columnas multicapa |
| Inflación | IPC regulados | INDEC | 2016-12 | Mensual | CSV/XLS | Automática | Alta | Ídem |
| Inflación | IPC estacionales | INDEC | 2016-12 | Mensual | CSV/XLS | Automática | Alta | Ídem |
| Inflación | IPIM general | INDEC | 2015-12 | Mensual | CSV/XLS | Automática | Alta | Base de referencia dic-2015; revisiones |
| Actividad | EMAE general, índice original e interanual | INDEC | 2004 | Mensual | XLS | Semiautomática | Alta | Libro reemplazado; revisiones frecuentes |
| Actividad | EMAE desestacionalizado, índice y mensual | INDEC | 2004 | Mensual | XLS | Semiautomática | Alta | Revisión de toda la historia por ajuste estacional |
| Actividad | EMAE por sector, índice/interanual | INDEC | 2004 | Mensual | XLS | Semiautomática | Alta | Clasificación sectorial y revisiones |
| Pobreza | Personas pobres e indigentes, total 31 aglomerados | INDEC | 2016-T2; luego semestres desde 2016-S2 | Semestral | XLS | Semiautomática | Alta | Primer punto trimestral no equivale a semestre |
| Pobreza | Personas pobres e indigentes por 6 regiones | INDEC | 2016-S2 | Semestral | XLS | Semiautomática | Alta | No confundir GBA con cobertura nacional |
| Reservas | Reservas internacionales brutas | BCRA | 1996-01-03 | Diaria | API v4 / TXT | Automática | Alta | Provisorias; valuación; versionado API |
| Reservas | Encajes/depósitos en moneda extranjera | BCRA | Al menos 2003 en IMD | Diaria/mensual | API v4/XLSX/TXT | Automática | Alta | Elegir saldo diario vs promedio mensual |
| Reservas | Swap PBoC activado | BCRA/FMI | Variable | Trimestral/discontinua | EECC/PDF | Manual controlada | Media-baja | Stock activado no aparece como serie diaria pública estable |
| Reservas | Otros pasivos de reservas (SEDESA, ALADI, BIS, repo) | BCRA/FMI | Variable | Trimestral/discontinua | EECC/PDF | Manual controlada | Media-baja | Granularidad y valuación insuficientes |
| Reservas | Reservas netas | Cálculo propio con definición aprobada | No fijado | Mensual inicialmente | Mixto | Manual controlada | Media | Varias definiciones legítimas; componentes no diarios |
| Reservas | Reservas líquidas | Cálculo propio | No fijado | Mensual/trimestral | Mixto | Manual controlada | Baja | “Liquidez” no tiene definición oficial única |
| Deuda | Deuda pública bruta del Tesoro | Secretaría de Finanzas | 2019 mensual; 2004 trimestral/gráfica | Mensual | XLSX | Semiautomática | Alta | URL/estructura del libro; valuación en USD |
| Deuda | Deuda del Tesoro por acreedor (incl. sector público) | Secretaría de Finanzas | Serie trimestral disponible | Trimestral | XLSX/PDF | Semiautomática | Alta | Necesaria para consolidar; cobertura puede cambiar |
| Deuda | Pasivos relevantes del BCRA | BCRA | 2003 (IMD; algunas series más antiguas) | Diaria/mensual | API v4/XLSX/TXT | Automática | Alta | Cambios de instrumentos: LEBAC/LELIQ/pases/BOPREAL |
| Deuda | Consolidada Tesoro+BCRA | Cálculo propio | No fijado | Mensual o trimestral | Mixto | Manual controlada | Media-baja | Tenencias cruzadas, unidades y perímetro institucional |
| Deuda | Consolidada neta de reservas | Cálculo propio | No fijado | Trimestral recomendado | Mixto | Manual controlada | Baja | Combina dos metodologías aún no aprobadas |

## Fuentes por módulo

### Inflación

**Página IPC:** https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-31  
**CSV divisiones/categorías (general, estacionales, núcleo y regulados):** https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv  
**CSV aperturas regionales:** https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_aperturas.csv  
**CSV divisiones:** https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv  
**XLS de aperturas:** https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipc_aperturas.xls  
**Metadatos:** https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_metadatos.txt

La serie nacional actual comienza en diciembre de 2016; la primera variación mensual utilizable es enero de 2017. No debe empalmarse silenciosamente con IPCNu o IPC-GBA. Los CSV estables permiten clasificar las aperturas como automáticas. El recurso contiene índices y variaciones; conviene conservar el índice oficial y la variación publicada, y validar esta última contra el cálculo.

**Página SIPM/IPIM:** https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-32  
**XLS oficial:** https://www.indec.gob.ar/ftp/cuadros/economia/series_sipm_dic2015.xls

El IPIM base de referencia diciembre de 2015 ofrece nivel y variación mensual. La página también anuncia CSV históricos; el extractor deberá descubrir y fijar la URL exacta desde el enlace oficial, con validación de esquema.

### Actividad económica

**Página EMAE:** https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-9-48  
**Metodología:** https://www.indec.gob.ar/ftp/cuadros/economia/metodologia_emae_ago_16.pdf

INDEC publica dos libros históricos: EMAE general (serie original, desestacionalizada y tendencia-ciclo; índices y variaciones) y EMAE por sector (base 2004=100). La cobertura oficial es 2004–último dato. Se recomienda usar desde 2015 sin recortar los brutos. Es semiautomática porque la página reemplaza libros y el vínculo directo puede cambiar. Las revisiones son parte normal de cuentas nacionales y del ajuste estacional.

### Pobreza e indigencia

**Página oficial:** https://www.indec.gob.ar/indec/web/Nivel4-Tema-4-46-152  
**Metodología:** https://www.indec.gob.ar/ftp/cuadros/sociedad/EPH_metodologia_22_pobreza.pdf  
**Archivo histórico/advertencia:** https://www.indec.gob.ar/indec/web/Institucional-Indec-InformacionDeArchivo-1

La publicación normalizada se reanudó con el segundo trimestre de 2016; desde el segundo semestre de 2016 hay cuadros semestrales comparables para 31 aglomerados y seis regiones estadísticas. El punto 2016-T2 debe conservar `period_label` y no renombrarse como 2016-S1. Las series 2007–2015 deben considerarse con reservas salvo revisión explícita de INDEC; no se incorporarán al tramo comparable.

### Reservas y componentes BCRA

**API oficial:** https://www.bcra.gob.ar/apis-banco-central/  
**Manual v4:** https://www.bcra.gob.ar/archivos/Catalogo/Content/files/pdf/principales-variables-v4.pdf  
**Informe Monetario Diario:** https://www.bcra.gob.ar/informe-monetario-diario/  
**TXT histórico de reservas y pasivos:** https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/din2_ser.txt  
**Página de reservas y liquidez:** https://www.bcra.gob.ar/reservas-internacionales-y-base-monetaria/

La API `Estadísticas Monetarias v4.0` reemplaza versiones depreciadas y debe ser la vía principal. La reserva bruta es oficial, diaria y provisional, sujeta a valuación. El IMD/API contiene depósitos en moneda extranjera, depósitos del Gobierno y pasivos monetarios. Los estados contables y el FMI son necesarios para swap y otros pasivos de reservas; no alcanzan para una reconstrucción diaria homogénea.

**Definición de referencia RIN (FMI 2025):** reservas brutas menos líneas swap, seguro de depósitos, encajes sobre depósitos FX y otros pasivos de reservas; el programa aplica tipos de cambio específicos y ajustes al crédito neto del FMI. Fuente: https://www.imf.org/en/-/media/files/publications/cr/2025/english/1argea2025002-print-pdf.pdf

### Deuda del Tesoro y pasivos BCRA

**Portal de deuda:** https://www.argentina.gob.ar/economia/finanzas/datos  
**Serie mensual (2019–último dato):** https://www.argentina.gob.ar/economia/finanzas/datos-mensuales  
**Explicación del reporte:** https://www.argentina.gob.ar/economia/finanzas/datos-mensuales-de-la-deuda  
**BCRA, pasivos diarios:** https://www.bcra.gob.ar/informacion-diaria-reservas-internacionales/  
**OPC, publicaciones:** https://opc.gob.ar/categoria-publicaciones/deuda-publica/

Finanzas publica deuda bruta mensual y bases trimestrales, con composición por acreedor. Para consolidar, el insumo crítico es la deuda del Tesoro en poder del BCRA y otros organismos públicos. Del lado BCRA deben definirse instrumento y contraparte: base monetaria no es automáticamente “deuda”, mientras que títulos/pases/BOPREAL, depósitos FX, swaps y otros pasivos requieren tratamiento explícito. Una suma bruta produciría doble conteo.

## Historial de revisiones y controles futuros

- **IPC/IPIM:** pueden revisarse cuadros o metadatos; versionar cada descarga y comparar claves/valores.
- **EMAE:** valores recientes son preliminares y el ajuste estacional puede revisar la historia completa.
- **Pobreza:** preservar período exacto, universo, coeficientes de variación e intervalos si se incorporan.
- **BCRA:** reservas son provisorias y sujetas a valuación; guardar fecha de consulta y versión de API.
- **Deuda:** cambios de valuación, nueva deuda y reclasificaciones pueden alterar stocks anteriores.

## Bloqueos y decisiones pendientes

1. Aprobar una definición de reservas netas: estadística corriente o la definición programática FMI (con tipos de cambio de programa).
2. Definir “líquidas”: si excluye oro, DEG y/o activos restringidos; no hay estándar oficial único.
3. Conseguir/validar series históricas del swap activado y otros pasivos de reservas con frecuencia consistente.
4. Fijar perímetro de deuda consolidada (Administración Central, Tesoro o sector público nacional) y pasivos BCRA incluidos.
5. Elegir unidad primaria de consolidación: USD a tipo de cambio de fin de período, ARS constantes y/o % del PIB. Se recomienda publicar más de una, sin tratarlas como equivalentes.
6. Determinar tratamiento de base monetaria. Recomendación inicial: mostrarla como pasivo monetario BCRA separado, no sumarla a deuda financiera por defecto.
7. Definir tratamiento histórico de instrumentos que migraron del BCRA al Tesoro y de BOPREAL.
