# Recaudación y resultado fiscal

## Alcance

El pipeline `aed fiscal` reúne dos publicaciones del Ministerio de Economía desde enero de 2017:

- recaudación de tributos nacionales por mes;
- resultado primario y resultado financiero del Sector Público Nacional no Financiero, base caja.

El resultado primario se mide antes de intereses. El resultado financiero incorpora los intereses y es la medida que DatArg presenta como resultado fiscal total.

## Transformaciones

Los importes oficiales se conservan en millones de pesos corrientes. Para hacer comparables los niveles mensuales se dividen por el IPC nacional del INDEC y se expresan a precios de diciembre de 2025. La variación real interanual de la recaudación compara esos niveles deflactados contra igual mes del año anterior.

Las vistas anuales reales suman los doce meses ya deflactados. Los porcentajes del PIB suman los doce resultados nominales y los dividen por el PIB anual a precios corrientes publicado por INDEC. No se publica un porcentaje anual para años incompletos.

## Actualización y controles

La ejecución habitual descubre y descarga la última planilla disponible de cada publicación y la combina con el historial promovido. `--refresh-history` recorre las planillas oficiales desde 2017. El extractor busca las etiquetas oficiales y las fechas dentro de cada libro para tolerar los cambios históricos de filas y nombres de hojas.

La salida es `data/processed/fiscal.csv`. Los cálculos reales requieren `data/processed/inflation.csv` y los porcentajes del PIB requieren `data/processed/gdp.csv`.

Fuentes:

- [Recaudación tributaria por mes](https://www.argentina.gob.ar/economia/ingresospublicos/pormes)
- [Sector Público Base Caja e IMIG](https://www.argentina.gob.ar/economia/sechacienda/infoestadistica)
