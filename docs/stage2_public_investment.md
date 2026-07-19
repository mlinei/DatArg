# Inversión pública y gastos de capital

## Alcance

El pipeline `aed public-investment` importa la planilla consolidada de la Dirección Nacional de Inversión Pública. Publica dos universos que deben interpretarse por separado:

- inversión pública de la Administración Pública Nacional, medida por devengado, desde 1995;
- gastos de capital del Sector Público Nacional, medidos por base caja, desde 1997.

Para ambos se conserva el índice real oficial con base 2019=100 y la relación con el PIB. También se importan las aperturas funcionales disponibles: desde 1995 para inversión pública y desde 2016 para gastos de capital.

## Criterio de publicación

La inversión pública incluye inversión real directa, transferencias de capital y anticipos de proyectos prioritarios definidos por la metodología oficial. El gasto de capital agrega inversión real directa, transferencias e inversión financiera, pero usa otro universo institucional y momento de registro; por eso las dos magnitudes no se suman ni se sustituyen entre sí.

Las columnas cuyo año contiene un asterisco se consideran proyecciones, estimaciones o crédito vigente. DatArg las excluye: la serie promovida termina en el último año ejecutado completo, actualmente 2025.

## Controles

El extractor valida que las series reales tengan base 2019=100, que los componentes funcionales en porcentaje del PIB sumen el total de inversión pública, que no haya claves duplicadas y que una actualización no elimine observaciones ya publicadas.

La salida es `data/processed/public_investment.csv`.

Fuentes:

- [Portal de Datos de Inversión Pública](https://www.argentina.gob.ar/jefatura/presupuestaria/inversion-publica/portal-de-datos-de-inversion-publica)
- [Metodología de inversión pública](https://www.argentina.gob.ar/sites/default/files/metodologia_de_inversion_publica.pdf)
