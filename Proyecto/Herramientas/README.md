# Herramientas del proyecto

Material de apoyo del curso para preparar los datos del proyecto de precios de
vivienda. Requisitos: `pandas`, `pyarrow`, `openpyxl` y, para las figuras,
`matplotlib` (`python3 -m pip install --user pandas pyarrow openpyxl
matplotlib`).

## Flujo

1. `python3 Proyecto/Herramientas/limpiar_inventario.py` lee el CSV crudo
   `inventario_vivienda_2025_v2.csv` (SNIIV, CONAVI) y escribe la versión
   limpia `inventario_vivienda_2025_limpio.parquet` (más un respaldo
   `.csv.zip`).
2. `python3 Proyecto/Herramientas/cruzar_shf.py` lee el archivo de la SHF
   `indice_shf_precios_vivienda_datos_abiertos.xlsx` y escribe la tabla de
   entidad por trimestre `indice_shf_entidad_trimestre.parquet` (más un
   `.csv`), e imprime un cruce de prueba con el inventario limpio.
3. `python3 Proyecto/Herramientas/eda_inicial.py` genera las figuras de la
   exploración inicial en `Proyecto/Documentacion/figuras/`; los comentarios
   de cada figura están en `Proyecto/Documentacion/03_eda_inicial.md`.

Los tres scripts se corren desde cualquier directorio; las rutas se resuelven
solas. Los archivos de datos viven en `Proyecto/Conjunto_de_Datos/` (fuentes y
URLs en su `FUENTE.md`), y la bitácora de qué se hizo con ellos y por qué está
en `Proyecto/Documentacion/`.

## Advertencias al trabajar con estos datos

1. Claves geográficas como texto. `cve_ent` ("01" a "32") y `cve_mun` ("001"
   en adelante) llevan ceros a la izquierda. Si se leen como número, "01" se
   vuelve 1 y los cruces con INEGI o SHF fallan. Al leer cualquier CSV del
   proyecto: `pd.read_csv(..., dtype={"cve_ent": str, "cve_mun": str})`. El
   Parquet ya conserva los tipos; por eso es el formato preferido.
2. Codificación. El CSV crudo es UTF-8 con BOM y trae mojibake ("EconÃ³mica").
   Hay que leerlo con `encoding="utf-8-sig"` y usar siempre la versión limpia;
   no vuelvan a abrir y guardar el crudo con Excel.
3. El inventario no trae precios. `vivienda_valor` es una escala categórica
   ordenada (Económica < Popular < Tradicional < Media < Residencial <
   Residencial plus). Para precios se usa el índice SHF (base 2017=100), que
   tampoco está en pesos: mide evolución relativa.
4. Frecuencias distintas. El inventario es mensual y el índice SHF trimestral.
   El cruce se hace por entidad y trimestre (`trimestre = (mes-1)//3 + 1`);
   `cruzar_shf.py` imprime un ejemplo.
5. `cve_ent_mun` (5 dígitos, por ejemplo "01001") es la clave municipal
   compuesta estándar del INEGI, añadida en la limpieza para cruces
   municipales. Ojo: el índice SHF por municipio solo cubre 72 municipios
   seleccionados; el cruce recomendado es a nivel entidad.
