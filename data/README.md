# Datos y trazabilidad

## Procedencia

La tabla `elecciones_presidenciales_1976_2020.csv` es una transcripción
estructurada de los cuadros nacionales publicados por la **Federal Election
Commission (FEC)** en su colección *Federal Elections* para cada ciclo. La
página índice es [Election results and voting information](https://www.fec.gov/introduction-campaign-finance/election-results-and-voting-information/)
(consulta: 1 de octubre de 2026). Como control histórico y documental se usó la
serie [Election Statistics, 1920 to Present](https://history.house.gov/Institution/Election-Statistics/Election-Statistics/)
de la Cámara de Representantes (consulta: 1 de octubre de 2026).

La FEC es la fuente primaria elegida para resultados presidenciales. La serie de
la Cámara es una fuente primaria institucional complementaria, especialmente
útil para extender el análisis hacia elecciones legislativas. Esta versión no
mezcla resultados legislativos porque la unidad de análisis sería distinta.

> **Nota de reproducibilidad:** el entorno de elaboración no permitió descargar
> automáticamente los sitios gubernamentales (respuesta HTTP 403). Por eso se
> conserva una tabla local pequeña, transcripta de las publicaciones oficiales.
> Antes de una entrega formal, dos integrantes deben cotejar cada fila con el
> informe FEC del ciclo y registrar fecha e iniciales de la revisión.

## Diccionario

| Variable | Tipo | Definición |
|---|---|---|
| `year` | entero | Año de la elección presidencial. |
| `dem_candidate`, `rep_candidate` | texto | Candidaturas de los dos partidos principales. |
| `dem_votes`, `rep_votes` | entero | Votos populares nacionales de cada candidatura. |
| `other_votes` | entero | Resto de votos: `total_votes - dem_votes - rep_votes`. |
| `total_votes` | entero | Total nacional informado. |
| `dem_electoral`, `rep_electoral` | entero | Votos electorales obtenidos. |
| `other_electoral` | entero | Votos electorales no asignados a esas dos candidaturas. |
| `winner` | categoría | Partido del ganador del Colegio Electoral. |

El notebook deriva: porcentajes sobre votos totales, margen popular
bipartidista (Demócrata menos Republicano), margen electoral, proporción de
terceras fuerzas y crecimiento del total de votos.

## Controles

- 12 elecciones, una cada cuatro años, desde 1976 hasta 2020.
- Los componentes del voto popular y electoral deben sumar sus totales.
- Desde 1976 existen 538 votos electorales por elección.
- No se imputan datos faltantes ni se redondean conteos originales.

## Licencia y actualización

Los datos son publicaciones del Gobierno de Estados Unidos. La documentación y
el código de este repositorio pueden reutilizarse con atribución. Si se reemplaza
la tabla, conservar este diccionario, añadir la URL exacta del informe y no
sobrescribir silenciosamente la versión anterior.
