# Fuente del conjunto de datos

**El Precio del Ladrillo**

---

## En resumen

- **Archivo:** `dataset_final.csv`
- **Qué contiene:** datos públicos de vivienda, crédito, inflación, tasas de interés y población de México, reunidos en una sola tabla.
- **Cada fila es:** un estado en un trimestre.
- **Cobertura:** los 32 estados, del primer trimestre de 2017 al cuarto trimestre de 2025.
- **Tamaño:** 1,152 filas y 33 columnas, sin valores vacíos y sin filas duplicadas.
- **Cómo se genera:** con el script `limpieza.py`, que lee los archivos originales de esta misma carpeta tal como se subieron (en `.csv` o comprimidos en `.zip`).

Para volver a generarlo, desde la raíz del repo:

```
python Proyecto/Conjunto_de_Datos/limpieza.py
```

Cualquiera puede correrlo y obtener el mismo resultado.

### Cambio de alcance

El conjunto anterior del equipo usaba solo el inventario de vivienda de 2025. Ahora el proyecto busca predecir la variación del precio de la vivienda, y con un solo año no hay suficiente historia para entrenar un modelo. Por eso se cambió a un periodo de nueve años, de 2017 a 2025, y se agregaron más fuentes.

---

## De dónde salió cada parte

### 1. Precio de la vivienda: Sociedad Hipotecaria Federal (SHF)

- **Archivo:** `indice_shf_precios_vivienda_datos_abiertos.xlsx`
- **Qué trae:** el Índice SHF de Precios de la Vivienda, trimestral, de 2005 a 2026, a nivel nacional, estatal y municipal.
- **Base:** 2017 = 100.
- **Verificación:** el promedio nacional de 2017 da exactamente 100, y los valores coinciden con el reporte oficial de SHF 2015 a 2019.

### 2. Créditos para vivienda: SEDATU (SNIIV)

Sistema Nacional de Información e Indicadores de Vivienda.

- **Archivos:**
  - `financiamientos_2016 (1).csv` y `financiamientos_2019.csv`, sin comprimir.
  - 2017, 2018 y de 2020 a 2025, comprimidos en `.csv.zip` por su tamaño, sin modificar su contenido.
  - `Financiamientos_2026.csv.zip` (enero a agosto de 2026). Todavía no se usa, porque el conjunto llega a 2025.
- **Qué trae:** créditos y subsidios otorgados por mes, estado, municipio y organismo (INFONAVIT, FOVISSSTE, bancos, entre otros), con número de acciones y monto en pesos.
- **Registros:** 3,533,477 de 2016 a 2025.
- **Consulta:** sniiv.sedatu.gob.mx/Reporte/Datos_abiertos

### 3. Oferta de vivienda: SEDATU (SNIIV), con datos del Registro Único de Vivienda (RUV)

- **Archivos:**
  - De `oferta_viv_2016.csv.zip` a `oferta_viv_2025.csv.zip`.
  - El de 2025 viene en un formato distinto (usa comillas simples) y el script lo detecta solo.
  - `Oferta_viv_2026.csv.zip`, que solo trae julio de 2026 y todavía no se usa.
- **Qué trae:** inventario mensual de viviendas en oferta por estado, municipio, nivel de valor, avance de obra y tipo de vivienda.
- **Consulta:** sniiv.sedatu.gob.mx/Reporte/Datos_abiertos

### 4. Inflación: INEGI, Índice Nacional de Precios al Consumidor (INPC)

- **Archivos:**
  - `inpc_nacional.csv.zip`, de enero 2016 a julio 2026.
  - `inpc_2015_dof.csv`, con los 12 meses de 2015.
- **Qué trae:** el INPC mensual nacional.
- **Base:** segunda quincena de julio de 2018 = 100.
- **Origen de los valores:**
  - Los de 2016 en adelante se tomaron de El Contribuyente, que republica las cifras oficiales del INEGI.
  - Los de 2015 se tomaron de la serie histórica publicada en el Diario Oficial de la Federación (DOF), y coinciden con el primer archivo en enero y diciembre de 2016.
- **Verificación:** los 12 meses de 2015 se compararon con una descarga directa de INEGI hecha el 4 de noviembre de 2026 (archivo `inpc_2015_inegi_consulta.csv`), y coinciden.

### 5. Tasas de interés: Banco de México (Sistema de Información Económica)

- **Archivos:** `banxico_SF60634_tasa_cetes91d.csv` y `banxico_SF43773_tasa_fondeo_bancario.csv`
- **Qué trae:**
  - Tasa de CETES a 91 días (serie SF60634, semanal).
  - Tasa de fondeo bancario (serie SF43773, diaria).
  - Ambas de 2016 a 2025, en porcentaje anual.
- **Consulta:** banxico.org.mx, en el Sistema de Información Económica, buscando la clave de cada serie.

### 6. Población: Consejo Nacional de Población (CONAPO)

- **Archivo:** `00_Pob_Mitad_1950_2070.csv`, comprimido como `00_Pob_Mitad_1950_2070.zip`.
- **Qué trae:** población a mitad de año por estado, edad y sexo, de 1970 a 2070. Hasta 2019 son datos conciliados y de 2020 en adelante son proyecciones.
- **Consulta:** gob.mx/conapo, en *Bases de datos de la Conciliación Demográfica 1950 a 2019 y Proyecciones de la población de México 2020 a 2070*.

### Diccionarios de datos

Cada fuente tiene su diccionario. Los de financiamientos e inventario son los oficiales de SEDATU. Los de SHF, INPC, Banxico y CONAPO los elaboró el equipo, porque esas instituciones no publican uno en ese formato.

---

## Tipos de dato de cada columna

- **Texto:** `estado` y `periodo`.
- **Entero:** `cve_ent`, `anio`, `trimestre`, `creditos`, `creditos_ind_vivienda`, `oferta_viviendas` y `poblacion`.
- **Indicador de 0 o 1:** `oferta_imputada` y `oferta_metodologia_2019`.
- **Decimal:** todas las demás.

---

## Decisiones de limpieza

### 1. Nivel de valor de la vivienda (`vivienda_valor`)

**El problema:** esta columna no es un precio en pesos. Es una categoría con orden, de menor a mayor valor. Según el diccionario de SEDATU, cada nivel corresponde a un costo promedio de la vivienda medido en UMA (Unidad de Medida y Actualización):

1. **Económica:** alrededor de 118 UMA
2. **Popular:** de 118.1 a 200 UMA
3. **Tradicional:** de 200.1 a 350 UMA
4. **Media:** de 350.1 a 750 UMA
5. **Residencial:** de 750.1 a 1,500 UMA
6. **Residencial plus:** más de 1,500 UMA

Si se usara como número, el modelo entendería, por ejemplo, que una vivienda Residencial (5) vale cinco veces una Económica (1), y eso no es correcto. Por eso, si se usa, debe tratarse como variable categórica ordenada.

**Lo que hicimos:** no se incluyó como columna. Entre 2016 y 2018 los archivos de SEDATU usan los códigos 7, 8 y 9, que no aparecen en el diccionario. Por eso no se puede comparar el nivel de valor antes y después de 2019, y completarlo implicaría inventar datos. El precio de la vivienda se mide con el índice SHF, y en el análisis exploratorio el nivel de valor se revisa por separado, solo de 2019 a 2024.

### 2. Clave y nombre del estado (`cve_ent` y `estado`)

**El problema:** las dos columnas dicen lo mismo.

**Lo que hicimos:**
- `cve_ent`, la clave INEGI del 1 al 32, es la única llave para unir las fuentes y la que debe usar el modelo.
- `estado` se conserva solo para que la tabla se pueda leer.
- Todos los nombres siguen el catálogo de CONAPO.
- Al archivo del SHF, que solo traía el nombre, se le quitaron los espacios sobrantes y se le asignó su clave.

### 3. Datos mensuales contra índice trimestral

**El problema:** los créditos, la oferta, el INPC y las tasas son mensuales, semanales o diarios, pero el índice SHF es trimestral. Si se unieran los datos mensuales con el índice, los tres meses de un trimestre repetirían el mismo valor del índice, y el modelo trataría como tres casos distintos lo que en realidad es un solo dato.

**Lo que hicimos:** todo se llevó a nivel trimestral antes de unirlo, así cada fila tiene su propio valor del índice:
- **Créditos:** se suman los meses del trimestre.
- **Oferta:** como es un inventario, se toma el último mes del trimestre en lugar de sumar.
- **INPC y tasas:** se promedian los meses o días del trimestre.
- **Población:** es anual, así que se usa el mismo valor en los cuatro trimestres del año.

### 4. Pesos constantes

Los montos de crédito se convirtieron a **pesos de 2024** con el INPC de cada mes, para quitar el efecto de la inflación y poder comparar entre años. El índice SHF no se ajustó, porque ya mide el precio de una vivienda de calidad constante.

### 5. Registros excluidos

De los créditos se quitaron **463 registros sin clave de estado** y **12 con monto negativo**.

### 6. Cambio de medición en la oferta (2019)

En febrero de 2019 el total nacional de viviendas en oferta baja de 560,245 a 311,343 de un mes a otro, lo que indica un cambio en la forma de contar de SEDATU. La columna `oferta_metodologia_2019` marca este cambio para que el modelo lo tome en cuenta.

### 7. Valores vacíos

- **Oferta del primer al tercer trimestre de 2024:** SEDATU solo publicó diciembre de 2024. Para cada estado se estimó en línea recta entre el cuarto trimestre de 2023 y el cuarto trimestre de 2024, y esas filas se marcan con `oferta_imputada = 1`.
- **Oferta del cuarto trimestre de 2023:** se usó noviembre, porque no hay diciembre.
- **Inflación anual de 2016:** se completó con el INPC de 2015 del DOF, verificado con INEGI.
- **Año 2016:** se usa solo para calcular los valores de periodos anteriores que necesita 2017. Por eso el conjunto empieza en 2017.

### 8. Datos raros en la oferta de 2025

- **Noviembre es una copia exacta de septiembre** en el archivo de SEDATU. No afecta al conjunto, porque de cada trimestre se toma el último mes: septiembre para el tercer trimestre y diciembre para el cuarto.
- **En diciembre la oferta sube 28% de un mes a otro** a nivel nacional, de 209,053 a 268,527 viviendas. El aumento se concentra en vivienda Popular de algunos estados, como Chiapas, Tabasco y Tamaulipas. No se pudo confirmar si es un cambio real o un error de la fuente, así que se dejó como viene.

---

## Variables del conjunto final

### Identificación

- cve_ent: clave del estado según INEGI, del 1 al 32. Es la llave.
- estado: nombre del estado, solo como etiqueta.
- anio: año.
- trimestre: trimestre del año, del 1 al 4.
- periodo: etiqueta del periodo, por ejemplo 2024T4.

### Precio de la vivienda

- indice_shf: Índice SHF de Precios de la Vivienda, base 2017 = 100.
- var_anual_shf_pct: variación porcentual del índice contra el mismo trimestre del año anterior.

### Crédito

- creditos: número de créditos y subsidios otorgados en el trimestre.
- monto_real_mdp: monto total otorgado, en millones de pesos de 2024.
- creditos_ind_vivienda: créditos individuales para comprar vivienda nueva o usada.
- credito_promedio_real: monto promedio de esos créditos individuales, en pesos de 2024.
- creditos_por_mil: créditos por cada mil habitantes.

### Oferta

- oferta_viviendas: viviendas en oferta al cierre del trimestre.
- oferta_por_mil: viviendas en oferta por cada mil habitantes.
- oferta_imputada: 1 si la oferta se estimó, 0 si es dato real.
- oferta_metodologia_2019: 1 a partir de 2019, 0 antes.

### Población, inflación y tasas

- poblacion: población a mitad de año del estado.
- inpc: INPC promedio del trimestre.
- inflacion_anual_pct: variación porcentual anual del INPC.
- tasa_cetes91: tasa de CETES a 91 días, promedio del trimestre, en porcentaje anual.
- tasa_fondeo: tasa de fondeo bancario, promedio del trimestre, en porcentaje anual.

### Valores de periodos anteriores

- Las columnas que terminan en `_lag1` tienen el valor de la variable **un trimestre antes**.
- Las que terminan en `_lag4` tienen el valor de **cuatro trimestres antes**, es decir, del mismo trimestre del año anterior.
- Se calcularon para `indice_shf`, `creditos_por_mil`, `credito_promedio_real`, `oferta_por_mil`, `tasa_fondeo` e `inflacion_anual_pct`.

Estas columnas permiten predecir sin hacer trampa, porque solo usan información que ya se conocía en ese momento.
