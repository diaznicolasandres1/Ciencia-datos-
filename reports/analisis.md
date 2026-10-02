# Análisis inicial de elecciones presidenciales de EE. UU.

Panel de 357 filas: 50 estados y DC × 7 elecciones (2000–2024). Estado de integración: **available_sources_complete**.

## Voto popular nacional

El porcentaje nacional se calcula sumando votos; no promediando porcentajes estatales. El voto popular no determina por sí solo la presidencia.

| Año | Demócrata % | Republicano % | Margen D−R (pp) |
|---|---:|---:|---:|
| 2000 | 48.14 | 47.65 | 0.49 |
| 2004 | 48.14 | 50.57 | -2.43 |
| 2008 | 52.76 | 45.36 | 7.40 |
| 2012 | 50.92 | 46.98 | 3.94 |
| 2016 | 48.01 | 45.83 | 2.18 |
| 2020 | 51.26 | 46.82 | 4.45 |
| 2024 | 48.27 | 49.74 | -1.47 |

![Voto nacional](figures/national_vote.png)

## Evaluación temporal

Regresión logística con `previous_margin` y `previous_dem_pct`. Para cada elección, se entrena exclusivamente con elecciones anteriores. Se compara con repetir el ganador de la elección previa. Los resultados actuales, encuestas retrospectivas y variables posteriores no se usan como entradas.

| Evaluación | Filas de entrenamiento | Aciertos / 51 | Accuracy | Baseline | Brier | Log loss |
|---|---:|---:|---:|---:|---:|---:|
| 2008 | 102 | 40 | 0.784 | 0.824 | 0.151 | 0.479 |
| 2012 | 153 | 48 | 0.941 | 0.961 | 0.039 | 0.147 |
| 2016 | 204 | 45 | 0.882 | 0.882 | 0.084 | 0.256 |
| 2020 | 255 | 42 | 0.824 | 0.902 | 0.097 | 0.274 |
| 2024 | 306 | 45 | 0.882 | 0.882 | 0.057 | 0.177 |

![Validación](figures/backtest_accuracy.png)

Las filas de una misma elección no son observaciones independientes. Hay solo cinco elecciones de evaluación; una accuracy alta puede provenir de acertar estados seguros. Estas probabilidades no se han calibrado para pronosticar una elección futura.

## Estados competitivos de 2024

![Estados](figures/competitive_states_2024.png)

## Fuentes pendientes y límites

- No hay ACS anterior a 2000/2004 en este pipeline; quedan faltantes.
- Encuestas disponibles solo 2000–2016; archivo retrospectivo publicado en 2020, excluido del modelo predictivo.
- FRED usa valores revisados y el año previo; no constituye un backtest de vintages en tiempo real.
- No se incluyen votos electorales sin verificar las asignaciones históricas y los distritos de ME/NE.
- No es una predicción de 2028.

## Comparación con Census

Se comparan los modelos con y sin educación universitaria, edad y pobreza en las mismas filas con ACS disponible (desde 2008). Las evaluaciones 2016, 2020 y 2024 usan al menos dos elecciones anteriores para entrenar. No deben compararse directamente con el primer backtest, que dispone de más años de entrenamiento.

| Año | Modelo | Filas de entrenamiento | Accuracy | Brier |
|---|---|---:|---:|---:|
| 2016 | historical_same_sample | 102 | 0.863 | 0.106 |
| 2016 | historical_plus_census | 102 | 0.863 | 0.091 |
| 2020 | historical_same_sample | 153 | 0.843 | 0.072 |
| 2020 | historical_plus_census | 153 | 0.902 | 0.071 |
| 2024 | historical_same_sample | 204 | 0.863 | 0.075 |
| 2024 | historical_plus_census | 204 | 0.804 | 0.124 |

## Próximos pasos

Revisar calidad, comparabilidad y fechas de publicación de Census; verificar vintages de FRED; incorporar encuestas de 2020/2024; conseguir asignaciones electorales históricas y datos distritales para Maine y Nebraska. La simulación del Colegio Electoral requiere además modelar errores correlacionados entre estados. Una proyección de 2028 requiere supuestos y datos de ese ciclo.
