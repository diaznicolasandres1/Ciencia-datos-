# Fundamentación y diseño del análisis

## 1. Propósito

Este es un **análisis exploratorio de datos (EDA)**. Busca identificar patrones
y casos que merezcan preguntas posteriores, no establecer que una variable
cause a otra. La pregunta central compara el apoyo popular con el resultado del
Colegio Electoral y estudia si esa relación cambia cuando crece el voto a otras
candidaturas o el electorado total.

## 2. Estado del arte y contexto institucional

Estados Unidos elige indirectamente a la presidencia: los votos populares se
agregan mediante reglas estatales para asignar electores. Por eso el ganador del
voto popular nacional puede no coincidir con el ganador electoral. La FEC reúne
los resultados oficiales por ciclo y la Oficina del Historiador de la Cámara
publica series históricas electorales desde 1920. Ambos organismos priorizan la
descripción y preservación de resultados; este trabajo agrega una capa
reproducible para comparar márgenes entre elecciones.

La literatura cuantitativa distingue entre asociación y explicación causal. En
una serie temporal corta, tendencias como crecimiento poblacional, cambios en
participación y reformas administrativas pueden producir correlaciones
espurias. En consecuencia, se informan tamaño muestral, diagramas de dispersión,
Pearson y Spearman, pero no valores *p* ni lenguaje causal.

## 3. Fuentes y criterios de selección

Se priorizaron fuentes porque:

1. **Autoridad:** FEC y Cámara de Representantes son fuentes gubernamentales
   primarias.
2. **Comparabilidad:** los informes permiten reconstruir las mismas variables
   para cada elección.
3. **Cobertura:** 1976–2020 incluye doce ciclos y alternancias partidarias.
4. **Granularidad adecuada:** una fila representa una elección nacional.
5. **Auditabilidad:** se preservan conteos, candidatos y año; las variables
   analíticas se calculan en el notebook.

Fuentes consultadas (1 de octubre de 2026):

- [FEC — Election results and voting information](https://www.fec.gov/introduction-campaign-finance/election-results-and-voting-information/).
- [U.S. House — Election Statistics, 1920 to Present](https://history.house.gov/Institution/Election-Statistics/Election-Statistics/).

## 4. Variables e hipótesis exploratorias

- **Margen popular bipartidista:** diferencia porcentual Demócrata–Republicano
  calculada sobre la suma de ambos. Evita que el peso variable de terceros
  partidos altere el denominador de la comparación principal.
- **Margen electoral:** diferencia porcentual de electores Demócrata–Republicano
  sobre los 538 disponibles.
- **Voto a otras candidaturas:** porcentaje del total fuera de los dos partidos.
- **Volumen total:** votos emitidos, usado descriptivamente; no equivale a
  participación porque falta el denominador de población elegible.

Hipótesis para explorar: (H1) los márgenes popular y electoral tienen asociación
positiva; (H2) esa asociación no es perfectamente lineal por las reglas del
Colegio Electoral; (H3) una mayor proporción de terceros puede coincidir con
elecciones más competitivas. Las hipótesis no se presentan como pruebas
confirmatorias.

## 5. Método

1. Validar tipos, unicidad, periodicidad y sumas.
2. Derivar porcentajes sin modificar la fuente.
3. Presentar descriptivos y series temporales.
4. Calcular correlaciones de Pearson (relación lineal) y Spearman (orden
   monotónico).
5. Identificar discrepancias entre ganador popular bipartidista y ganador
   electoral, e interpretar los resultados con cautela.

## 6. Limitaciones y próximos pasos

- **n = 12** es insuficiente para generalizaciones fuertes.
- Las observaciones temporales no son independientes y contienen tendencia.
- El agregado nacional oculta diferencias estatales y reglas de asignación.
- `total_votes` no mide turnout; para ello se requiere población elegible.
- La categoría `other_votes` agrupa opciones heterogéneas.
- Una correlación no demuestra causalidad ni fraude, sesgo o eficacia de campaña.

La siguiente iteración debería incorporar resultados por estado, población en
edad/elegible para votar, educación, ingreso y urbanización desde fuentes
oficiales (Census/ACS), armonizando año y geografía. Se deberían preregistrar
hipótesis, ajustar por múltiples comparaciones y ensayar modelos multinivel o de
panel en lugar de interpretar correlaciones bivariadas como efectos.
