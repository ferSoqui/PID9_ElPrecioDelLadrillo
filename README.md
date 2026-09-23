# PID9 El Precio del Ladrillo

En Proyecto/Conjunto_de_Datos queda un solo dataset, vivienda_mexico_2025.parquet (y su version en csv comprimido). Es la union de dos fuentes reales de gobierno: el inventario de vivienda 2025 de CONAVI (226,891 registros, con entidad, municipio, avance de obra, segmento de valor y tipo horizontal o vertical) cruzado por entidad y trimestre con el Indice SHF de Precios de la Vivienda (serie oficial trimestral desde 2005). Tenian tambien un conjunto propio mas chico armado con datos.gob.mx (320 filas por entidad y año), pero ese no traia ninguna columna de precio, solo conteos de vivienda registrada y variables macro, asi que no sirve para el objetivo del proyecto de identificar variables asociadas al precio. Por eso se quita y se deja este, que ya trae el indice de precios pegado a cada registro.

La matriz de revision ya tiene 50 fuentes reales. En Fuentes hay 37 PDF subidos, todavia faltan algunos por completar los 50.

Por ahora el trabajo es entender y limpiar este dataset antes de pensar en modelos. Revisen los tipos de cada columna, la columna vivienda_valor es categorica (de Economica a Residencial plus) no un precio en pesos, y hay que decidir como tratarla, como variable categorica ordenada o con otro criterio. Tambien esta duplicada la informacion de entidad en cve_ent y en el nombre, y el archivo trae registros mensuales de 2025 unidos a un indice que es trimestral, asi que cada registro de un mismo trimestre comparte el mismo valor de indice_shf, eso hay que tenerlo claro antes de usarlo como variable independiente.

Con eso hecho, exploren con graficas como se distribuye el inventario de vivienda por segmento y por entidad, como se mueve el indice_shf y su variacion anual a lo largo de 2025 por estado, y si hay relacion visible entre el avance de obra o el tipo de vivienda y el estado donde se concentra mas construccion.

Por ultimo, escriban su propio FUENTE.md en Proyecto/Conjunto_de_Datos explicando de donde salio cada parte del dataset (CONAVI y SHF) y terminen de subir a Fuentes los PDF que faltan.
