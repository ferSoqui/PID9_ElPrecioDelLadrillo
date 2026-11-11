"""Modelado de la variación anual del índice SHF por estado, a 1 trimestre y a 1 año.

Corre desde la raíz del repo:
    python Proyecto/Modelado/modelado.py

Corridas:
    1. Ridge y Lasso con y sin los tres rezagos del crecimiento trimestral.
    2. Random Forest y HistGradientBoosting sobre la variación y sobre el cambio de la variación.
    3. Origen móvil: entrenar con objetivos hasta 2020, 2021 y 2022 y probar con el año siguiente.
    4. Importancia por permutación del mejor modelo de cada horizonte en el periodo de prueba.
    Además: tiempos de entrenamiento y pruebas de Diebold-Mariano y Wilcoxon.
"""
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Lasso, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

AQUI = Path(__file__).resolve().parent
DATOS = AQUI.parent / "Conjunto_de_Datos"
FIGURAS = AQUI / "figuras"
FIGURAS.mkdir(exist_ok=True)

ULTIMO_ANIO_ENTRENAMIENTO = 2022            # partición principal: objetivos hasta 2022 entrenan, 2023 en adelante prueban
CORTES_ORIGEN_MOVIL = [2020, 2021, 2022]    # entrenar hasta el corte, probar con el año siguiente
HORIZONTES = {1: "1 trimestre", 4: "1 año"}
SEMILLA = 0

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
shf["var_anual"] = g.pct_change(4) * 100                         # variable a predecir
shf["crec_trim"] = g.pct_change(1) * 100                         # crecimiento trimestral
gv = shf.groupby("cve_ent")["var_anual"]
shf["var_anual_lag1"] = gv.shift(1)
shf["var_anual_lag4"] = gv.shift(4)
gc = shf.groupby("cve_ent")["crec_trim"]
for k in (1, 2, 3):                                              # crecimiento trimestral de 1, 2 y 3 trimestres antes
    shf[f"crec_trim_lag{k}"] = gc.shift(k)
# factor nacional: promedio de la variación anual de los OTROS 31 estados en el mismo trimestre
suma = shf.groupby("t")["var_anual"].transform("sum")
n = shf.groupby("t")["var_anual"].transform("count")
shf["factor_nacional"] = (suma - shf["var_anual"]) / (n - 1)

# ------------------------------------------------------------------ 2. Variables de entrada
VAR_PRECIO = ["var_anual", "var_anual_lag1", "var_anual_lag4", "crec_trim", "factor_nacional"]
REZAGOS_CREC = ["crec_trim_lag1", "crec_trim_lag2", "crec_trim_lag3"]
VAR_OTRAS = ["creditos_por_mil", "credito_promedio_real", "oferta_por_mil", "oferta_metodologia_2019",
             "tasa_fondeo", "tasa_cetes91", "inflacion_anual_pct"]
ENTRADAS = VAR_PRECIO + VAR_OTRAS                                # versión de la primera entrega
ENTRADAS_R = VAR_PRECIO + REZAGOS_CREC + VAR_OTRAS               # con los tres rezagos del crecimiento trimestral

base = panel[["cve_ent", "estado", "anio", "trimestre", "periodo", "t"] + VAR_OTRAS].merge(
    shf[["cve_ent", "t"] + VAR_PRECIO + REZAGOS_CREC], on=["cve_ent", "t"], how="left")
objetivo = shf[["cve_ent", "t", "var_anual", "anio"]].rename(columns={"var_anual": "y", "anio": "anio_objetivo"})


def armar(h):
    """Filas con entradas en t y objetivo en t + h."""
    d = base.copy()
    d["t_objetivo"] = d["t"] + h
    d = d.merge(objetivo.rename(columns={"t": "t_objetivo"}), on=["cve_ent", "t_objetivo"], how="inner")
    assert d[ENTRADAS_R + ["y"]].notna().all().all(), "Hay vacíos en las entradas"
    d["periodo_objetivo"] = (d["t_objetivo"] // 4).astype(str) + "T" + (d["t_objetivo"] % 4 + 1).astype(str)
    return d


# ------------------------------------------------------------------ 3. Modelos
ALPHAS = {"Ridge": [0.01, 0.1, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000],
          "Lasso": [0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1, 3]}


def lineal(nombre, alpha):
    m = Ridge(alpha=alpha) if nombre == "Ridge" else Lasso(alpha=alpha, max_iter=50000)
    return make_pipeline(StandardScaler(), m)


def anios_validacion(ent, corte):
    """Los tres últimos años del entrenamiento que tengan entrenamiento antes (al menos un año completo)."""
    minimo = 32 * 4
    return [a for a in (corte - 2, corte - 1, corte) if (ent["anio_objetivo"] < a).sum() >= minimo]


def elegir_alpha(nombre, ent, entradas, corte):
    """Elige alpha con validación por tiempo DENTRO del entrenamiento: entrena con los objetivos
    anteriores a cada año de validación y valida con ese año. Con el corte 2022 son 2020, 2021 y 2022."""
    mejor, mejor_mae = None, np.inf
    for a in ALPHAS[nombre]:
        errores = []
        for anio_val in anios_validacion(ent, corte):
            tr, va = ent[ent["anio_objetivo"] < anio_val], ent[ent["anio_objetivo"] == anio_val]
            m = lineal(nombre, a).fit(tr[entradas], tr["y"])
            errores.append(mean_absolute_error(va["y"], m.predict(va[entradas])))
        if np.mean(errores) < mejor_mae:
            mejor, mejor_mae = a, np.mean(errores)
    return mejor


def arbol(tipo):
    if tipo == "RF":
        return RandomForestRegressor(n_estimators=500, min_samples_leaf=5, max_features=0.5,
                                     n_jobs=-1, random_state=SEMILLA)
    return HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_depth=3,
                                         min_samples_leaf=20, random_state=SEMILLA)


class Pronostico:
    """Envuelve un modelo para que siempre devuelva la variación pronosticada.
    Si objetivo='cambio', el modelo aprende y - var_anual y la predicción final le suma var_anual de hoy."""

    def __init__(self, est, entradas, objetivo_tipo="variacion"):
        self.est, self.entradas, self.tipo = est, entradas, objetivo_tipo

    def fit(self, d):
        y = d["y"] - d["var_anual"] if self.tipo == "cambio" else d["y"]
        self.est.fit(d[self.entradas], y)
        return self

    def predict(self, d):
        p = self.est.predict(d[self.entradas])
        return p + d["var_anual"].values if self.tipo == "cambio" else p


# Nombre del modelo -> (familia, entradas, objetivo)
MODELOS = {
    "Ridge":                  ("Ridge", ENTRADAS, "variacion"),
    "Lasso":                  ("Lasso", ENTRADAS, "variacion"),
    "Ridge + rezagos":        ("Ridge", ENTRADAS_R, "variacion"),
    "Lasso + rezagos":        ("Lasso", ENTRADAS_R, "variacion"),
    "Random Forest":          ("RF", ENTRADAS_R, "variacion"),
    "Random Forest (cambio)": ("RF", ENTRADAS_R, "cambio"),
    "HistGB":                 ("HGB", ENTRADAS_R, "variacion"),
    "HistGB (cambio)":        ("HGB", ENTRADAS_R, "cambio"),
}
ORDEN = ["Ingenuo", "Media"] + list(MODELOS)


def correr(d, corte, anio_prueba=None):
    """Entrena con objetivos <= corte y pronostica la prueba (objetivos > corte, o solo anio_prueba)."""
    ent = d[d["anio_objetivo"] <= corte]
    pru = d[d["anio_objetivo"] > corte] if anio_prueba is None else d[d["anio_objetivo"] == anio_prueba]
    pru = pru.copy()
    pred = {"Ingenuo": pru["var_anual"].values, "Media": np.full(len(pru), ent["y"].mean())}
    ajustados, alphas = {}, {}
    tiempos = {"Ingenuo": 0.0, "Media": 0.0}
    for nombre, (fam, entradas, tipo) in MODELOS.items():
        t0 = time.perf_counter()                                 # incluye la elección de alpha
        if fam in ("Ridge", "Lasso"):
            alphas[nombre] = elegir_alpha(fam, ent, entradas, corte)
            est = lineal(fam, alphas[nombre])
        else:
            est = arbol(fam)
        m = Pronostico(est, entradas, tipo).fit(ent)
        tiempos[nombre] = time.perf_counter() - t0
        pred[nombre] = m.predict(pru)
        ajustados[nombre] = m
    return ent, pru, pred, ajustados, alphas, tiempos


def metricas(y, p):
    return {"MAE": mean_absolute_error(y, p), "RMSE": np.sqrt(mean_squared_error(y, p)), "R2": r2_score(y, p)}


def importancia_permutacion(m, pru, repeticiones=30):
    """Aumento del MAE al revolver cada variable en el periodo de prueba (promedio de varias repeticiones)."""
    rng = np.random.default_rng(SEMILLA)
    base_mae = mean_absolute_error(pru["y"], m.predict(pru))
    filas = []
    for v in m.entradas:
        aumentos = []
        for _ in range(repeticiones):
            x = pru.copy()
            x[v] = rng.permutation(x[v].values)
            if v == "var_anual" and m.tipo == "cambio":
                # var_anual entra como variable y también se suma al final; solo se revuelve como variable
                p = m.est.predict(x[m.entradas]) + pru["var_anual"].values
            else:
                p = m.predict(x)
            aumentos.append(mean_absolute_error(pru["y"], p) - base_mae)
        filas.append({"variable": v, "aumento_MAE": np.mean(aumentos), "desv": np.std(aumentos)})
    return pd.DataFrame(filas).sort_values("aumento_MAE", ascending=False)


resultados, por_estado, coefs, predicciones, origen, importancias = [], [], [], [], [], []
mejores = {}
for h, nombre_h in HORIZONTES.items():
    d = armar(h)

    # --- Partición principal
    ent, pru, pred, ajustados, alphas, _ = correr(d, ULTIMO_ANIO_ENTRENAMIENTO)
    print(f"\nHorizonte {nombre_h}: entrenamiento {len(ent)} filas "
          f"({ent['periodo_objetivo'].min()} a {ent['periodo_objetivo'].max()}), "
          f"prueba {len(pru)} filas ({pru['periodo_objetivo'].min()} a {pru['periodo_objetivo'].max()})")
    for nombre, a in alphas.items():
        print(f"   {nombre}: alpha = {a}")
        fam, entradas, _ = MODELOS[nombre]
        coefs += [{"modelo": nombre, "horizonte": nombre_h, "alpha": a, "variable": v, "coeficiente": round(x, 4)}
                  for v, x in zip(entradas, ajustados[nombre].est[-1].coef_)]

    for nombre in ORDEN:
        p = pred[nombre]
        resultados.append({"modelo": nombre, "horizonte": nombre_h, **metricas(pru["y"], p)})
        pru[f"pred_{nombre}"] = p
        e = (pru["y"] - p).abs().groupby(pru["estado"]).mean()
        por_estado += [{"modelo": nombre, "horizonte": nombre_h, "estado": s, "MAE": v} for s, v in e.items()]
    pru["horizonte"] = nombre_h
    predicciones.append(pru)

    # --- Origen móvil
    for corte in CORTES_ORIGEN_MOVIL:
        _, pru_c, pred_c, _, _, tiempos_c = correr(d, corte, anio_prueba=corte + 1)
        for nombre in ORDEN:
            origen.append({"modelo": nombre, "horizonte": nombre_h, "corte": corte, "anio_prueba": corte + 1,
                           "MAE": mean_absolute_error(pru_c["y"], pred_c[nombre]),
                           "RMSE": np.sqrt(mean_squared_error(pru_c["y"], pred_c[nombre])),
                           "tiempo_s": tiempos_c[nombre]})

    # --- Importancia por permutación del mejor modelo con variables (la media no usa ninguna)
    r = pd.DataFrame([x for x in resultados if x["horizonte"] == nombre_h and x["modelo"] in MODELOS])
    mejor = r.sort_values("MAE").iloc[0]["modelo"]
    mejores[nombre_h] = mejor
    imp = importancia_permutacion(ajustados[mejor], pru)
    imp.insert(0, "horizonte", nombre_h)
    imp.insert(0, "modelo", mejor)
    importancias.append(imp)

res = pd.DataFrame(resultados).round(3)
pe = pd.DataFrame(por_estado).round(3)
co = pd.DataFrame(coefs)
pr = pd.concat(predicciones)
om = pd.DataFrame(origen)
om_tabla = om.pivot_table(index=["horizonte", "modelo"], columns="anio_prueba", values="MAE")
om_tabla.columns = [f"prueba_{c}" for c in om_tabla.columns]
om_tabla["promedio"] = om_tabla.mean(axis=1)
om_tabla = om_tabla.reset_index()
om_tabla["modelo"] = pd.Categorical(om_tabla["modelo"], ORDEN, ordered=True)
om_tabla = om_tabla.sort_values(["horizonte", "modelo"], ascending=[False, True]).round(3)
imp = pd.concat(importancias).round(4)
# Resumen del origen móvil: media y desviación estándar de los tres cortes
om_res = om.groupby(["horizonte", "modelo"])[["MAE", "RMSE", "tiempo_s"]].agg(["mean", "std"])
om_res.columns = [f"{a}_{b}" for a, b in om_res.columns]
om_res = om_res.reset_index()
om_res["modelo"] = pd.Categorical(om_res["modelo"], ORDEN, ordered=True)
om_res = om_res.sort_values(["horizonte", "modelo"], ascending=[False, True]).round(3)


# ------------------------------------------------------------------ 3b. Significancia estadística
def diebold_mariano(d_t, h):
    """Prueba de Diebold-Mariano con la corrección de Harvey, Leybourne y Newbold (1997).
    d_t: serie de diferencias de pérdida por trimestre objetivo. Varianza HAC con h - 1 rezagos."""
    d_t = np.asarray(d_t, dtype=float)
    T, dbar = len(d_t), d_t.mean()
    g = [np.mean((d_t[k:] - dbar) * (d_t[:T - k] - dbar)) for k in range(h)]
    var = (g[0] + 2 * sum(g[1:])) / T
    dm = dbar / np.sqrt(var)
    dm *= np.sqrt((T + 1 - 2 * h + h * (h - 1) / T) / T)
    p = 2 * stats.t.sf(abs(dm), df=T - 1)
    return dm, p, T


PARES = {"1 trimestre": [("Lasso + rezagos", "Ingenuo"), ("Lasso + rezagos", "Lasso"),
                         ("Lasso + rezagos", "Random Forest (cambio)")],
         "1 año": [("HistGB", "Media"), ("HistGB (cambio)", "Media"), ("HistGB", "Ingenuo")]}
signif = []
for h, nombre_h in HORIZONTES.items():
    q = pr[pr["horizonte"] == nombre_h]
    for a, b in PARES[nombre_h]:
        ea, eb = (q["y"] - q[f"pred_{a}"]).abs(), (q["y"] - q[f"pred_{b}"]).abs()
        d_t = (ea - eb).groupby(q["periodo_objetivo"]).mean()          # diferencia de MAE por trimestre
        dm, p, T = diebold_mariano(d_t.values, h)
        por_est = pd.DataFrame({"a": ea, "b": eb, "e": q["estado"]}).groupby("e").mean()
        w = stats.wilcoxon(por_est["a"], por_est["b"])
        signif.append({"horizonte": nombre_h, "modelo": a, "contra": b,
                       "dif_MAE": ea.mean() - eb.mean(), "DM": dm, "p_DM": p, "trimestres": T,
                       "Wilcoxon_W": w.statistic, "p_Wilcoxon": w.pvalue, "estados": len(por_est),
                       "estados_gana": int((por_est["a"] < por_est["b"]).sum())})
sig = pd.DataFrame(signif).round(4)

res.to_csv(AQUI / "resultados_modelos.csv", index=False)
pe.to_csv(AQUI / "mae_por_estado.csv", index=False, encoding="utf-8-sig")
co.to_csv(AQUI / "coeficientes.csv", index=False)
om_tabla.to_csv(AQUI / "origen_movil.csv", index=False)
om_res.to_csv(AQUI / "origen_movil_resumen.csv", index=False)
sig.to_csv(AQUI / "significancia.csv", index=False)
imp.to_csv(AQUI / "importancia_permutacion.csv", index=False)
pr[["horizonte", "estado", "periodo", "periodo_objetivo", "y"] + [c for c in pr.columns if c.startswith("pred_")]] \
    .round(3).to_csv(AQUI / "predicciones_prueba.csv", index=False, encoding="utf-8-sig")

pd.set_option("display.width", 200)
print("\nResultados en el periodo de prueba:")
print(res.to_string(index=False))
print("\nOrigen móvil (MAE):")
print(om_tabla.to_string(index=False))
print("\nOrigen móvil, media y desviación estándar:")
print(om_res.to_string(index=False))
print("\nSignificancia:")
print(sig.to_string(index=False))
print("\nImportancia por permutación:")
print(imp.to_string(index=False))

# ------------------------------------------------------------------ 4. Figuras
COLORES = {"Ingenuo": "#9aa0a6", "Media": "#c7a76b", "Ridge": "#9cc3ee", "Lasso": "#8fd9bd",
           "Ridge + rezagos": "#2a78d6", "Lasso + rezagos": "#1baf7a",
           "Random Forest": "#f2b48f", "Random Forest (cambio)": "#eb6834",
           "HistGB": "#c9a7e8", "HistGB (cambio)": "#8a4fc9"}


def barras_por_modelo(tabla, columna, titulo, archivo):
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    for ax, nombre_h in zip(axes, HORIZONTES.values()):
        r = tabla[tabla["horizonte"] == nombre_h].set_index("modelo").reindex(ORDEN)
        ax.bar(range(len(r)), r[columna], color=[COLORES[m] for m in r.index])
        for i, v in enumerate(r[columna]):
            ax.text(i, v + 0.03, f"{v:.2f}", ha="center", fontsize=8)
        ax.set_xticks(range(len(r)), r.index, rotation=55, ha="right", fontsize=8)
        ax.set_title(f"Horizonte: {nombre_h}")
        ax.set_ylabel("MAE (puntos porcentuales)")
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(titulo, fontweight="bold")
    plt.tight_layout()
    plt.savefig(FIGURAS / archivo, dpi=130)
    plt.close()


# 4.1 MAE por modelo y horizonte (partición principal)
barras_por_modelo(res, "MAE", "Error promedio en el periodo de prueba (2023 en adelante)", "mae_por_modelo.png")

# 4.2 MAE promedio del origen móvil
barras_por_modelo(om_tabla.rename(columns={"promedio": "MAE"}), "MAE",
                  "Origen móvil: MAE promedio de las pruebas 2021, 2022 y 2023", "origen_movil.png")

# 4.3 Real contra pronóstico: promedio de los 32 estados
fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
for ax, nombre_h in zip(axes, HORIZONTES.values()):
    mejor = mejores[nombre_h]
    p = pr[pr["horizonte"] == nombre_h].groupby("periodo_objetivo")[
        ["y", "pred_Ingenuo", "pred_Media", f"pred_{mejor}"]].mean()
    ax.plot(p.index, p["y"], color="black", linewidth=2, label="Real")
    ax.plot(p.index, p["pred_Ingenuo"], color=COLORES["Ingenuo"], linestyle="--", label="Ingenuo")
    ax.plot(p.index, p["pred_Media"], color=COLORES["Media"], linestyle=":", label="Media")
    ax.plot(p.index, p[f"pred_{mejor}"], color=COLORES[mejor], label=mejor)
    ax.set_title(f"Horizonte: {nombre_h}")
    ax.tick_params(axis="x", rotation=60, labelsize=8)
    ax.set_ylabel("Variación anual del índice SHF (%)")
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
fig.suptitle("Variación anual real y pronosticada, promedio de los 32 estados", fontweight="bold")
plt.tight_layout()
plt.savefig(FIGURAS / "real_vs_pronostico.png", dpi=130)
plt.close()

# 4.4 MAE por estado a 1 trimestre: mejor modelo contra ingenuo
mejor1 = mejores["1 trimestre"]
x = pe[pe["horizonte"] == "1 trimestre"].pivot(index="estado", columns="modelo", values="MAE").sort_values(mejor1)
fig, ax = plt.subplots(figsize=(8, 9))
yy = np.arange(len(x))
ax.barh(yy + 0.2, x["Ingenuo"], height=0.4, color=COLORES["Ingenuo"], label="Ingenuo")
ax.barh(yy - 0.2, x[mejor1], height=0.4, color=COLORES[mejor1], label=mejor1)
ax.set_yticks(yy, x.index, fontsize=8)
ax.set_xlabel("MAE (puntos porcentuales)")
ax.set_title("Error por estado a 1 trimestre", fontweight="bold")
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(FIGURAS / "mae_por_estado_1trimestre.png", dpi=130)
plt.close()

# 4.5 Coeficientes de Ridge y Lasso con rezagos (variables estandarizadas)
fig, axes = plt.subplots(2, 2, figsize=(12, 8.5), sharey=True)
for fila, nombre in enumerate(["Lasso + rezagos", "Ridge + rezagos"]):
    for col, nombre_h in enumerate(HORIZONTES.values()):
        ax = axes[fila, col]
        c = co[(co["modelo"] == nombre) & (co["horizonte"] == nombre_h)].set_index("variable")["coeficiente"]
        c = c.reindex(ENTRADAS_R[::-1])
        ax.barh(c.index, c.values, color=["#2a78d6" if v >= 0 else "#eb6834" for v in c.values])
        ax.axvline(0, color="gray", linewidth=0.8)
        ax.set_title(f"{nombre}, horizonte: {nombre_h}")
        ax.spines[["top", "right"]].set_visible(False)
fig.suptitle("Coeficientes (variables estandarizadas). Azul: sube el pronóstico; naranja: lo baja",
             fontweight="bold")
plt.tight_layout()
plt.savefig(FIGURAS / "coeficientes.png", dpi=130)
plt.close()

# 4.6 Importancia por permutación
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for ax, nombre_h in zip(axes, HORIZONTES.values()):
    i = imp[imp["horizonte"] == nombre_h].sort_values("aumento_MAE")
    ax.barh(i["variable"], i["aumento_MAE"], xerr=i["desv"], color=COLORES[mejores[nombre_h]])
    ax.axvline(0, color="gray", linewidth=0.8)
    ax.set_title(f"{mejores[nombre_h]}, horizonte: {nombre_h}", fontsize=10)
    ax.set_xlabel("Aumento del MAE al revolver la variable")
    ax.tick_params(axis="y", labelsize=8)
    ax.spines[["top", "right"]].set_visible(False)
fig.suptitle("Importancia por permutación en el periodo de prueba", fontweight="bold")
plt.tight_layout()
plt.savefig(FIGURAS / "importancia_permutacion.png", dpi=130)
plt.close()

print(f"\nArchivos guardados en {AQUI}")
