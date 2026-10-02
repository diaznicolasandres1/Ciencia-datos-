# Elecciones presidenciales de Estados Unidos

Trabajo de ciencia de datos: construir un dataset estatal, explorar elecciones de 2000–2024 y evaluar modelos con separación temporal. El repositorio contiene código, archivos fuente descargados, un dataset maestro y un informe ejecutado. **No contiene una predicción de 2028.**

El [informe del trabajo práctico](INFORME.md) explica el proceso, los resultados, la incorporación de Census y las revisiones necesarias para la entrega. Census ya está descargado para 2008–2024; la clave no está guardada en el repositorio y no es necesaria para reutilizar estos archivos.

## Ejecutar

Requiere Python 3.12. En este entorno:

```bash
cd /workspace/Ciencia-datos-
source /workspace/.venvs/ciencia-datos/bin/activate
python build_dataset.py --offline --allow-partial
python analyze.py
python -m pytest -q
```

En otra máquina:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python build_dataset.py --allow-partial
python analyze.py
python -m pytest -q
```

PowerShell: activar con `.venv\Scripts\Activate.ps1`.

`--offline` nunca descarga. Los archivos ya presentes se reutilizan. `--allow-partial` permite generar un dataset incompleto y registra los problemas; sin esa opción, cualquier fuente requerida pendiente termina con error y no reemplaza el CSV. Consultar siempre `data/processed/data_quality.json` para conocer el estado. La reconstrucción sin conexión es posible con los datos incluidos.

## Archivos

- `build_dataset.py`: descarga, limpieza, joins validados y controles de calidad.
- `analyze.py`: voto popular, estados competitivos y backtest temporal.
- `requirements.txt`: versiones exactas del entorno probado.
- `data/raw/`: archivos originales; el CSV de encuestas está comprimido sin alterar sus datos.
- `data/raw/manifest.json`: URL de origen, tamaño y SHA-256 de cada archivo.
- `data/processed/elections_master.csv`: 357 filas, una por estado/DC y elección.
- `data/processed/data_quality.json`: faltantes, problemas y límites.
- `reports/analisis.md`: resultados y gráficos del análisis inicial.
- `reports/backtest_predictions.csv`: probabilidades históricas fuera del entrenamiento.
- `tests/`: controles de agregación, rezagos, integridad y ausencia de resultados actuales entre las entradas.

## Fuentes y metodología

1. **Resultados 1976–2020, MIT/MEDSL**, copia pública de Plotly: [CSV](https://raw.githubusercontent.com/plotly/Figure-Friday/main/2024/week-33/1976-2020-president.csv). Dataset original: [Harvard Dataverse, DOI 10.7910/DVN/42MVDX](https://doi.org/10.7910/DVN/42MVDX). Dataverse devuelve 403 en este entorno; se identifica explícitamente el mirror utilizado. El año 1996 se conserva durante el procesamiento para calcular el rezago de 2000.
2. **Resultados 2024, MEDSL**: [repositorio oficial](https://github.com/MEDSL/2024-elections-official). Descarga correspondiente al commit `df531089c78e6d0098db1a6bfb3849a066a06995`; versión del CSV `2025-11-20`. Se suman líneas partidarias de los candidatos y se evita sumar TOTAL junto con sus modos de votación.
3. **Encuestas históricas, FiveThirtyEight**: [documentación](https://github.com/fivethirtyeight/data/tree/master/polls). Archivo 1968–2016. Se conserva la última estimación por candidatura hasta el 31 de octubre, con antigüedad máxima de 30 días, para las elecciones 2000–2016. No es el promedio de todas las encuestas del año. El archivo fue reconstruido/publicado retrospectivamente en 2020; se usa para exploración, **no como predictor en el backtest**. No se rellenan artificialmente 2020/2024. Los antiguos enlaces de FiveThirtyEight para 2020 redirigen a HTML, no a CSV.
4. **Economía, FRED**: UNRATE (desempleo), CPIAUCSL (precios) y GDPC1 (PIB real), CSV públicos sin API key. Se usan promedios del año anterior a la elección y variaciones interanuales de esos promedios. Los datos son revisados: para una evaluación estricta de información conocida en cada fecha hay que incorporar vintages/fechas de publicación.
5. **Demografía, Census ACS**: ACS 1-year de 2006 para 2008; ACS 5-year de `año electoral − 2` desde 2012. ACS 5-year comienza en 2009, por lo que el endpoint 2008/acs5 del script previo era inválido. No se inventa demografía para 2000/2004. Para 2006/2010 se utilizan B15002 (educación), B23001 (empleados/desempleados civiles por sexo y edad) y B03001 (población hispana), porque algunas tablas modernas no existen en esos años. El Census responde `Missing Key` sin credencial: las descargas nuevas requieren `CENSUS_API_KEY`.

Las claves de unión son `year` + `state_fips` para Census y `year` + `state_po` para encuestas; FRED se une por año con cardinalidad muchos-a-uno. Los porcentajes electorales usan el total oficial incluyendo terceros partidos. Poblaciones racial y étnica se solapan: `hispanic_pct` no debe sumarse a `white_pct` y `black_pct`. Educación usa población de 25 años o más; pobreza usa el universo de personas para quienes se determina pobreza; desempleo ACS usa fuerza laboral civil.

## Credencial para nuevas descargas

Solicitar una clave en [Census](https://api.census.gov/data/key_signup.html) y guardarla de forma segura como `CENSUS_API_KEY` en la configuración del entorno. No incluirla en archivos, commits ni chat. El script reutiliza la variable si existe y no muestra su valor ni URLs que la contengan. Después:

```bash
python build_dataset.py
python analyze.py
python -m pytest -q
```

Los años 2000/2004 seguirán sin demografía y 2020/2024 sin encuestas; están documentados como límites estructurales, incluso cuando las fuentes configuradas se descarguen correctamente.

## Variables y evaluación

Identificadores: `year`, `state`, `state_po`, `state_fips`, `state_year`. Resultados observados: votos, `dem_pct`, `rep_pct`, `margin`, `winner`, `target_democrat`. **Estos resultados actuales son etiquetas o datos descriptivos, nunca predictores de esa misma elección.** Rezagos: `previous_*`, con año previo explícito. Variables de encuestas: `poll_dem`, `poll_rep`, `poll_margin`. Economía y Census tienen año de referencia explícito; los valores faltantes permanecen vacíos en el CSV.

El modelo inicial solo usa `previous_margin` y `previous_dem_pct`. Entrena con elecciones anteriores y evalúa cada elección de 2008–2024 por separado; compara una regresión logística con repetir el ganador previo. No utiliza una partición aleatoria de estados. El baseline resulta tan bueno o mejor en todas las elecciones evaluadas, por lo que no se sostiene una mejora predictiva. Además se comparan, sobre las mismas filas con ACS, dos modelos con y sin educación, edad y pobreza para 2016/2020/2024. Agregar Census mejora 2020 y empeora 2024; los resultados están en `reports/census_model_comparison.csv`.

No se incluyen asignaciones del Colegio Electoral sin verificar las tablas históricas. Maine y Nebraska requieren información por distrito; una simulación presidencial debería considerar además errores correlacionados entre estados. Más filas estatales no equivalen a más elecciones independientes.

Para la entrega universitaria falta incorporar la consigna formal/rúbrica, si exige técnicas o formatos específicos. Las atribuciones anteriores identifican las fuentes; revisar sus términos antes de redistribuir los datos fuera del proyecto.
