# Bitácora 01. Origen de los datos

Esta carpeta es la bitácora del conjunto de datos del proyecto. La idea es
simple: cada archivo de datos que usen debe poder rastrearse hasta su origen, y
cada versión nueva debe explicar qué le hicieron a la anterior y por qué. Si en
la revisión final alguien les pregunta "¿de dónde salió este número?", la
respuesta tiene que estar aquí, no en la memoria de quien corrió el script.

## Fuente 1: inventario de vivienda 2025 (SNIIV, CONAVI)

Es el archivo que el equipo ya tenía: `inventario_vivienda_2025_v2.csv`,
descargado del Sistema Nacional de Información e Indicadores de Vivienda
(SNIIV) de la CONAVI. Contiene 226,891 registros mensuales de vivienda en
inventario durante 2025 (enero a diciembre), desglosados por entidad,
municipio, avance de obra, segmento de valor, rango de UMA y tipo de vivienda
(horizontal o vertical). Cubre las 32 entidades y 445 municipios.

Un punto que condiciona todo el proyecto: este archivo no trae precios en
pesos. La columna `vivienda_valor` es una escala categórica (de Económica a
Residencial plus). Quien quiera hablar de precios necesita la segunda fuente.

## Fuente 2: índice SHF de precios de la vivienda

Para tener una variable de precio se descargó el índice SHF de precios de la
vivienda, que publica la Sociedad Hipotecaria Federal cada trimestre. Se usó el
archivo de datos abiertos correspondiente al segundo trimestre de 2026.

- Página del documento:
  https://www.gob.mx/shf/documentos/indice-shf-de-precios-de-la-vivienda-en-mexico-2025-a-2026
- URL directa del archivo descargado:
  https://www.gob.mx/cms/uploads/attachment/file/1097035/Indice_SHF_datos_abiertos_2_trim_2026.xlsx
- Fecha de descarga: 31 de agosto de 2026.
- Página general del índice, con la nota metodológica:
  https://www.gob.mx/shf/articulos/indice-de-precios-de-la-vivienda-shf

El archivo (`indice_shf_precios_vivienda_datos_abiertos.xlsx`) trae el índice
trimestral con base 2017 = 100, desde el primer trimestre de 2005 hasta el
segundo de 2026, en una sola hoja que mezcla tres niveles: series nacionales,
las 32 entidades y 72 municipios seleccionados. El índice no está en pesos:
mide la evolución relativa del precio de la vivienda con crédito hipotecario.
Tengan presente esa limitación cuando redacten conclusiones.

## Cadena de versiones

Regla de trabajo: los archivos crudos no se tocan nunca. Toda versión nueva
sale de un script que cualquiera del equipo puede volver a correr, y queda
anotada en esta bitácora.

Inventario SNIIV:

- v0: `inventario_vivienda_2025_v2.csv`. El crudo, tal como llegó al equipo.
  Tiene problemas conocidos de codificación y de tipos que se detallan en la
  bitácora 02. No se edita ni se vuelve a guardar desde Excel.
- v1: `inventario_vivienda_2025_limpio.parquet` (y respaldo
  `inventario_vivienda_2025_limpio.csv.zip`). Generada por
  `Proyecto/Herramientas/limpiar_inventario.py` a partir de v0. Es la versión
  con la que se trabaja. Qué cambió y por qué: bitácora 02.

Índice SHF:

- Original: `indice_shf_precios_vivienda_datos_abiertos.xlsx`, tal como se
  descargó. No se edita.
- Derivada: `indice_shf_entidad_trimestre.parquet` (y `.csv`), la tabla larga
  de entidad por trimestre que genera `Proyecto/Herramientas/cruzar_shf.py`.
  Incluye la clave INEGI de entidad para poder cruzarla con el inventario.

Los detalles de URLs y actualización trimestral están también en
`Proyecto/Conjunto_de_Datos/FUENTE.md`, que es el archivo que pide el curso.

## Lo que sigue y les toca a ustedes

1. Definir la pregunta de investigación con el precio como variable central.
   El inventario solo da cantidades y categorías; el precio vive en el índice
   SHF. La pregunta tiene que ser contestable con estas dos piezas o justificar
   qué otra fuente haría falta.
2. La matriz de revisión de literatura no existe todavía. Va en
   `Articulos/Revision/` y es la fase actual del curso; los PDF que ya juntaron
   en `Articulos/Revision/Fuentes/` son la materia prima.
3. Si consiguen una versión más reciente de cualquiera de las dos fuentes,
   guarden el archivo nuevo sin sobrescribir el anterior, vuelvan a correr los
   scripts y agreguen aquí la entrada correspondiente.

Cada paso nuevo que den con los datos se documenta en esta carpeta con el
mismo formato: un archivo numerado que diga de qué versión partió, qué cambió,
con qué números lo verificaron y qué decisión del equipo lo motivó.
