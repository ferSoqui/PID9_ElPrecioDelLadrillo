# Fuentes de los conjuntos de datos

## 1. Inventario de vivienda 2025 (`inventario_vivienda_2025_v2.csv`)

- **Fuente:** Sistema Nacional de Información e Indicadores de Vivienda (SNIIV), CONAVI.
- **Contenido:** registros mensuales de vivienda en inventario por entidad,
  municipio, avance de obra, segmento de valor (categórico), rango de UMA y
  tipo (horizontal/vertical). 226,891 filas, año 2025.
- **Importante:** la columna `vivienda_valor` es **categórica** (Económica …
  Residencial plus); el archivo **no contiene precios en pesos**. Para
  análisis de precios se cruza con el índice SHF (abajo).
- Versión limpia: `inventario_vivienda_2025_limpio.parquet` (y `.csv.zip`),
  generada con `Proyecto/Herramientas/limpiar_inventario.py`.

## 2. Índice SHF de Precios de la Vivienda (`indice_shf_precios_vivienda_datos_abiertos.xlsx`)

- **Fuente:** Sociedad Hipotecaria Federal (SHF), "Índice SHF datos abiertos,
  2.º trimestre de 2026".
- **Página del documento:**
  https://www.gob.mx/shf/documentos/indice-shf-de-precios-de-la-vivienda-en-mexico-2025-a-2026
- **URL directa del archivo descargado (2026-08-31):**
  https://www.gob.mx/cms/uploads/attachment/file/1097035/Indice_SHF_datos_abiertos_2_trim_2026.xlsx
- **Página general del índice (nota metodológica y trimestres anteriores):**
  https://www.gob.mx/shf/articulos/indice-de-precios-de-la-vivienda-shf
- **Contenido:** índice trimestral de precios de la vivienda (base 2017=100)
  desde 1T-2005 hasta 2T-2026. Una sola hoja con tres niveles mezclados en
  filas: series globales/nacionales (columna `Global`), 32 entidades
  federativas (columna `Estado`) y 72 municipios/alcaldías seleccionados
  (columna `Municipio`).
- Tabla entidad×trimestre lista para análisis:
  `indice_shf_entidad_trimestre.parquet` (y `.csv`), generada con
  `Proyecto/Herramientas/cruzar_shf.py`.
- **Actualización:** la SHF publica el índice cada trimestre; para
  actualizarlo, buscar el nuevo "Índice SHF datos abiertos" en la página del
  documento indicada arriba y volver a correr `cruzar_shf.py`.
