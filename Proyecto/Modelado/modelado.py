from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

AQUI = Path(__file__).resolve().parent
DATOS = AQUI.parent / "Conjunto_de_Datos"
FIGURAS = AQUI / "figuras"
FIGURAS.mkdir(exist_ok=True)

ULTIMO_ANIO_ENTRENAMIENTO = 2022
HORIZONTES = {1: "1 trimestre", 4: "1 año"}

# ------------------------------------------------------------------ 1. Datos
panel = pd.read_csv(DATOS / "dataset_final.csv", encoding="utf-8-sig")
panel["t"] = panel["anio"] * 4 + panel["trimestre"] - 1         

# El índice SHF se lee completo (2005 a 2026T2) para tener los rezagos de 2017 y los objetivos de 2026
shf = pd.read_excel(DATOS / "indice_shf_precios_vivienda_datos_abiertos.xlsx")
shf = shf[shf["Global"].isna() & shf["Municipio"].isna() & shf["Estado"].notna()].copy()
shf["estado"] = shf["Estado"].str.strip()
shf = shf.merge(panel[["cve_ent", "estado"]].drop_duplicates(), on="estado", how="inner")
shf = shf.rename(columns={"Año": "anio", "Trimestre": "trimestre", "Indice": "indice"})
shf["t"] = shf["anio"] * 4 + shf["trimestre"] - 1
shf = shf.sort_values(["cve_ent", "t"])
g = shf.groupby("cve_ent")["indice"]
shf["var_anual"] = (g.pct_change(4) * 100)                       # variable a predecir
shf["crec_trim"] = (g.pct_change(1) * 100)                       # crecimiento trimestral
gv = shf.groupby("cve_ent")["var_anual"]
shf["var_anual_lag1"] = gv.shift(1)
shf["var_anual_lag4"] = gv.shift(4)
# factor nacional: promedio de la variación anual de los OTROS 31 estados en el mismo trimestre
suma = shf.groupby("t")["var_anual"].transform("sum")
n = shf.groupby("t")["var_anual"].transform("count")
shf["factor_nacional"] = (suma - shf["var_anual"]) / (n - 1)

# ------------------------------------------------------------------ 2. Variables de entrada
VAR_PRECIO = ["var_anual", "var_anual_lag1", "var_anual_lag4", "crec_trim", "factor_nacional"]
VAR_OTRAS = ["creditos_por_mil", "credito_promedio_real", "oferta_por_mil", "oferta_metodologia_2019",
             "tasa_fondeo", "tasa_cetes91", "inflacion_anual_pct"]
ENTRADAS = VAR_PRECIO + VAR_OTRAS

base = panel[["cve_ent", "estado", "anio", "trimestre", "periodo", "t"] + VAR_OTRAS].merge(
    shf[["cve_ent", "t"] + VAR_PRECIO], on=["cve_ent", "t"], how="left")
objetivo = shf[["cve_ent", "t", "var_anual", "anio"]].rename(columns={"var_anual": "y", "anio": "anio_objetivo"})


def armar(h):
    """Filas con entradas en t y objetivo en t + h."""
    d = base.copy()
    d["t_objetivo"] = d["t"] + h
    d = d.merge(objetivo.rename(columns={"t": "t_objetivo"}), on=["cve_ent", "t_objetivo"], how="inner")
    assert d[ENTRADAS + ["y"]].notna().all().all(), "Hay vacíos en las entradas"
    d["periodo_objetivo"] = (d["t_objetivo"] // 4).astype(str) + "T" + (d["t_objetivo"] % 4 + 1).astype(str)
    return d


# ------------------------------------------------------------------ 3. Modelos
ALPHAS = {"Ridge": [0.01, 0.1, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000],
          "Lasso": [0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1, 3]}


def modelo(nombre, alpha):
    m = Ridge(alpha=alpha) if nombre == "Ridge" else Lasso(alpha=alpha, max_iter=50000)
    return make_pipeline(StandardScaler(), m)


def elegir_alpha(nombre, ent):
    """Elige alpha con validación por tiempo DENTRO del entrenamiento:
    entrena con objetivos anteriores a 2020, 2021 y 2022, y valida con cada uno de esos años."""
    mejor, mejor_mae = None, np.inf
    for a in ALPHAS[nombre]:
        errores = []
        for anio_val in [2020, 2021, 2022]:
            tr, va = ent[ent["anio_objetivo"] < anio_val], ent[ent["anio_objetivo"] == anio_val]
            m = modelo(nombre, a).fit(tr[ENTRADAS], tr["y"])
            errores.append(mean_absolute_error(va["y"], m.predict(va[ENTRADAS])))
        if np.mean(errores) < mejor_mae:
            mejor, mejor_mae = a, np.mean(errores)
    return mejor


resultados, por_estado, coefs, predicciones = [], [], [], []
for h, nombre_h in HORIZONTES.items():
    d = armar(h)
    ent = d[d["anio_objetivo"] <= ULTIMO_ANIO_ENTRENAMIENTO]
    pru = d[d["anio_objetivo"] > ULTIMO_ANIO_ENTRENAMIENTO].copy()
    print(f"\nHorizonte {nombre_h}: entrenamiento {len(ent)} filas "
          f"({ent['periodo_objetivo'].min()} a {ent['periodo_objetivo'].max()}), "
          f"prueba {len(pru)} filas ({pru['periodo_objetivo'].min()} a {pru['periodo_objetivo'].max()})")

    pred = {
        "Ingenuo": pru["var_anual"].values,                  # la variación de hoy se repite
        "Media": np.full(len(pru), ent["y"].mean()),         # promedio del entrenamiento
    }
    for nombre in ["Ridge", "Lasso"]:
        a = elegir_alpha(nombre, ent)
        m = modelo(nombre, a).fit(ent[ENTRADAS], ent["y"])
        pred[nombre] = m.predict(pru[ENTRADAS])
        print(f"   {nombre}: alpha = {a}")
        coefs += [{"modelo": nombre, "horizonte": nombre_h, "alpha": a, "variable": v, "coeficiente": round(x, 4)}
                  for v, x in zip(ENTRADAS, m[-1].coef_)]

    for nombre, p in pred.items():
        resultados.append({"modelo": nombre, "horizonte": nombre_h,
                           "MAE": mean_absolute_error(pru["y"], p),
                           "RMSE": np.sqrt(mean_squared_error(pru["y"], p)),
                           "R2": r2_score(pru["y"], p)})
        pru[f"pred_{nombre}"] = p
        e = (pru["y"] - p).abs().groupby(pru["estado"]).mean()
        por_estado += [{"modelo": nombre, "horizonte": nombre_h, "estado": s, "MAE": v} for s, v in e.items()]
    pru["horizonte"] = nombre_h
    predicciones.append(pru)

res = pd.DataFrame(resultados).round(3)
pe = pd.DataFrame(por_estado).round(3)
co = pd.DataFrame(coefs)
pr = pd.concat(predicciones)
res.to_csv(AQUI / "resultados_modelos.csv", index=False)
pe.to_csv(AQUI / "mae_por_estado.csv", index=False, encoding="utf-8-sig")
co.to_csv(AQUI / "coeficientes.csv", index=False)
pr[["horizonte", "estado", "periodo", "periodo_objetivo", "y"] + [c for c in pr.columns if c.startswith("pred_")]] \
    .round(3).to_csv(AQUI / "predicciones_prueba.csv", index=False, encoding="utf-8-sig")

print("\nResultados en el periodo de prueba:")
print(res.to_string(index=False))

# ------------------------------------------------------------------ 4. Figuras
COLORES = {"Ingenuo": "#9aa0a6", "Media": "#c7a76b", "Ridge": "#2a78d6", "Lasso": "#1baf7a"}

# 4.1 MAE por modelo y horizonte
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for ax, (h, nombre_h) in zip(axes, HORIZONTES.items()):
    r = res[res["horizonte"] == nombre_h]
    ax.bar(r["modelo"], r["MAE"], color=[COLORES[m] for m in r["modelo"]])
    for i, v in enumerate(r["MAE"]):
        ax.text(i, v + 0.03, f"{v:.2f}", ha="center", fontsize=9)
    ax.set_title(f"Horizonte: {nombre_h}")
    ax.set_ylabel("MAE (puntos porcentuales)")
    ax.spines[["top", "right"]].set_visible(False)
fig.suptitle("Error promedio en el periodo de prueba (2023 en adelante)", fontweight="bold")
plt.tight_layout()
plt.savefig(FIGURAS / "mae_por_modelo.png", dpi=130)
plt.close()

# 4.2 Real contra pronóstico: promedio de los 32 estados
fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
for ax, (h, nombre_h) in zip(axes, HORIZONTES.items()):
    p = pr[pr["horizonte"] == nombre_h].groupby("periodo_objetivo")[
        ["y", "pred_Ingenuo", "pred_Media", "pred_Lasso"]].mean()
    ax.plot(p.index, p["y"], color="black", linewidth=2, label="Real")
    ax.plot(p.index, p["pred_Ingenuo"], color=COLORES["Ingenuo"], linestyle="--", label="Ingenuo")
    ax.plot(p.index, p["pred_Media"], color=COLORES["Media"], linestyle=":", label="Media")
    ax.plot(p.index, p["pred_Lasso"], color=COLORES["Lasso"], label="Lasso")
    ax.set_title(f"Horizonte: {nombre_h}")
    ax.tick_params(axis="x", rotation=60, labelsize=8)
    ax.set_ylabel("Variación anual del índice SHF (%)")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
fig.suptitle("Variación anual real y pronosticada, promedio de los 32 estados", fontweight="bold")
plt.tight_layout()
plt.savefig(FIGURAS / "real_vs_pronostico.png", dpi=130)
plt.close()

# 4.3 MAE por estado (Lasso contra ingenuo, a 1 trimestre)
x = pe[pe["horizonte"] == "1 trimestre"].pivot(index="estado", columns="modelo", values="MAE").sort_values("Lasso")
fig, ax = plt.subplots(figsize=(8, 9))
yy = np.arange(len(x))
ax.barh(yy + 0.2, x["Ingenuo"], height=0.4, color=COLORES["Ingenuo"], label="Ingenuo")
ax.barh(yy - 0.2, x["Lasso"], height=0.4, color=COLORES["Lasso"], label="Lasso")
ax.set_yticks(yy, x.index, fontsize=8)
ax.set_xlabel("MAE (puntos porcentuales)")
ax.set_title("Error por estado a 1 trimestre", fontweight="bold")
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(FIGURAS / "mae_por_estado_1trimestre.png", dpi=130)
plt.close()

# 4.4 Peso de cada variable (coeficientes con variables estandarizadas)
fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharey=True)
for fila, nombre in enumerate(["Lasso", "Ridge"]):
    for col, nombre_h in enumerate(HORIZONTES.values()):
        ax = axes[fila, col]
        c = co[(co["modelo"] == nombre) & (co["horizonte"] == nombre_h)].set_index("variable")["coeficiente"]
        c = c.reindex(ENTRADAS[::-1])
        ax.barh(c.index, c.values, color=["#2a78d6" if v >= 0 else "#eb6834" for v in c.values])
        ax.axvline(0, color="gray", linewidth=0.8)
        ax.set_title(f"{nombre}, horizonte: {nombre_h}")
        ax.spines[["top", "right"]].set_visible(False)
fig.suptitle("Coeficientes (variables estandarizadas). Azul: sube el pronóstico; naranja: lo baja",
             fontweight="bold")
plt.tight_layout()
plt.savefig(FIGURAS / "coeficientes.png", dpi=130)
plt.close()

print(f"\nArchivos guardados en {AQUI}")
