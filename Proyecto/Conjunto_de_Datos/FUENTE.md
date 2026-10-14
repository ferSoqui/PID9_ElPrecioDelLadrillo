FUENTE DEL CONJUNTO DE DATOS
El Precio del Ladrillo


QUÉ ES ESTE CONJUNTO DE DATOS

El archivo dataset_final.csv reúne en una sola tabla datos públicos de vivienda, crédito, inflación, tasas de interés y población de México.

Cada fila es un estado en un trimestre. Abarca los 32 estados, del primer trimestre de 2017 al cuarto trimestre de 2024. En total son 1,024 filas y 33 columnas, sin valores vacíos y sin filas duplicadas.

Lo genera el script limpieza.py a partir de los archivos originales de la carpeta datos_crudos. Cualquiera puede volver a correrlo y obtener el mismo resultado.

Cambio de alcance: el conjunto anterior del equipo usaba solo el inventario de vivienda de 2025. Ahora el proyecto busca predecir la variación del precio de la vivienda, y con un solo año no hay suficiente historia para entrenar un modelo. Por eso se cambió a un periodo de ocho años y se agregaron más fuentes.


DE DÓNDE SALIÓ CADA PARTE

1. Precio de la vivienda: Sociedad Hipotecaria Federal (SHF)

Archivo: indice_shf_precios_vivienda_datos_abiertos.xlsx

Contenido: Índice SHF de Precios de la Vivienda, trimestral, de 2005 a 2026, a nivel nacional, estatal y municipal. Su base es 2017 igual a 100. Se verificó que el promedio nacional de 2017 da exactamente 100 y que los valores coinciden con el reporte oficial de SHF 2015 a 2019.

2. Créditos para vivienda: SEDATU, Sistema Nacional de Información e Indicadores de Vivienda (SNIIV)

Archivos: financiamientos_2016.csv y de financiamientos_2017.csv a financiamientos_2024.csv. Por su tamaño se suben comprimidos en formato .csv.gz, sin modificar su contenido.

Contenido: créditos y subsidios otorgados por mes, estado, municipio y organismo (INFONAVIT, FOVISSSTE, bancos, entre otros), con número de acciones y monto en pesos. Son 3,207,828 registros.

Consulta: sniiv.sedatu.gob.mx/Reporte/Datos_abiertos

3. Oferta de vivienda: SEDATU, SNIIV, con datos del Registro Único de Vivienda (RUV)

Archivos: de oferta_viv_2016.csv a oferta_viv_2024.csv

Contenido: inventario mensual de viviendas en oferta por estado, municipio, nivel de valor, avance de obra y tipo de vivienda.

Consulta: sniiv.sedatu.gob.mx/Reporte/Datos_abiertos

4. Inflación: INEGI, Índice Nacional de Precios al Consumidor (INPC)

Archivos: inpc_nacional.csv, de enero 2016 a julio 2026, e inpc_2015_dof.csv, con los 12 meses de 2015.

Contenido: INPC mensual nacional con base en la segunda quincena de julio de 2018 igual a 100. Los valores de 2016 en adelante se tomaron de El Contribuyente, que republica las cifras oficiales del INEGI. Los de 2015 se tomaron de la serie histórica publicada en el Diario Oficial de la Federación, y coinciden con el primer archivo en enero y diciembre de 2016.

5. Tasas de interés: Banco de México, Sistema de Información Económica (SIE)

Archivos: banxico_SF60634_tasa_cetes91d.csv y banxico_SF43773_tasa_fondeo_bancario.csv

Contenido: tasa de CETES a 91 días (serie SF60634, semanal) y tasa de fondeo bancario (serie SF43773, diaria), de 2016 a 2025, en porcentaje anual.

Consulta: banxico.org.mx, en el Sistema de Información Económica, buscando la clave de cada serie.

Se descargó también la inflación no subyacente (serie SP74665), pero no se usa porque mide casi lo mismo que el INPC.

6. Población: Consejo Nacional de Población (CONAPO)

Archivo: 00_Pob_Mitad_1950_2070.csv, comprimido como .csv.gz

Contenido: población a mitad de año por estado, edad y sexo, de 1970 a 2070. Hasta 2019 son datos conciliados y de 2020 en adelante son proyecciones.

Consulta: gob.mx/conapo, en Bases de datos de la Conciliación Demográfica 1950 a 2019 y Proyecciones de la población de México 2020 a 2070.

Cada fuente tiene su diccionario de datos. Los de financiamientos e inventario son los oficiales de SEDATU. Los de SHF, INPC, Banxico y CONAPO los elaboró el equipo, porque esas instituciones no publican uno en ese formato.


TIPOS DE DATO DE CADA COLUMNA

Texto: estado y periodo.

Entero: cve_ent, anio, trimestre, creditos, creditos_ind_vivienda, oferta_viviendas y poblacion.

Indicador de 0 o 1: oferta_imputada y oferta_metodologia_2019.

Decimal: todas las demás columnas.


DECISIONES DE LIMPIEZA

1. Nivel de valor de la vivienda (vivienda_valor)

Esta columna no es un precio en pesos. Es una categoría con orden, que va de menor a mayor valor. Según el diccionario de SEDATU, cada nivel corresponde a un costo promedio de la vivienda medido en UMA (Unidad de Medida y Actualización):

1 Económica, alrededor de 118 UMA

2 Popular, de 118.1 a 200 UMA

3 Tradicional, de 200.1 a 350 UMA

4 Media, de 350.1 a 750 UMA

5 Residencial, de 750.1 a 1,500 UMA

6 Residencial plus, más de 1,500 UMA

Si se usara como número, el modelo entendería por ejemplo que una vivienda Residencial vale cinco veces una Económica, y eso no es correcto. Por eso, si se usa, debe tratarse como variable categórica ordenada.

En este conjunto de datos no se incluyó como columna. Entre 2016 y 2018 los archivos de SEDATU usan códigos 7, 8 y 9, que no aparecen en el diccionario. Por eso no se puede comparar el nivel de valor antes y después de 2019, y completarlo implicaría inventar datos. El precio de la vivienda se mide con el índice SHF, y para el análisis exploratorio el nivel de valor se revisa por separado, solo de 2019 a 2024.

2. Clave y nombre del estado (cve_ent y estado)

Las dos columnas dicen lo mismo. Se decidió que cve_ent, la clave INEGI del 1 al 32, es la única llave para unir las fuentes y la que debe usar el modelo. La columna estado se conserva solo para que la tabla se pueda leer. Todos los nombres siguen el catálogo de CONAPO. Al archivo del SHF, que solo traía el nombre, se le quitaron los espacios sobrantes y se le asignó su clave.

3. Datos mensuales contra índice trimestral

Los créditos, la oferta, el INPC y las tasas son mensuales, semanales o diarios, pero el índice SHF es trimestral. Si se unieran los datos mensuales con el índice, los tres meses de un trimestre repetirían el mismo valor del índice, y el modelo trataría como tres casos distintos lo que en realidad es un solo dato.

Para evitarlo, todo se llevó a nivel trimestral antes de unirlo. Así cada fila tiene su propio valor del índice, sin repeticiones:

Créditos: se suman los meses del trimestre.

Oferta: como es un inventario, se toma el último mes del trimestre en lugar de sumar.

INPC y tasas: se promedian los meses o días del trimestre.

Población: es anual, así que se usa el mismo valor en los cuatro trimestres del año.

4. Pesos constantes

Los montos de crédito se convirtieron a pesos de 2024 con el INPC de cada mes, para quitar el efecto de la inflación y poder comparar entre años. El índice SHF no se ajustó, porque ya mide el precio de una vivienda de calidad constante.

5. Registros excluidos

De los créditos se quitaron 452 registros sin clave de estado y 12 con monto negativo.

6. Cambio de medición en la oferta

En febrero de 2019 el total nacional de viviendas en oferta baja de 560,245 a 311,343 de un mes a otro, lo que indica un cambio en la forma de contar de SEDATU. La columna oferta_metodologia_2019 marca este cambio para que el modelo lo tome en cuenta.

7. Valores vacíos

Oferta del primer al tercer trimestre de 2024: SEDATU solo publicó diciembre de 2024. Para cada estado se estimó en línea recta entre el cuarto trimestre de 2023 y el cuarto trimestre de 2024, y esas filas se marcan con oferta_imputada igual a 1.

Oferta del cuarto trimestre de 2023: se usó noviembre, porque no hay diciembre.

Inflación anual de 2016: se completó con el INPC de 2015 del Diario Oficial de la Federación.

Año 2016: se usa solo para calcular los valores de periodos anteriores que necesita 2017, por eso el conjunto empieza en 2017.


VARIABLES DEL CONJUNTO FINAL

Identificación

cve_ent: clave del estado según INEGI, del 1 al 32. Es la llave.

estado: nombre del estado, solo como etiqueta.

anio: año.

trimestre: trimestre del año, del 1 al 4.

periodo: etiqueta del periodo, por ejemplo 2024T4.

Precio de la vivienda

indice_shf: Índice SHF de Precios de la Vivienda, base 2017 igual a 100. Es la variable que el modelo va a predecir.

var_anual_shf_pct: variación porcentual del índice contra el mismo trimestre del año anterior.

Crédito

creditos: número de créditos y subsidios otorgados en el trimestre.

monto_real_mdp: monto total otorgado, en millones de pesos de 2024.

creditos_ind_vivienda: créditos individuales para comprar vivienda nueva o usada.

credito_promedio_real: monto promedio de esos créditos individuales, en pesos de 2024.

creditos_por_mil: créditos por cada mil habitantes.

Oferta

oferta_viviendas: viviendas en oferta al cierre del trimestre.

oferta_por_mil: viviendas en oferta por cada mil habitantes.

oferta_imputada: 1 si la oferta se estimó, 0 si es dato real.

oferta_metodologia_2019: 1 a partir de 2019, 0 antes.

Población, inflación y tasas

poblacion: población a mitad de año del estado.

inpc: INPC promedio del trimestre.

inflacion_anual_pct: variación porcentual anual del INPC.

tasa_cetes91: tasa de CETES a 91 días, promedio del trimestre, en porcentaje anual.

tasa_fondeo: tasa de fondeo bancario, promedio del trimestre, en porcentaje anual.

Valores de periodos anteriores

Las columnas que terminan en lag1 tienen el valor de la variable un trimestre antes. Las que terminan en lag4 tienen el valor de cuatro trimestres antes, es decir, del mismo trimestre del año anterior. Se calcularon para indice_shf, creditos_por_mil, credito_promedio_real, oferta_por_mil, tasa_fondeo e inflacion_anual_pct.

Estas columnas permiten predecir sin hacer trampa, porque solo usan información que ya se conocía en ese momento.
