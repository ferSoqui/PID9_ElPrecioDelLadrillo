# PID9 El Precio del Ladrillo

En Proyecto/Conjunto_de_Datos queda un solo dataset, vivienda_mexico_2025.parquet (y su version en csv comprimido). Es la union de dos fuentes reales de gobierno: el inventario de vivienda 2025 de CONAVI (226,891 registros, con entidad, municipio, avance de obra, segmento de valor y tipo horizontal o vertical) cruzado por entidad y trimestre con el Indice SHF de Precios de la Vivienda (serie oficial trimestral desde 2005). Tenian tambien un conjunto propio mas chico armado con datos.gob.mx (320 filas por entidad y año), pero ese no traia ninguna columna de precio, solo conteos de vivienda registrada y variables macro, asi que no sirve para el objetivo del proyecto de identificar variables asociadas al precio. Por eso se quita y se deja este, que ya trae el indice de precios pegado a cada registro.

La matriz de revision ya tiene 50 fuentes reales. En Fuentes hay 37 PDF subidos, todavia faltan algunos por completar los 50.

Por ahora el trabajo es entender y limpiar este dataset antes de pensar en modelos. Revisen los tipos de cada columna, la columna vivienda_valor es categorica (de Economica a Residencial plus) no un precio en pesos, y hay que decidir como tratarla, como variable categorica ordenada o con otro criterio. Tambien esta duplicada la informacion de entidad en cve_ent y en el nombre, y el archivo trae registros mensuales de 2025 unidos a un indice que es trimestral, asi que cada registro de un mismo trimestre comparte el mismo valor de indice_shf, eso hay que tenerlo claro antes de usarlo como variable independiente.

Con eso hecho, exploren con graficas como se distribuye el inventario de vivienda por segmento y por entidad, como se mueve el indice_shf y su variacion anual a lo largo de 2025 por estado, y si hay relacion visible entre el avance de obra o el tipo de vivienda y el estado donde se concentra mas construccion.

Por ultimo, escriban su propio FUENTE.md en Proyecto/Conjunto_de_Datos explicando de donde salio cada parte del dataset (CONAVI y SHF) y terminen de subir a Fuentes los PDF que faltan.

Viernes 2 de Octubre -> Pre-procesamiento y finalización del conjunto de datos a usar

Miercoles 14 de Octubre -> Realizar apartado exploratorio de su conjunto de datos

## 19 de octubre

El cambio de alcance está bien hecho y bien justificado. Un panel de 32 estados por 32 trimestres con seis fuentes de gobierno sirve mucho más que el inventario de un solo año, FUENTE.md explica cada fuente y cada decisión, y el exploratorio del notebook está completo. El problema es que el repo no reproduce lo que FUENTE.md describe. dataset_final.csv no está subido, inpc_2015_dof.csv tampoco, y limpieza.py busca inpc_nacional.csv y 00_Pob_Mitad_1950_2070.csv cuando en el repo están como zip con otro nombre, así que el script se detiene al arrancar. Lo corrí renombrando los archivos y sí sale el 1,024 por 33, pero con 160 celdas vacías en los rezagos de inflación por el archivo de 2015 que falta. Siguen ahí vivienda_mexico_2025 del alcance viejo y la serie SP74665 que dicen que no usan, bórrenlas. Y subieron oferta y financiamientos de 2025 completos y de 2026 hasta julio, el índice SHF llega a 2026T2, pero el script corta en 2024. Para un modelo que pronostica esos trimestres son justo los que sirven para probar, extiendan el panel por lo menos a 2025T4.

Ahora el modelado. Aquí va punto por punto.

**Objetivo:** estimar la variación del precio de la vivienda por estado e identificar qué factores la mueven, que es lo que dice su propuesta.

**Variable a predecir:** var_anual_shf_pct de un estado en el siguiente trimestre y en el mismo trimestre del siguiente año, usando solo información que ya se conocía en el trimestre actual. Nunca el nivel del índice: con la tendencia y el estado el nivel da R2 de 0.99 y no aprendieron nada. Variables de entrada: los rezagos de la propia variación, el crecimiento trimestral, crédito, oferta, tasas e inflación, más un factor nacional que es el promedio de la variación de los demás estados, como en Mattera y Franses 2025.

**Modelos a usar:** primero dos pronósticos simples obligatorios, el ingenuo (la variación del próximo trimestre es la misma que la de hoy) y la media del periodo de entrenamiento. Un modelo vale solo si le gana al ingenuo; si no le gana, lo que están reportando es que el precio es persistente, no que el modelo sirva. Después los de su matriz, donde dominan regresión lineal y Random Forest: Ridge y Lasso (Preethi 2025, Wang 2021), Random Forest (Adetunji 2022, Giraldo 2023, Picardo 2019, Gutiérrez 2026), XGBoost o gradient boosting (Sharma 2024, Li 2023, Soltani 2022), y si les alcanza una red con rezagos como Xu y Zhang 2021. Para ver qué factores pesan, importancia por permutación o SHAP como Gutiérrez 2026 y An 2025.

**Validación:** por tiempo. Entrenan con 2017 a 2022 y prueban con 2023 en adelante. Nunca split aleatorio, porque dos trimestres seguidos del mismo estado son casi la misma fila y el modelo se ve mejor de lo que es. Cuando ya tengan un modelo que funcione, repitan con varios cortes (entrenar hasta 2020, hasta 2021, hasta 2022) y promedien el error. Eso se llama origen móvil y evita que el resultado dependa de un solo año de prueba.

**Métricas:** MAE, RMSE y R2 por horizonte, y el MAE por estado para ver dónde falla.

**Lo que deben esperar:** a un trimestre el ingenuo anda en MAE de 0.9 puntos y Ridge cerca de 0.6, y casi todo viene del precio rezagado. A un año nada le gana claramente a la media (MAE cerca de 2) y crédito y oferta aportan muy poco. Eso es un resultado válido, no un fracaso, y se reporta así, explicando que con ocho años de datos y dos choques (pandemia e inflación de 2022) no alcanza para más.

**Entrega:** todo el modelado va en Proyecto/Modelado, con scripts que corran desde la raíz del repo, la tabla de resultados por modelo y horizonte, las figuras y un RESULTADOS.md donde expliquen qué salió y por qué. Esa tabla es la sección de resultados del artículo. Además documenten todo, con sus gráficas, en el PDF o en el documento donde estén llevando el artículo, porque esa es la evidencia que revisamos.

04 Noviembre -> Repo reproducible (dataset_final.csv, inpc_2015_dof.csv, limpieza.py corriendo con los nombres que hay en el repo, borrar lo del alcance viejo), panel extendido a 2025, ingenuo y media, Ridge o Lasso con split temporal a un trimestre y a un año.

11 Noviembre -> Random Forest y XGBoost, origen móvil, importancia de variables, matriz completa a 60 con sus PDF, todo en Proyecto/Modelado/RESULTADOS.md y documentado con gráficas en PDF o en el documento del artículo.

## 6 de noviembre

Revise lo del 4 de noviembre y esta bien hecho: dataset_final.csv extendido a 2025T4 sin vacios, el alcance viejo borrado, modelado.py corriendo desde la raiz con ingenuo, media, Ridge y Lasso a un trimestre y a un año, split por tiempo, alpha elegido dentro del entrenamiento, y RESULTADOS.md con las conclusiones correctas. Reproduje el script y la tabla sale igual. Lasso a un trimestre con MAE de 0.64 contra 0.86 del ingenuo, y a un año nada le gana a la media, es justo lo que habia que esperar. Agregue inpc_2015_dof.csv a Conjunto_de_Datos para que limpieza.py corra completo; con el, regenera exactamente su dataset_final.csv.

Probe sobre su mismo script si se puede bajar mas y si, a un trimestre: agregarle a Lasso el crecimiento trimestral de uno, dos y tres trimestres antes baja el MAE de 0.64 a 0.58, y gana en los cuatro años de prueba y en 30 de 32 estados. Random Forest y boosting no le ganan a Lasso a un trimestre. A un año ningun modelo le gana claramente a la media; el que mas se acerca es Random Forest prediciendo el cambio de la variacion en vez de la variacion misma, y el resultado depende de con que año se pruebe, por eso el origen movil es obligatorio. No hay articulos que modelen el indice SHF por estado; los comparables (Kohlscheen 2025 con paises, Gupta 2020 con los estados de EUA, Mattera y Franses 2025) usan 40 años o mas de datos, y eso explica lo de un año. Va en la discusion.

**Objetivo:** el mismo del 19 de octubre. Variacion anual del indice SHF por estado a un trimestre y a un año, y que factores la mueven.

**Variable objetivo:** var_anual del siguiente trimestre y del mismo trimestre del año siguiente, sin cambios.

**Variables de entrada:** las que ya tienen mas tres rezagos del crecimiento trimestral: crec_trim de uno, dos y tres trimestres antes, calculados del mismo indice SHF con shift por estado. Para los arboles, ademas, una version del objetivo como cambio: y menos var_anual de hoy; la prediccion final se obtiene sumandole var_anual de hoy.

**Modelos:** ingenuo, media, Ridge y Lasso que ya tienen, mas Random Forest y XGBoost o HistGradientBoosting, cada uno sobre la variacion y sobre el cambio.

**Corridas que faltan:**
1. Lasso y Ridge con los tres rezagos del crecimiento trimestral, a un trimestre y a un año. Reporten la tabla con y sin rezagos.
2. Random Forest y XGBoost o HistGradientBoosting sobre la variacion y sobre el cambio, a un trimestre y a un año, con la misma particion.
3. Origen movil para todos los modelos: entrenar con objetivos hasta 2020, hasta 2021 y hasta 2022, probar con el año siguiente, y reportar el MAE de cada corte y el promedio.
4. Importancia por permutacion del mejor modelo de cada horizonte, sobre el periodo de prueba.

**Validacion y metricas:** las mismas. Particion por tiempo, MAE, RMSE y R2 por horizonte, MAE por estado, y la tabla de origen movil.

**Lo que deben esperar:** a un trimestre Lasso con rezagos cerca de 0.58 de MAE en su particion y cerca de 0.69 en el promedio del origen movil, contra 0.77 del Lasso actual y 0.98 del ingenuo; Lasso conserva los rezagos uno y dos y deja los demas en cero. Los arboles quedan entre 0.69 y 0.82. A un año la media queda cerca de 2.4, Random Forest sobre el cambio cerca de 2.4 en su particion y cerca de 1.9 en el origen movil, y los lineales peor que la media; se reporta asi. En importancia, a un trimestre solo pesan var_anual y crec_trim; a un año asoman tasa de fondeo, oferta y credito promedio con pesos chicos. Agreguen las tablas y figuras nuevas a RESULTADOS.md.

**Pendientes del repo:** matriz a 60 con sus PDF en Fuentes, y el PDF de resultados generado desde RESULTADOS.md con sus figuras.

**Articulo de investigacion:** `Plantilla_Articulo_Propuesta` tal cual, sin cambiar secciones. RESULTADOS.md ya es la seccion de resultados; el resto se arma asi:

| Seccion | Que va |
|---|---|
| Titulo | Ejemplo: "Pronostico de la variacion del precio de la vivienda por estado en Mexico con el indice SHF: persistencia, credito y oferta a uno y cuatro trimestres" |
| Resumen | Panel de 32 estados por 36 trimestres con seis fuentes de gobierno, seis modelos, MAE 0.58 contra 0.86 del ingenuo a un trimestre, a un año nada le gana a la media |
| I. Introduccion | Tres contribuciones: el panel estatal armado de fuentes publicas; medir cuanto aportan credito, oferta y tasas sobre la persistencia del precio; evaluar con origen movil |
| II. Trabajos relacionados | Los de la matriz agrupados en hedonicos de vivienda individual y en pronostico regional (Mattera y Franses 2025, Gupta 2020, Kohlscheen 2025). Cierre: ninguno pronostica el indice SHF por estado |
| III. Metodologia | Fuentes y FUENTE.md, construccion del panel, variables por bloque, el factor nacional, modelos, metricas |
| IV. Diseno experimental | Particion por tiempo, eleccion de alpha dentro del entrenamiento, origen movil, por que nunca split aleatorio |
| V. Resultados | Tablas de RESULTADOS.md con las corridas 1 a 4, MAE por estado, importancia |
| VI. Discusion | Por que a un trimestre es persistencia y a un año no alcanza la informacion, comparacion con los trabajos de 40 años de datos, los dos choques, limitaciones |
| VII. Conclusiones | Con los numeros. Futuro: mas años, datos municipales, variables de empleo |
| Referencias | IEEE; cada fuente de datos con URL y fecha de descarga de FUENTE.md |

**Articulo de revision:** `Plantilla_Articulo_Revision` tal cual. La matriz si cambia: agreguen estas columnas para las 60 filas: año; tipo de fuente; pais o region; escala (vivienda individual, ciudad, estado o region, pais); tipo de dato (corte transversal, serie de tiempo, panel); familia de modelo (hedonico o regresion, arboles o boosting, red neuronal, espacial, hibrido); pronostica en el tiempo (si o no); metrica principal y valor. Registren el metodo de busqueda.

| Seccion | Que va |
|---|---|
| I. Introduccion | PR1: que modelos se usan para explicar y pronosticar el precio de la vivienda entre 2017 y 2026 y que resultado reportan. PR2: que variables usan (de la vivienda, del entorno, macroeconomicas). PR3: cuantos pronostican en el tiempo y como validan |
| II. Metodo | Bases consultadas, cadena de busqueda, fecha, criterios de inclusion y exclusion, numeros que cuadren con las 60 filas |
| III. Panorama | Figura por año y familia de modelo; tabla por escala y tipo de dato. Sale de las columnas nuevas |
| IV. Problematicas | Datos faltantes, heterogeneidad espacial, pocos años de datos, validacion aleatoria en datos con tiempo, variables macro que no aportan |
| V. Soluciones | Por familia: hedonicos, espaciales, arboles y boosting, redes, factores y paneles |
| VI. Analisis | Que se repite (el propio precio domina, los hedonicos explican pero no pronostican) y cuando dos trabajos no son comparables |
| VII. Vacios | Casi nadie pronostica por estado en Mexico; pocos validan por tiempo; pocos comparan contra el ingenuo. De aqui sale el articulo de investigacion |
| VIII. Conclusiones | Responder PR1 a PR3 y limitaciones |

20 Noviembre -> todo junto: corridas 1 a 4 en RESULTADOS.md y el PDF, matriz a 60 con las columnas nuevas y los dos articulos completos en sus plantillas. Las corridas son de pocos dias; dediquen el tiempo a los articulos.
