# Bitácora 02. Limpieza del inventario: de v0 a v1

La versión v1 del inventario la produce
`Proyecto/Herramientas/limpiar_inventario.py` a partir del CSV crudo (v0). No
basta con correr el script: cada quien debe entender qué hace y poder defender
cada decisión ante el resto del equipo o en la revisión del proyecto. Este
documento explica cada cambio con los números que lo respaldan.

## 1. Codificación dañada

El CSV crudo es UTF-8 con BOM (una marca invisible al inicio del archivo) y
además trae mojibake: texto que en algún momento se decodificó como Latin-1 y
se volvió a guardar. El caso concreto es la categoría "Económica", que en v0
aparece como "EconÃ³mica" en 2,418 filas; el resto de las columnas de texto no
está afectado, pero el script revisa todas por si acaso.

Qué se hizo: leer con `encoding="utf-8-sig"` para descartar el BOM, y reparar
cada cadena dañada reencodificándola a Latin-1 y decodificándola como UTF-8.
Una cadena sana no sobrevive esa doble conversión, así que se queda tal cual;
solo cambian las que estaban rotas.

Por qué no se corrigió a mano en Excel: no sería reproducible (nadie podría
verificar qué se cambió), y abrir y guardar el CSV con Excel es justo el tipo
de operación que introdujo el daño y que además borra los ceros a la izquierda
de las claves. El crudo se queda intacto como evidencia.

## 2. Claves geográficas leídas como texto

Las columnas `cve_ent` (entidad, "01" a "32") y `cve_mun` (municipio, "001" en
adelante) son claves del INEGI y llevan ceros a la izquierda. Si se deja que
pandas infiera el tipo, las lee como enteros: "01" se convierte en 1, y a
partir de ahí cualquier cruce con otra fuente que sí tenga "01" como texto
falla en silencio, que es la peor forma de fallar. Por eso la lectura fuerza
`dtype=str` en esas columnas y aplica `zfill` (2 dígitos para entidad, 3 para
municipio) como red de seguridad.

Esta es la razón principal de que el formato de trabajo sea Parquet: conserva
los tipos. Quien use el CSV de respaldo tiene que volver a declarar
`dtype={"cve_ent": str, "cve_mun": str}` cada vez que lo lea.

## 3. Categorías ordenadas

`vivienda_valor` es una escala, no una lista de etiquetas sueltas:

Económica < Popular < Tradicional < Media < Residencial < Residencial plus

Si se deja como texto, cualquier ordenamiento o gráfica usa el orden
alfabético (Económica, Media, Popular, Residencial...), que desordena la
escala y produce lecturas equivocadas sin que nada truene. Se convirtió en
categórica ordenada de pandas, igual que `vivienda_uma` (rangos de UMA) y
`avance_obra` (etapas de la obra), que también tienen orden natural. Las
columnas `tipo` y `entidad` quedaron categóricas sin orden, porque no lo
tienen.

Un detalle del script que conviene imitar: antes de asignar el orden verifica
que no haya categorías fuera de la lista prevista, y truena con un mensaje
claro si aparece una. Es preferible que un script falle a que invente.

## 4. Columna añadida: cve_ent_mun

Se agregó `cve_ent_mun`, la concatenación de entidad y municipio en 5 dígitos
(por ejemplo "01001"). Es la clave municipal estándar del INEGI y evita el
error clásico de cruzar solo por `cve_mun`, que se repite entre entidades (hay
un municipio "001" en cada estado). Con ella el inventario tiene 445 claves
municipales distintas. Es la única columna nueva: v0 tiene 12 columnas y v1
tiene 13.

## 5. Tipos numéricos y de fecha

`fecha` pasó a datetime (son fechas de fin de mes), `vivienda` a entero
(`errors="raise"`: si alguna celda no fuera un número el script truena en
lugar de dejar un hueco), y `anio` y `mes` a enteros chicos. Nada de esto
cambia valores; solo deja los tipos correctos para agrupar y graficar.

## 6. Verificación: nada se perdió

- Filas en v0: 226,891 (sin contar el encabezado). Filas en v1: 226,891. El
  script tiene un `assert` que truena si la limpieza pierde una sola fila.
- Valores nulos: 0 antes y 0 después.
- Total de viviendas registradas en v1: 2,585,013 (suma de la columna
  `vivienda` sobre todos los registros mensuales).
- Las seis categorías de `vivienda_valor` se leen correctamente en v1; las
  2,418 filas de "EconÃ³mica" quedaron como "Económica" y los conteos por
  categoría cuadran con el crudo.

La limpieza solo corrigió representación (codificación, tipos, orden) y agregó
una columna derivada; no filtró, no imputó y no modificó ningún valor
observado. Esa frase deben poder decirla, y sostenerla, en la presentación.

## Lo que sigue y les toca a ustedes

1. Revisen `avance_obra`: trae categorías como "Sin reporte", "Sin HBT",
   "HBT - 5m" y "HBT + 5m". Antes de usar esa columna averigüen en la
   documentación del SNIIV qué significan y decidan si entran en su análisis.
2. Decidan la unidad de análisis. El archivo tiene un renglón por combinación
   de mes, municipio, avance, segmento, UMA y tipo; casi cualquier pregunta
   requerirá agregarlo, y esa agregación es una decisión que deben justificar.
3. Si transforman los datos otra vez (filtrar 2025 incompleto, agregar por
   trimestre, unir con el índice SHF), eso es una v2: script propio en
   `Proyecto/Herramientas/` y bitácora numerada en esta carpeta, con el mismo
   formato de este documento: qué cambió, por qué, y con qué números se
   verificó que no se rompió nada.
