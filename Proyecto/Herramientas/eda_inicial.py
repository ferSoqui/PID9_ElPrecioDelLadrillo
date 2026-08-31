#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exploracion inicial de los datos del proyecto (EDA de arranque).

Material de apoyo del curso. Genera las figuras que se comentan en
Proyecto/Documentacion/03_eda_inicial.md. Son figuras de exploracion,
no figuras finales de articulo: sirven para conocer los datos y para
que el equipo se haga preguntas, no para responderlas.

Figuras que produce (en Proyecto/Documentacion/figuras/):

    fig_01_viviendas_por_segmento.png
    fig_02_inventario_mensual_2025.png
    fig_03_shf_variacion_por_entidad.png
    fig_04_shf_series_contrastantes.png

Uso:
    python3 Proyecto/Herramientas/eda_inicial.py

Requiere: pandas, pyarrow, matplotlib. Antes hay que haber corrido
limpiar_inventario.py y cruzar_shf.py, porque lee sus salidas.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # sin ventana; solo escribe archivos PNG
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[2]
DATOS = RAIZ / "Proyecto" / "Conjunto_de_Datos"
FIGURAS = RAIZ / "Proyecto" / "Documentacion" / "figuras"

PARQUET_INVENTARIO = DATOS / "inventario_vivienda_2025_limpio.parquet"
PARQUET_SHF = DATOS / "indice_shf_entidad_trimestre.parquet"

# ---------------------------------------------------------------------------
# Estilo comun de las figuras
# ---------------------------------------------------------------------------
# Un solo tono para magnitudes; tonos distintos solo cuando cada serie es
# una entidad diferente. El orden de los colores es fijo, no se recicla.
AZUL = "#2a78d6"
NARANJA = "#eb6834"
AGUA = "#1baf7a"
AMARILLO = "#eda100"
GRIS_TEXTO = "#52514e"

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#cccccc",
    "axes.grid": True,
    "grid.color": "#e6e6e6",
    "grid.linewidth": 0.8,
    "axes.axisbelow": True,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.size": 10,
})


def guardar(fig, nombre: str) -> None:
    ruta = FIGURAS / nombre
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  - {ruta}")


def miles(x, _pos=None) -> str:
    return f"{x:,.0f}"


# ---------------------------------------------------------------------------
# Figura 1: viviendas en inventario por segmento de valor
# ---------------------------------------------------------------------------
def fig_segmento(inv: pd.DataFrame) -> None:
    # Suma de viviendas (no numero de filas) por segmento, respetando el
    # orden de la escala: Economica a Residencial plus.
    por_segmento = (
        inv.groupby("vivienda_valor", observed=False)["vivienda"].sum()
    )
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(por_segmento.index.astype(str), por_segmento.values,
            color=AZUL, height=0.62)
    for i, v in enumerate(por_segmento.values):
        ax.annotate(f"{v:,.0f}", (v, i), xytext=(5, 0),
                    textcoords="offset points", va="center",
                    fontsize=9, color=GRIS_TEXTO)
    ax.set_xlabel("Viviendas en inventario (suma de registros mensuales, 2025)")
    ax.set_title("Inventario 2025 por segmento de valor de la vivienda",
                 loc="left")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(miles))
    ax.set_xlim(0, por_segmento.max() * 1.14)
    ax.invert_yaxis()  # Economica arriba: la escala se lee de menor a mayor
    guardar(fig, "fig_01_viviendas_por_segmento.png")


# ---------------------------------------------------------------------------
# Figura 2: evolucion mensual del inventario nacional en 2025
# ---------------------------------------------------------------------------
MESES_ABREV = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
               "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def fig_mensual(inv: pd.DataFrame) -> None:
    mensual = inv.groupby("fecha")["vivienda"].sum().sort_index()
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(mensual.index, mensual.values, color=AZUL, linewidth=2,
            marker="o", markersize=5)
    ax.set_ylabel("Viviendas en inventario")
    ax.set_title("Inventario nacional de vivienda por mes, 2025", loc="left")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(miles))
    ax.set_ylim(0, mensual.max() * 1.12)  # eje desde cero: sin dramatizar
    ax.set_xticks(mensual.index)
    ax.set_xticklabels([MESES_ABREV[f.month - 1] for f in mensual.index])
    # Etiqueta directa solo en los puntos que llaman la atencion.
    for fecha in (mensual.idxmin(), mensual.idxmax()):
        v = mensual[fecha]
        ax.annotate(f"{v:,.0f}", (fecha, v), xytext=(0, 9),
                    textcoords="offset points", ha="center",
                    fontsize=9, color=GRIS_TEXTO)
    guardar(fig, "fig_02_inventario_mensual_2025.png")


# ---------------------------------------------------------------------------
# Figura 3: distribucion de la variacion anual del indice SHF por entidad
# ---------------------------------------------------------------------------
def fig_variacion_entidades(shf: pd.DataFrame) -> None:
    # Variaciones anuales trimestrales de 2021 en adelante: cada entidad
    # aporta una distribucion de ~22 observaciones. Un violin por entidad,
    # ordenado por mediana, deja ver nivel y dispersion a la vez.
    reciente = shf[(shf["anio"] >= 2021) & shf["var_anual_pct"].notna()]
    orden = (
        reciente.groupby("entidad", observed=True)["var_anual_pct"]
        .median().sort_values().index.tolist()
    )
    series = [reciente.loc[reciente["entidad"] == e, "var_anual_pct"].values
              for e in orden]

    fig, ax = plt.subplots(figsize=(8, 11))
    partes = ax.violinplot(series, vert=False, showmedians=True,
                           positions=range(1, len(orden) + 1))
    for cuerpo in partes["bodies"]:
        cuerpo.set_facecolor(AZUL)
        cuerpo.set_alpha(0.55)
        cuerpo.set_edgecolor("none")
    for clave in ("cmins", "cmaxes", "cbars", "cmedians"):
        partes[clave].set_color(AZUL)
        partes[clave].set_linewidth(1)
    ax.set_yticks(range(1, len(orden) + 1))
    ax.set_yticklabels(orden, fontsize=8.5)
    ax.set_xlabel("Variacion anual del indice SHF (%), trimestres 2021 a 2026")
    ax.set_title("Que tanto y que tan parejo sube el precio en cada entidad",
                 loc="left")
    guardar(fig, "fig_03_shf_variacion_por_entidad.png")


# ---------------------------------------------------------------------------
# Figura 4: series del indice SHF en entidades contrastantes
# ---------------------------------------------------------------------------
ENTIDADES_CONTRASTE = [
    # (nombre, color) en orden fijo; elegidas por contrastar en nivel y ritmo
    ("Quintana Roo", AZUL),
    ("Jalisco", NARANJA),
    ("Tamaulipas", AGUA),
    ("Ciudad de México", AMARILLO),
]


def fig_series_contraste(shf: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    for nombre, color in ENTIDADES_CONTRASTE:
        serie = shf[shf["entidad"] == nombre].sort_values("fecha_cierre")
        ax.plot(serie["fecha_cierre"], serie["indice_shf"],
                color=color, linewidth=2, label=nombre)
        ultimo = serie.iloc[-1]
        ax.annotate(nombre, (ultimo["fecha_cierre"], ultimo["indice_shf"]),
                    xytext=(6, 0), textcoords="offset points",
                    va="center", fontsize=8.5, color=GRIS_TEXTO)
    ax.axhline(100, color="#bbbbbb", linewidth=1, linestyle="--")
    ax.annotate("base 2017 = 100", (shf["fecha_cierre"].min(), 100),
                xytext=(0, 5), textcoords="offset points",
                fontsize=8, color=GRIS_TEXTO)
    ax.set_ylabel("Indice SHF (base 2017 = 100)")
    ax.set_title("Indice SHF de precios de la vivienda, entidades contrastantes",
                 loc="left")
    ax.legend(loc="upper left", frameon=False, fontsize=8.5)
    # Margen derecho extra para las etiquetas directas de fin de linea.
    ax.set_xlim(shf["fecha_cierre"].min(),
                shf["fecha_cierre"].max() + pd.Timedelta(days=900))
    guardar(fig, "fig_04_shf_series_contrastantes.png")


# ---------------------------------------------------------------------------
def main() -> None:
    FIGURAS.mkdir(parents=True, exist_ok=True)
    inv = pd.read_parquet(PARQUET_INVENTARIO)
    shf = pd.read_parquet(PARQUET_SHF)

    print("Datos cargados:")
    print(f"  - Inventario: {len(inv):,} filas "
          f"({inv['fecha'].min().date()} a {inv['fecha'].max().date()})")
    print(f"  - Indice SHF: {len(shf):,} filas "
          f"({shf['periodo'].iloc[0]} a {shf['periodo'].iloc[-1]})")
    print("Figuras escritas:")

    fig_segmento(inv)
    fig_mensual(inv)
    fig_variacion_entidades(shf)
    fig_series_contraste(shf)

    print("Listo. Las lecturas y preguntas de cada figura estan en "
          "Proyecto/Documentacion/03_eda_inicial.md")


if __name__ == "__main__":
    main()
