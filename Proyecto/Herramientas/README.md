# Herramientas del proyecto

Material de apoyo del curso para preparar los datos del proyecto de precios
de vivienda. Requisitos: `pandas`, `pyarrow`, `openpyxl`
(`python3 -m pip install --user pandas pyarrow openpyxl`).

## Flujo

```
inventario_vivienda_2025_v2.csv  (crudo, SNIIV/CONAVI)
        │  1) python3 Proyecto/Herramientas/limpiar_inventario.py
        ▼
inventario_vivienda_2025_limpio.parquet  (+ .csv.zip)
        │
        │   indice_shf_precios_vivienda_datos_abiertos.xlsx  (SHF)
        │  2) python3 Proyecto/Herramientas/cruzar_shf.py
        ▼
indice_shf_entidad_trimestre.parquet  (+ .csv)   ← tabla entidad×trimestre
```

Ambos scripts se corren desde cualquier directorio; las rutas se resuelven
solas. Los archivos viven en `Proyecto/Conjunto_de_Datos/` (fuentes y URLs
en su `FUENTE.md`).

## Advertencias al trabajar con estos datos

1. **Claves geográficas como TEXTO.** `cve_ent` ("01"–"32") y `cve_mun`
   ("001"…) llevan ceros a la izquierda. Si se leen como número, "01" se
   vuelve 1 y los cruces con INEGI/SHF fallan. Al leer cualquier CSV del
   proyecto: `pd.read_csv(..., dtype={"cve_ent": str, "cve_mun": str})`.
   El Parquet ya conserva los tipos; por eso es el formato preferido.
2. **Codificación.** El CSV crudo es UTF-8 con BOM y trae mojibake
   ("EconÃ³mica"). Leerlo con `encoding="utf-8-sig"` y usar siempre la
   versión limpia; no volver a abrir/guardar el crudo con Excel.
3. **El inventario NO trae precios.** `vivienda_valor` es una escala
   categórica ordenada (Económica < Popular < Tradicional < Media <
   Residencial < Residencial plus). Para precios se usa el índice SHF
   (base 2017=100), que tampoco está en pesos: mide evolución relativa.
4. **Frecuencias distintas.** El inventario es mensual y el índice SHF
   trimestral. El cruce se hace por entidad y trimestre
   (`trimestre = (mes-1)//3 + 1`); `cruzar_shf.py` imprime un ejemplo.
5. **`cve_ent_mun`** (5 dígitos, ej. "01001") es la clave municipal
   compuesta estándar del INEGI, añadida en la limpieza para cruces
   municipales. Ojo: el índice SHF por municipio solo cubre 72 municipios
   seleccionados; el cruce recomendado es a nivel entidad.
