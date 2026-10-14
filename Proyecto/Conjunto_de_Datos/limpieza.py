
from glob import glob
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
CRUDOS = AQUI / "datos_crudos" if (AQUI / "datos_crudos").is_dir() else AQUI
SALIDA = AQUI / "dataset_final.csv"
ANIO_INI, ANIO_FIN = 2016, 2024     
ANIO_SALIDA = 2017                  


def archivos(patron):
    lista = sorted(glob(str(CRUDOS / patron)))
    return [f for f in lista if not (f.endswith(".gz") and f[:-3] in lista)]


def leer_por_anio(patron, columnas, nombre):
    partes, anio_en = [], {}
    for f in archivos(patron):
        anio_nombre = int(Path(f).name.split("_")[-1][:4]) if "oferta" in nombre else None
        if anio_nombre and not (ANIO_INI <= anio_nombre <= ANIO_FIN):
            print(f"   {Path(f).name}: fuera de 2016-2024, se ignora")
            continue
        d = pd.read_csv(f, encoding="latin-1", usecols=columnas)
        d = d[d["año"].between(ANIO_INI, ANIO_FIN)]
        if d.empty:
            print(f"   {Path(f).name}: fuera de 2016-2024, se ignora")
            continue
        for a in d["año"].unique():
            if a in anio_en:
                raise SystemExit(f"El año {a} de {nombre} viene en dos archivos: {anio_en[a]} y {Path(f).name}.\n"
                                 "Probablemente uno es copia del otro. Deja solo uno y vuelve a correr.")
            anio_en[a] = Path(f).name
        print(f"   {Path(f).name}: {len(d):,} filas")
        partes.append(d)
    return pd.concat(partes, ignore_index=True).rename(columns={"año": "anio"})


# ---- revisar que estén todos los archivos antes de empezar
NECESARIOS = {
    "00_Pob_Mitad_1950_2070.csv (o .csv.gz)": "00_Pob_Mitad_1950_2070.csv*",
    "indice_shf_precios_vivienda_datos_abiertos*.xlsx": "indice_shf*.xlsx",
    "inpc_nacional.csv": "inpc_nacional.csv",
    "banxico_SF60634_tasa_cetes91d.csv": "banxico_SF60634*",
    "banxico_SF43773_tasa_fondeo_bancario.csv": "banxico_SF43773*",
    "financiamientos_2016_1.csv ... financiamientos_2024.csv (o .csv.gz)": "financiamientos_*.csv*",
    "oferta_viv_2016.csv ... oferta_viv_2024.csv": "oferta_viv_20[12][0-9].csv*",
}
faltan = [n for n, p in NECESARIOS.items() if not archivos(p)]
if faltan:
    raise SystemExit("No encontré estos archivos en " + str(CRUDOS) + ":\n  - " + "\n  - ".join(faltan)
                     + "\nPonlos en una carpeta llamada datos_crudos junto a este script.")
print("Leyendo archivos de:", CRUDOS)


def trimestre(mes):
    return (mes - 1) // 3 + 1


# ---------------------------------------------------------------- 1. Población (CONAPO)
pob = pd.read_csv(archivos("00_Pob_Mitad_1950_2070.csv*")[0])
catalogo = (pob[["CVE_GEO", "ENTIDAD"]].drop_duplicates()
            .rename(columns={"CVE_GEO": "cve_ent", "ENTIDAD": "estado"}))
pob = (pob.groupby(["ANIO", "CVE_GEO"], as_index=False)["POBLACION"].sum()
       .rename(columns={"ANIO": "anio", "CVE_GEO": "cve_ent", "POBLACION": "poblacion"}))

# ---------------------------------------------------------------- 2. Índice SHF (estatal)
shf = pd.read_excel(archivos("indice_shf*.xlsx")[0])
shf = shf[shf["Global"].isna() & shf["Municipio"].isna() & shf["Estado"].notna()].copy()
shf["Estado"] = shf["Estado"].str.strip()
faltan = set(shf["Estado"]) - set(catalogo["estado"])
assert not faltan, f"Estados del SHF sin clave: {faltan}"
shf = shf.merge(catalogo, left_on="Estado", right_on="estado")
shf = (shf.rename(columns={"Año": "anio", "Trimestre": "trimestre", "Indice": "indice_shf"})
       [["cve_ent", "anio", "trimestre", "indice_shf"]]
       .sort_values(["cve_ent", "anio", "trimestre"]))
shf["var_anual_shf_pct"] = (shf.groupby("cve_ent")["indice_shf"].pct_change(4) * 100).round(2)

# ---------------------------------------------------------------- 3. INPC
inpc_m = pd.read_csv(archivos("inpc_nacional.csv")[0])
if archivos("inpc_2015_dof.csv"):   # INPC 2015 (DOF), para que la inflación anual de 2016 no quede vacía
    inpc_m = pd.concat([pd.read_csv(archivos("inpc_2015_dof.csv")[0]), inpc_m], ignore_index=True)
inpc_m = inpc_m.sort_values(["anio", "mes"]).reset_index(drop=True)
inpc_base = inpc_m.loc[inpc_m["anio"] == 2024, "inpc_nacional"].mean()   # pesos promedio de 2024
inpc_m["deflactor"] = inpc_base / inpc_m["inpc_nacional"]
inpc_t = (inpc_m.assign(trimestre=trimestre(inpc_m["mes"]))
          .groupby(["anio", "trimestre"], as_index=False)["inpc_nacional"].mean()
          .rename(columns={"inpc_nacional": "inpc"})
          .sort_values(["anio", "trimestre"]))
inpc_t["inflacion_anual_pct"] = (inpc_t["inpc"].pct_change(4) * 100).round(2)
inpc_t["inpc"] = inpc_t["inpc"].round(3)

# ---------------------------------------------------------------- 4. Banxico (tasas)
def tasa_trimestral(patron, nombre):
    b = pd.read_csv(archivos(patron)[0])
    f = pd.to_datetime(b["fecha"], format="%d/%m/%Y")
    b = b.assign(anio=f.dt.year, trimestre=f.dt.quarter, dato=pd.to_numeric(b["dato"], errors="coerce"))
    return b.groupby(["anio", "trimestre"], as_index=False)["dato"].mean().round(4).rename(columns={"dato": nombre})

tasas = (tasa_trimestral("banxico_SF60634*", "tasa_cetes91")
         .merge(tasa_trimestral("banxico_SF43773*", "tasa_fondeo"), on=["anio", "trimestre"], how="outer"))

# ---------------------------------------------------------------- 5. Financiamientos
print("Financiamientos:")
fin = leer_por_anio("financiamientos_*.csv*", ["año", "mes", "cve_ent", "destino", "tipo", "acciones", "monto"],
                    "financiamientos")
n_total = len(fin)
fin["cve_ent"] = pd.to_numeric(fin["cve_ent"], errors="coerce")
sin_estado = fin["cve_ent"].isna().sum()
negativos = (fin["monto"] < 0).sum()
fin = fin[fin["cve_ent"].notna() & (fin["monto"] >= 0)].copy()
fin["cve_ent"] = fin["cve_ent"].astype(int)
fin = fin.merge(inpc_m[["anio", "mes", "deflactor"]], on=["anio", "mes"], how="left")
fin["monto_real"] = fin["monto"] * fin["deflactor"]
fin["trimestre"] = trimestre(fin["mes"])

llave = ["cve_ent", "anio", "trimestre"]
fin_tot = (fin.groupby(llave, as_index=False)
           .agg(creditos=("acciones", "sum"), monto_real=("monto_real", "sum")))
ind = fin[(fin["tipo"] == 1) & fin["destino"].isin([2, 3]) & (fin["monto"] > 0) & (fin["acciones"] > 0)]
fin_ind = (ind.groupby(llave, as_index=False)
           .agg(creditos_ind_vivienda=("acciones", "sum"), _monto_ind=("monto_real", "sum")))
fin_ind["credito_promedio_real"] = (fin_ind["_monto_ind"] / fin_ind["creditos_ind_vivienda"]).round(0)
fin_q = fin_tot.merge(fin_ind.drop(columns="_monto_ind"), on=llave, how="left")
fin_q["monto_real_mdp"] = (fin_q.pop("monto_real") / 1e6).round(2)

# ---------------------------------------------------------------- 6. Oferta de vivienda
print("Oferta:")
of = leer_por_anio("oferta_viv_20[12][0-9].csv*", ["año", "mes", "cve_ent", "vivienda_valor", "viviendas"], "oferta")
of["cve_ent"] = pd.to_numeric(of["cve_ent"], errors="coerce").astype("Int64")
of = of[of["cve_ent"].notna()].copy()
of["cve_ent"] = of["cve_ent"].astype(int)
of["trimestre"] = trimestre(of["mes"])
# último mes disponible de cada trimestre (a nivel nacional, para que todos los estados usen el mismo)
ult = of.groupby(["anio", "trimestre"], as_index=False)["mes"].max()
of = of.merge(ult, on=["anio", "trimestre", "mes"])
of_q = of.groupby(llave, as_index=False)["viviendas"].sum().rename(columns={"viviendas": "oferta_viviendas"})
# ---------------------------------------------------------------- 7. Unión
base = pd.MultiIndex.from_product([catalogo["cve_ent"].sort_values(), range(ANIO_INI - 1, ANIO_FIN + 1), range(1, 5)],
                                  names=llave).to_frame(index=False)
df = (base.merge(catalogo, on="cve_ent")
      .merge(shf, on=llave, how="left")
      .merge(fin_q, on=llave, how="left")
      .merge(of_q, on=llave, how="left")
      .merge(inpc_t, on=["anio", "trimestre"], how="left")
      .merge(tasas, on=["anio", "trimestre"], how="left")
      .merge(pob, on=["anio", "cve_ent"], how="left"))

df["oferta_metodologia_2019"] = (df["anio"] >= 2019).astype(int)
# Oferta 2024T1-T3 no existe (SEDATU solo publicó diciembre 2024): se interpola en línea recta
# entre 2023T4 y 2024T4 para cada estado, y se marca con oferta_imputada = 1.
df = df.sort_values(llave)
df["oferta_imputada"] = (df["oferta_viviendas"].isna() & (df["anio"] == 2024)).astype(int)
df["oferta_viviendas"] = df.groupby("cve_ent")["oferta_viviendas"].transform(
    lambda s: s.interpolate(method="linear", limit_area="inside")).round(0)
df["creditos_por_mil"] = (df["creditos"] / df["poblacion"] * 1000).round(3)
df["oferta_por_mil"] = (df["oferta_viviendas"] / df["poblacion"] * 1000).round(3)

# rezagos (se calculan antes de recortar a 2016 para que 2016 tenga su lag del SHF)
df = df.sort_values(llave)
g = df.groupby("cve_ent")
for col in ["indice_shf", "creditos_por_mil", "credito_promedio_real", "oferta_por_mil",
            "tasa_fondeo", "inflacion_anual_pct"]:
    df[f"{col}_lag1"] = g[col].shift(1)
    df[f"{col}_lag4"] = g[col].shift(4)

df = df[df["anio"].between(ANIO_SALIDA, ANIO_FIN)].copy()
df.insert(4, "periodo", df["anio"].astype(str) + "T" + df["trimestre"].astype(str))

orden = ["cve_ent", "estado", "anio", "trimestre", "periodo",
         "indice_shf", "var_anual_shf_pct",
         "creditos", "monto_real_mdp", "creditos_ind_vivienda", "credito_promedio_real", "creditos_por_mil",
         "oferta_viviendas", "oferta_por_mil", "oferta_imputada", "oferta_metodologia_2019",
         "poblacion", "inpc", "inflacion_anual_pct", "tasa_cetes91", "tasa_fondeo"]
orden += [c for c in df.columns if c.endswith(("_lag1", "_lag4"))]
df = df[orden].reset_index(drop=True)
for c in ["creditos", "creditos_ind_vivienda", "oferta_viviendas", "poblacion"]:
    df[c] = df[c].round(0).astype("Int64")
# utf-8-sig: así Excel en Windows muestra bien los acentos (México, Querétaro, Yucatán...)
df.to_csv(SALIDA, index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- 8. Resumen
print(f"Dataset: {SALIDA}  ->  {len(df)} filas x {df.shape[1]} columnas")
print(f"Estados: {df['cve_ent'].nunique()}  |  Trimestres: {df['periodo'].nunique()}")
print(f"Financiamientos: {n_total:,} filas leídas, {sin_estado:,} sin estado y {negativos} con monto negativo excluidas")
print(f"Base de pesos: INPC promedio 2024 = {inpc_base:.3f}")
v = df.isna().sum()
print("Vacíos:", "ninguno" if v.sum() == 0 else "\n" + v[v > 0].to_string())
