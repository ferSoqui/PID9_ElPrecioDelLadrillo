# Estructura estándar del proyecto

Organización unificada para todos los proyectos del curso.

```
Articulos/
    Revision/            Material para el articulo de review
        Fuentes/         PDFs de los articulos encontrados
        (la matriz de revision .xlsx o .csv va en este nivel)
    Investigacion/       Material para el articulo de investigacion
        Fuentes/
Recursos/                Archivos, notas y referencias para entender el tema
Proyecto/
    Propuesta/           Pre-propuesta y propuesta
    Conjunto_de_Datos/   Conjunto de datos del proyecto
    Herramientas/        Scripts para preparar y explorar los datos
    Documentacion/       Bitacora de los datos y figuras de exploracion
```

## Reglas del curso

- El conjunto de datos debe ser real, no simulado. Incluyan en
  `Proyecto/Conjunto_de_Datos/` un archivo (por ejemplo `FUENTE.md`) indicando
  de dónde se obtuvo: URL, institución y fecha de descarga.
- La matriz de revisión se trabaja en `Articulos/Revision/` (Excel o CSV).
- Fase actual: revisión de literatura, es decir, búsqueda de artículos y
  llenado de la matriz de revisión. Con eso se genera después la propuesta con
  base en el conjunto de datos encontrado.
- No cambien los nombres de estas carpetas; agreguen dentro lo que necesiten.
