#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Índice SHF de precios de la vivienda: tabla entidad × trimestre.

Material de apoyo del curso. El archivo de datos abiertos de la SHF trae
tres niveles mezclados en una sola hoja (series globales, entidades y
municipios seleccionados). Este script:

1. Lee el XLSX de datos abiertos de la SHF.
2. Se queda con las filas de ENTIDAD FEDERATIVA.
3. Asigna la clave INEGI de entidad (cve_ent, texto de 2 dígitos con cero
   a la izquierda) para poder cruzar con el inventario SNIIV limpio.
4. Construye la columna `periodo` (p. ej. "2025T1") y una fecha de cierre
   de trimestre.
5. Escribe la tabla larga entidad×trimestre en Parquet y CSV, y muestra de
   ejemplo el cruce con el inventario 2025.

Uso:
    python3 Proyecto/Herramientas/cruzar_shf.py

Nota: el índice SHF tiene base 2017 = 100. No son pesos: mide la evolución
relativa del precio de la vivienda con transacción hipotecaria.
"""

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
DATOS = RAIZ / "Proyecto" / "Conjunto_de_Datos"
XLSX_SHF = DATOS / "indice_shf_precios_vivienda_datos_abiertos.xlsx"
PARQUET_INVENTARIO = DATOS / "inventario_vivienda_2025_limpio.parquet"
SALIDA_PARQUET = DATOS / "indice_shf_entidad_trimestre.parquet"
SALIDA_CSV = DATOS / "indice_shf_entidad_trimestre.csv"

# Claves INEGI de entidad. Los nombres coinciden textualmente con los del
# inventario SNIIV limpio (verificado), así que el cruce por nombre o por
# clave es equivalente; se prefiere la clave por ser estable.
CVE_ENT = {
    "Aguascalientes": "01", "Baja California": "02", "Baja California Sur": "03",
    "Campeche": "04", "Coahuila": "05", "Colima": "06", "Chiapas": "07",
    "Chihuahua": "08", "Ciudad de México": "09", "Durango": "10",
    "Guanajuato": "11", "Guerrero": "12", "Hidalgo": "13", "Jalisco": "14",
    "México": "15", "Michoacán": "16", "Morelos": "17", "Nayarit": "18",
    "Nuevo León": "19", "Oaxaca": "20", "Puebla": "21", "Querétaro": "22",
    "Quintana Roo": "23", "San Luis Potosí": "24", "Sinaloa": "25",
    "Sonora": "26", "Tabasco": "27", "Tamaulipas": "28", "Tlaxcala": "29",
    "Veracruz": "30", "Yucatán": "31", "Zacatecas": "32",
}

# Mes de cierre de cada trimestre, para construir una fecha comparable
# con la columna `fecha` del inventario (fin de mes).
MES_CIERRE = {1: "03-31", 2: "06-30", 3: "09-30", 4: "12-31"}


def tabla_entidad_trimestre(xlsx_shf: Path = XLSX_SHF) -> pd.DataFrame:
    """Devuelve el índice SHF en formato largo: una fila por entidad y trimestre."""
    crudo = pd.read_excel(xlsx_shf)
    # Filas de entidad: tienen `Estado` y NO tienen `Municipio` (las filas
    # municipales también traen `Estado`, hay que excluirlas) ni `Global`.
    ent = crudo[crudo["Estado"].notna() & crudo["Municipio"].isna()].copy()

    desconocidas = set(ent["Estado"].unique()) - set(CVE_ENT)
    if desconocidas:
        raise ValueError(
            f"Entidades sin clave asignada: {sorted(desconocidas)}. "
            "Actualizar el diccionario CVE_ENT."
        )

    ent["cve_ent"] = ent["Estado"].map(CVE_ENT)
    ent = ent.rename(columns={
        "Estado": "entidad",
        "Año": "anio",
        "Trimestre": "trimestre",
        "Indice": "indice_shf",
    })
    ent["anio"] = ent["anio"].astype(int)
    ent["trimestre"] = ent["trimestre"].astype(int)
    ent["periodo"] = ent["anio"].astype(str) + "T" + ent["trimestre"].astype(str)
    ent["fecha_cierre"] = pd.to_datetime(
        ent["anio"].astype(str) + "-" + ent["trimestre"].map(MES_CIERRE)
    )
    # Variación anual (%) del índice: mismo trimestre del año anterior.
    ent = ent.sort_values(["cve_ent", "anio", "trimestre"])
    ent["var_anual_pct"] = (
        ent.groupby("cve_ent")["indice_shf"].pct_change(periods=4) * 100
    ).round(2)

    columnas = ["cve_ent", "entidad", "anio", "trimestre", "periodo",
                "fecha_cierre", "indice_shf", "var_anual_pct"]
    resultado = ent[columnas].reset_index(drop=True)

    duplicados = resultado.duplicated(subset=["cve_ent", "periodo"]).sum()
    if duplicados:
        raise ValueError(
            f"{duplicados} combinaciones entidad-periodo duplicadas: "
            "revisar el filtro de filas del XLSX de la SHF."
        )
    return resultado


def cruzar_con_inventario(shf: pd.DataFrame) -> pd.DataFrame:
    """Ejemplo de cruce: viviendas en inventario 2025 por entidad y trimestre
    junto con el índice SHF del trimestre correspondiente."""
    inv = pd.read_parquet(PARQUET_INVENTARIO)
    inv["trimestre"] = ((inv["mes"] - 1) // 3 + 1).astype(int)
    agregado = (
        inv.groupby(["cve_ent", "entidad", "anio", "trimestre"], observed=True)
        ["vivienda"].sum().reset_index(name="viviendas_inventario")
    )
    agregado["anio"] = agregado["anio"].astype(int)
    cruce = agregado.merge(
        shf[["cve_ent", "anio", "trimestre", "periodo", "indice_shf",
             "var_anual_pct"]],
        on=["cve_ent", "anio", "trimestre"],
        how="left",
    )
    return cruce


if __name__ == "__main__":
    shf = tabla_entidad_trimestre()
    shf.to_parquet(SALIDA_PARQUET, index=False)
    # En el CSV, cve_ent conserva los ceros porque se escribe como texto;
    # al RELEERLO hay que declarar dtype={"cve_ent": str}.
    shf.to_csv(SALIDA_CSV, index=False, encoding="utf-8")

    print("=" * 70)
    print("ÍNDICE SHF — TABLA ENTIDAD × TRIMESTRE")
    print("=" * 70)
    print(f"Filas: {len(shf):,}  |  Entidades: {shf['cve_ent'].nunique()}  |  "
          f"Periodos: {shf['periodo'].nunique()} "
          f"({shf['periodo'].iloc[0]} a {shf['periodo'].iloc[-1]})")
    print(f"Columnas: {list(shf.columns)}")
    print()
    print("Archivos escritos:")
    print(f"  - {SALIDA_PARQUET}")
    print(f"  - {SALIDA_CSV}")

    if PARQUET_INVENTARIO.exists():
        cruce = cruzar_con_inventario(shf)
        sin_indice = cruce["indice_shf"].isna().sum()
        print()
        print("Cruce de prueba con el inventario 2025 "
              f"({len(cruce)} combinaciones entidad-trimestre, "
              f"{sin_indice} sin índice SHF*):")
        print(cruce.head(8).to_string(index=False))
        print()
        print("* Los trimestres de 2025-2026 aún no publicados por la SHF "
              "quedan sin índice; se completan al actualizar el XLSX.")
    else:
        print("\nAviso: no se encontró el inventario limpio; "
              "correr antes limpiar_inventario.py para el cruce de prueba.")
