# Pipeline de salarios

## Fuente y cobertura

El pipeline usa el CSV oficial y actualizable del INDEC `indice_salarios.csv`. Publica índices mensuales para el total, total registrado, privado registrado, público y privado no registrado. La serie nominal total comienza en octubre de 2016; las series registradas tienen observaciones desde octubre de 2015.

El sector privado no registrado es estimado por el INDEC a partir de la Encuesta Permanente de Hogares. No representa por sí solo toda la informalidad laboral.

## Salario real

Para cada segmento y mes común se calcula:

`índice real = (índice salarial / IPC) / (índice salarial dic-2016 / IPC dic-2016) × 100`

Así, diciembre de 2016 vale 100. Un valor superior a 100 indica mayor poder adquisitivo que en esa base y uno inferior indica menor poder adquisitivo. No se obtiene restando niveles ni variaciones mensuales.

Para los índices nominales y reales también se calcula la variación contra el mes inmediatamente anterior: `(índice_t / índice_t-1 - 1) × 100`.

## Ejecución

```bash
aed inflation
aed wages
```

La segunda orden requiere `data/processed/inflation.csv`. La salida promovida es `data/processed/wages.csv`.
