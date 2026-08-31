#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Limpieza del inventario de vivienda 2025 (SNIIV / CONAVI).

Material de apoyo del curso. Este script:

1. Lee el CSV crudo forzando TODAS las claves geográficas como texto
   (si se leen como número, '01' se convierte en 1 y se pierde el cero
   a la izquierda, rompiendo el cruce con otras fuentes como el INEGI
   o el índice SHF).
2. Corrige el mojibake (texto mal decodificado, p. ej. "EconÃ³mica"
   en lugar de "Económica"), producto de un archivo UTF-8 leído alguna
   vez como Latin-1 y vuelto a guardar.
3. Convierte las columnas categóricas en categorías ORDENADAS cuando
   el orden tiene sentido (valor de la vivienda, rango de UMA, avance
   de obra), de modo que ordenamientos y gráficas respeten la escala
   real y no el orden alfabético.
4. Tipifica fecha como datetime y vivienda (conteo) como entero.
5. Escribe el resultado en Parquet (conserva tipos y categorías) y,
   como alternativa, en CSV comprimido (zip).

Uso:
    python3 Proyecto/Herramientas/limpiar_inventario.py

Los archivos de entrada/salida viven en Proyecto/Conjunto_de_Datos/.
"""

from pathlib import Path
import zipfile

import pandas as pd

# ---------------------------------------------------------------------------
# Rutas (relativas a la raíz del repositorio, sin importar desde dónde se corra)
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[2]  # .../PID9_ElPrecioDelLadrillo
DATOS = RAIZ / "Proyecto" / "Conjunto_de_Datos"
CSV_CRUDO = DATOS / "inventario_vivienda_2025_v2.csv"
PARQUET_LIMPIO = DATOS / "inventario_vivienda_2025_limpio.parquet"
CSV_LIMPIO_ZIP = DATOS / "inventario_vivienda_2025_limpio.csv.zip"

# ---------------------------------------------------------------------------
# Órdenes de las escalas categóricas
# ---------------------------------------------------------------------------
ORDEN_VALOR = [
    "Económica",
    "Popular",
    "Tradicional",
    "Media",
    "Residencial",
    "Residencial plus",
]

ORDEN_UMA = [
    "0 hasta 60",
    "Mayor o igual 60 hasta 136",
    "Mayor o igual 136 hasta 158",
    "Mayor a 158 hasta 175",
    "Mayor a 175 hasta 190",
    "Mayor a 190",
]

ORDEN_AVANCE = [
    "Sin reporte",
    "Avance 0",
    "Avance 1-19",
    "Avance 20-39",
    "Avance 40-59",
    "Avance 60-79",
    "Avance 80-99",
    "Sin HBT",
    "HBT - 5m",
    "HBT + 5m",
]


def corregir_mojibake(texto: str) -> str:
    """Repara cadenas UTF-8 que fueron decodificadas como Latin-1.

    Ejemplo: "EconÃ³mica" -> "Económica". Si la cadena no está dañada,
    la conversión falla y se devuelve tal cual.
    """
    if not isinstance(texto, str):
        return texto
    try:
        reparado = texto.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return texto
    return reparado


def limpiar(csv_crudo: Path = CSV_CRUDO) -> pd.DataFrame:
    """Lee el CSV crudo y devuelve el DataFrame limpio y tipificado."""
    # dtype=str en las claves: NUNCA dejar que pandas las infiera como int.
    # encoding="utf-8-sig" descarta el BOM inicial del archivo.
    df = pd.read_csv(
        csv_crudo,
        encoding="utf-8-sig",
        dtype={
            "cve_ent": str,
            "cve_mun": str,
            "entidad": str,
            "municipio": str,
            "avance_obra": str,
            "vivienda_valor": str,
            "vivienda_uma": str,
            "tipo": str,
        },
    )
    filas_crudas = len(df)

    # --- Mojibake en todas las columnas de texto -------------------------
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].map(corregir_mojibake)

    # --- Claves geográficas como texto con ceros a la izquierda ----------
    # cve_ent: 2 dígitos (01-32). cve_mun: 3 dígitos dentro de la entidad.
    df["cve_ent"] = df["cve_ent"].str.strip().str.zfill(2)
    df["cve_mun"] = df["cve_mun"].str.strip().str.zfill(3)
    # Clave compuesta de 5 dígitos (igual a la clave de municipio del INEGI),
    # útil para cruces a nivel municipal.
    df["cve_ent_mun"] = df["cve_ent"] + df["cve_mun"]

    # --- Tipos ------------------------------------------------------------
    df["fecha"] = pd.to_datetime(df["fecha"], format="%Y-%m-%d")
    df["anio"] = df["anio"].astype("int16")
    df["mes"] = df["mes"].astype("int8")
    df["vivienda"] = pd.to_numeric(df["vivienda"], errors="raise").astype("int32")

    # --- Categorías ordenadas --------------------------------------------
    def categorica_ordenada(serie: pd.Series, orden: list) -> pd.Series:
        faltantes = set(serie.dropna().unique()) - set(orden)
        if faltantes:
            raise ValueError(
                f"Categorías no previstas en '{serie.name}': {sorted(faltantes)}. "
                "Revisar el orden definido al inicio del script."
            )
        return pd.Categorical(serie, categories=orden, ordered=True)

    df["vivienda_valor"] = categorica_ordenada(df["vivienda_valor"], ORDEN_VALOR)
    df["vivienda_uma"] = categorica_ordenada(df["vivienda_uma"], ORDEN_UMA)
    df["avance_obra"] = categorica_ordenada(df["avance_obra"], ORDEN_AVANCE)
    # Sin orden intrínseco:
    df["tipo"] = df["tipo"].astype("category")
    df["entidad"] = df["entidad"].astype("category")

    assert len(df) == filas_crudas, "La limpieza no debe perder filas"
    return df


def escribir_salidas(df: pd.DataFrame) -> None:
    """Escribe el Parquet y el CSV comprimido de respaldo."""
    df.to_parquet(PARQUET_LIMPIO, index=False)

    # Alternativa para quien no use Parquet. OJO: el CSV no conserva los
    # tipos; al releerlo hay que volver a declarar dtype=str en las claves.
    with zipfile.ZipFile(CSV_LIMPIO_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "inventario_vivienda_2025_limpio.csv",
            df.to_csv(index=False),
        )


def resumen(df: pd.DataFrame) -> None:
    print("=" * 70)
    print("RESUMEN DE LA LIMPIEZA")
    print("=" * 70)
    print(f"Filas:    {len(df):,}")
    print(f"Columnas: {len(df.columns)} -> {list(df.columns)}")
    print()
    print("Tipos de columna:")
    print(df.dtypes.to_string())
    print()
    print("Categorías de vivienda_valor (ordenadas):")
    print("  " + " < ".join(df["vivienda_valor"].cat.categories))
    print()
    print(f"Entidades: {df['cve_ent'].nunique()}  |  "
          f"Municipios (clave compuesta): {df['cve_ent_mun'].nunique()}")
    print(f"Periodo: {df['fecha'].min().date()} a {df['fecha'].max().date()}")
    print(f"Total de viviendas registradas: {df['vivienda'].sum():,}")
    print()
    print("Verificaciones:")
    print(f"  - Mojibake corregido: "
          f"{'Económica' in df['vivienda_valor'].cat.categories}")
    print(f"  - Claves con ceros a la izquierda (ej.): "
          f"cve_ent={df['cve_ent'].iloc[0]!r}, cve_mun={df['cve_mun'].iloc[0]!r}")
    print(f"  - Valores nulos totales: {int(df.isna().sum().sum())}")
    print()
    print("Archivos escritos:")
    for ruta in (PARQUET_LIMPIO, CSV_LIMPIO_ZIP):
        print(f"  - {ruta}  ({ruta.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    datos = limpiar()
    escribir_salidas(datos)
    resumen(datos)
