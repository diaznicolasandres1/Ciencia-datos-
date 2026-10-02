# Elecciones presidenciales de Estados Unidos: análisis exploratorio

Repositorio de trabajo para estudiar relaciones entre el voto popular y el
Colegio Electoral en las elecciones presidenciales de Estados Unidos. El
proyecto incluye una copia local de los datos, la fundamentación metodológica,
un notebook reproducible y una declaración de uso de inteligencia artificial.

## Integrantes

> **Completar antes de entregar:** reemplazar esta tabla con los datos del grupo.

| Nombre y apellido | Legajo/matrícula | Correo | Rol |
|---|---|---|---|
| Pendiente | Pendiente | Pendiente | Análisis y documentación |

## Pregunta y alcance

**Pregunta exploratoria:** ¿cómo se relacionan, entre 1976 y 2020, el margen
bipartidista del voto popular, el margen del Colegio Electoral, la participación
de terceras fuerzas y el volumen total de votos?

La unidad de análisis es cada elección presidencial (12 observaciones). No se
busca probar causalidad ni predecir ganadores: se describen asociaciones,
elecciones atípicas y límites del diseño. La fundamentación completa y el estado
del arte están en [`docs/fundamentacion.md`](docs/fundamentacion.md).

## Estructura

- `data/elecciones_presidenciales_1976_2020.csv`: tabla analítica local.
- `data/README.md`: diccionario, procedencia y decisiones de transcripción.
- `notebooks/analisis_elecciones_eeuu.ipynb`: limpieza, indicadores,
  correlaciones, visualizaciones e interpretación.
- `docs/fundamentacion.md`: selección de fuentes, criterios, hipótesis y límites.
- `docs/declaracion_uso_ia.md`: declaración editable de uso de IA.

## Ejecución

El notebook utiliza únicamente la biblioteca estándar de Python, por lo que no
requiere instalar paquetes. Abrirlo en Jupyter y ejecutar **Run All**. También
puede verificarse desde la terminal con:

```bash
python scripts/validar_datos.py
python scripts/ejecutar_notebook.py
```

Los gráficos se generan como SVG dentro del propio notebook. Para actualizar la
tabla se deben contrastar los valores con los informes oficiales indicados en
`data/README.md` y conservar evidencia de la revisión.
