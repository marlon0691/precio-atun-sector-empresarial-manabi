"""
FASE 4 (ANALYZE): Q1, Q2 y Q3.

Decisiones metodológicas clave (ver README §Metodología):
- El precio Bangkok es común a todas las empresas en un año → NO se usan efectos fijos de año
  (serían perfectamente colineales con el precio). Se usa efecto fijo de empresa y errores
  Driscoll-Kraay (robustos a correlación transversal y serial), adecuados con N grande y T=15.
- Los ratios por empresa se acotan a [-1, 1] y se restringen a empresas con ingresos ≥ USD 100 mil
  (actividad material); los resultados agregados se ponderan por ingresos.
- 2014: el formulario no reporta 'total costos' para casi ninguna empresa → margen bruto 2014 excluido.
- Series mensuales: errores HAC (Newey-West, 12 rezagos) por la fuerte autocorrelación del precio y del ONI.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from linearmodels.panel import PanelOLS
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.tsa.ar_model import AutoReg
from statsmodels.tsa.stattools import adfuller, ccf, grangercausalitytests

from .data_loader import TAB, PROC, agregados_sector, dataset_mensual

warnings.filterwarnings("ignore")

TIPOS = ["Manufacturera", "Pesquera"]
METRICAS = {"margen_bruto": "Margen bruto", "margen_operativo": "Margen operativo (antes de part. e IR)",
            "margen_neto": "Margen neto", "roa": "ROA", "roe": "ROE"}
ING_MIN = 100_000
HAC = {"cov_type": "HAC", "cov_kwds": {"maxlags": 12}}


def _save(df: pd.DataFrame, name: str) -> pd.DataFrame:
    df.to_csv(TAB / name, index=False, encoding="utf-8")
    return df


def panel_analitico(df: pd.DataFrame | None = None) -> pd.DataFrame:
    if df is None:
        df = pd.read_parquet(PROC / "dataset_maestro_manabi.parquet")
    d = df[df.anio.between(2011, 2025) & (df.ingresos >= ING_MIN)].copy()
    for m in METRICAS:
        d[m + "_c"] = d[m].clip(-1, 1)
    d.loc[d.anio == 2014, "margen_bruto_c"] = np.nan
    d["dp10"] = d["precio_var_yoy_pct"] / 10  # efecto por cada +10% de variación anual del precio
    return d


def agregados(df: pd.DataFrame | None = None) -> pd.DataFrame:
    if df is None:
        df = pd.read_parquet(PROC / "dataset_maestro_manabi.parquet")
    a = agregados_sector(df)
    a.loc[a.anio == 2014, "margen_bruto_agr"] = np.nan
    a = a[a.anio.between(2011, 2025)].copy()
    a["p100"] = a["precio_prom"] / 100
    a["dp10"] = a["precio_var_yoy_pct"] / 10
    a = a.sort_values(["tipo_empresa", "anio"])
    a["crec_ventas_pct"] = a.groupby("tipo_empresa")["ingresos"].transform(lambda s: np.log(s).diff() * 100)
    return _save(a, "agregados_sector_tipo_anio.csv")


# ======================================================================================
# Q1 — precio Bangkok ↔ desempeño financiero
# ======================================================================================
def q1(d: pd.DataFrame, a: pd.DataFrame) -> dict:
    # A) Correlaciones (nivel empresa y nivel agregado)
    filas = []
    for tipo in TIPOS:
        for m in METRICAS:
            s = d[d.tipo_empresa == tipo].dropna(subset=[m + "_c", "precio_prom"])
            rp, pp = stats.pearsonr(s.precio_prom, s[m + "_c"])
            rs, ps = stats.spearmanr(s.precio_prom, s[m + "_c"])
            col = f"{m}_agr"
            sa = a[a.tipo_empresa == tipo].dropna(subset=[col])
            ra, pa = stats.pearsonr(sa.precio_prom, sa[col])
            filas.append({"tipo": tipo, "metrica": m, "n_empresa_anio": len(s), "r_pearson": rp, "p_pearson": pp,
                          "r_spearman": rs, "p_spearman": ps, "n_anios": len(sa), "r_agregado": ra, "p_agregado": pa,
                          "direccion": "↑ positiva" if ra > 0 else "↓ negativa"})
    corr = _save(pd.DataFrame(filas).round(4), "q1_correlaciones_precio_desempeno.csv")

    # B) Panel con efectos fijos de empresa (Driscoll-Kraay)
    filas, textos = [], []
    for tipo in TIPOS:
        for m in METRICAS:
            s = d[d.tipo_empresa == tipo].dropna(subset=[m + "_c", "precio_prom_100", "dp10"]).set_index(["ruc", "anio"])
            res = PanelOLS.from_formula(f"{m}_c ~ precio_prom_100 + dp10 + EntityEffects", s).fit(cov_type="kernel")
            ci = res.conf_int()
            for v in ["precio_prom_100", "dp10"]:
                filas.append({"tipo": tipo, "metrica": m, "variable": v, "coef_pp": res.params[v] * 100,
                              "ic95_inf_pp": ci.loc[v, "lower"] * 100, "ic95_sup_pp": ci.loc[v, "upper"] * 100,
                              "p_value": res.pvalues[v], "n_obs": int(res.nobs), "n_empresas": int(s.index.get_level_values(0).nunique()),
                              "r2_within": res.rsquared_within})
            textos.append(f"\n\n===== {tipo} — {m} =====\n{res.summary}")
    panel = _save(pd.DataFrame(filas).round(4), "q1_panel_efectos_fijos.csv")
    (TAB / "q1_panel_efectos_fijos_resumen.txt").write_text("".join(textos), encoding="utf-8")

    # C) Series agregadas (empresa representativa ponderada por ingresos), HAC
    filas = []
    modelos_agr = {}
    for tipo in TIPOS:
        sa = a[a.tipo_empresa == tipo]
        for m in METRICAS:
            col = f"{m}_agr"
            s = sa.dropna(subset=[col, "dp10"])
            r = smf.ols(f"{col} ~ p100 + dp10", s).fit(cov_type="HAC", cov_kwds={"maxlags": 1})
            r1 = smf.ols(f"{col} ~ p100", sa.dropna(subset=[col])).fit(cov_type="HAC", cov_kwds={"maxlags": 1})
            modelos_agr[(tipo, m)] = r1
            ci = r.conf_int()
            for v in ["p100", "dp10"]:
                filas.append({"tipo": tipo, "metrica": m, "modelo": "nivel+variación", "variable": v,
                              "coef_pp": r.params[v] * 100, "ic95_inf_pp": ci.loc[v, 0] * 100, "ic95_sup_pp": ci.loc[v, 1] * 100,
                              "p_value": r.pvalues[v], "r2": r.rsquared, "n_anios": int(r.nobs)})
            ci1 = r1.conf_int()
            filas.append({"tipo": tipo, "metrica": m, "modelo": "solo nivel", "variable": "p100",
                          "coef_pp": r1.params["p100"] * 100, "ic95_inf_pp": ci1.loc["p100", 0] * 100,
                          "ic95_sup_pp": ci1.loc["p100", 1] * 100, "p_value": r1.pvalues["p100"], "r2": r1.rsquared,
                          "n_anios": int(r1.nobs)})
        # crecimiento de ventas ↔ variación de precio
        s = sa.dropna(subset=["crec_ventas_pct", "dp10"])
        r = smf.ols("crec_ventas_pct ~ dp10", s).fit(cov_type="HAC", cov_kwds={"maxlags": 1})
        ci = r.conf_int()
        filas.append({"tipo": tipo, "metrica": "crec_ventas_pct", "modelo": "variación", "variable": "dp10",
                      "coef_pp": r.params["dp10"], "ic95_inf_pp": ci.loc["dp10", 0], "ic95_sup_pp": ci.loc["dp10", 1],
                      "p_value": r.pvalues["dp10"], "r2": r.rsquared, "n_anios": int(r.nobs)})
    agr = _save(pd.DataFrame(filas).round(4), "q1_regresiones_agregadas.csv")

    # D) Test formal de asimetría (interacción tipo × precio) en panel
    s = d.dropna(subset=["margen_operativo_c", "precio_prom_100"]).copy()
    s["pesq"] = (s.tipo_empresa == "Pesquera").astype(int)
    s["p_x_pesq"] = s.precio_prom_100 * s.pesq
    s = s.set_index(["ruc", "anio"])
    r = PanelOLS.from_formula("margen_operativo_c ~ precio_prom_100 + p_x_pesq + EntityEffects", s).fit(cov_type="kernel")
    asim = {"coef_precio_manuf_pp": r.params["precio_prom_100"] * 100,
            "coef_diferencial_pesquera_pp": r.params["p_x_pesq"] * 100, "p_diferencial": r.pvalues["p_x_pesq"]}

    return {"corr": corr, "panel": panel, "agr": agr, "asimetria": asim, "modelos_agr": modelos_agr}


# ======================================================================================
# Q2 — ONI ↔ precio Bangkok
# ======================================================================================
def q2(m: pd.DataFrame | None = None, nlags: int = 18) -> dict:
    if m is None:
        m = dataset_mensual()
    out = {"n_meses": len(m), "periodo": f"{m.fecha.min():%Y-%m} a {m.fecha.max():%Y-%m}"}

    # Estacionariedad
    out["adf"] = {c: float(adfuller(m[c].dropna(), autolag="AIC")[1]) for c in ["precio_usd_ton", "oni_anom", "dlog_precio"]}

    # A) CCF bruta: corr(precio_{t+k}, ONI_t)  → ONI adelanta al precio k meses
    banda = 1.96 / np.sqrt(len(m))
    raw = ccf(m.precio_usd_ton, m.oni_anom, nlags=nlags + 1, adjusted=False)[: nlags + 1]
    # Pre-blanqueo (Box-Jenkins): filtro AR(3) del ONI aplicado a ambas series
    ar = AutoReg(m.oni_anom.values, lags=3).fit()
    p = ar.params
    x = m.precio_usd_ton.values
    fx = x[3:] - p[0] - sum(p[i] * x[3 - i: len(x) - i] for i in range(1, 4))
    pw = ccf(fx, ar.resid, nlags=nlags + 1, adjusted=False)[: nlags + 1]
    ccf_df = pd.DataFrame({"lag_meses": range(nlags + 1), "ccf_bruta": raw, "ccf_preblanqueada": pw,
                           "banda_95": banda, "sig_bruta": np.abs(raw) > banda,
                           "sig_preblanqueada": np.abs(pw) > 1.96 / np.sqrt(len(fx))})
    _save(ccf_df.round(4), "q2_ccf_oni_precio.csv")
    lag_opt = int(ccf_df.loc[1:, "ccf_bruta"].abs().idxmax())
    out.update(lag_optimo=lag_opt, ccf_lag_optimo=float(raw[lag_opt]), ccf_df=ccf_df)

    # B) Granger
    gr = []
    for y, x_, lab in [("precio_usd_ton", "oni_anom", "ONI → precio (niveles)"),
                       ("dlog_precio", "oni_anom", "ONI → Δlog precio"),
                       ("oni_anom", "precio_usd_ton", "precio → ONI (control)")]:
        res = grangercausalitytests(m[[y, x_]].dropna(), maxlag=12)
        for k, v in res.items():
            gr.append({"hipotesis": lab, "lag": int(k), "F": v[0]["ssr_ftest"][0], "p_value": v[0]["ssr_ftest"][1]})
    gr = _save(pd.DataFrame(gr).round(4), "q2_granger.csv")
    out["granger_min_p"] = float(gr[gr.hipotesis.str.startswith("ONI → precio")].p_value.min())
    out["granger"] = gr

    # C) Precio por episodio (contemporáneo y con rezago óptimo)
    resumen, tests = [], []
    for k in [0, lag_opt]:
        mm = m.copy()
        mm["ep"] = mm.episodio_enso.shift(k)
        mm = mm.dropna(subset=["ep"])
        g = mm.groupby("ep").precio_usd_ton.agg(["mean", "median", "std", "count"]).reset_index()
        g["rezago_meses"] = k
        resumen.append(g)
        grupos = [mm[mm.ep == e].precio_usd_ton for e in ["El Niño", "La Niña", "Neutro"]]
        f, pa = stats.f_oneway(*grupos)
        h, pk = stats.kruskal(*grupos)
        t, pt = stats.ttest_ind(grupos[0], grupos[1], equal_var=False)
        rh = smf.ols('precio_usd_ton ~ C(ep, Treatment("Neutro"))', mm).fit(**HAC)
        mm["nino"] = (mm.ep == "El Niño").astype(int)
        rn = smf.ols("precio_usd_ton ~ nino", mm[mm.ep != "Neutro"]).fit(**HAC)
        tests.append({"rezago_meses": k, "anova_F": f, "anova_p": pa, "kruskal_H": h, "kruskal_p": pk,
                      "welch_t_nino_vs_nina": t, "welch_p": pt,
                      "dif_nino_menos_nina_usd": grupos[0].mean() - grupos[1].mean(),
                      "dif_HAC_p": rn.pvalues["nino"],
                      "dif_HAC_ic95": list(rn.conf_int().loc["nino"].round(0)),
                      "nino_vs_neutro_HAC_usd": rh.params.iloc[1], "nino_vs_neutro_HAC_p": rh.pvalues.iloc[1]})
        if k == lag_opt:
            tk = pairwise_tukeyhsd(mm.precio_usd_ton, mm.ep)
            (TAB / "q2_tukey_hsd.txt").write_text(str(tk.summary()), encoding="utf-8")
    _save(pd.concat(resumen).round(1), "q2_precio_por_episodio_enso.csv")
    tests = _save(pd.DataFrame(tests).round(4), "q2_tests_episodio_enso.csv")
    out["tests_enso"] = tests

    # D) Lineal vs polinómico, por rezago (HAC)
    fil = []
    mods = {}
    for k in range(0, nlags + 1):
        mm = m.copy()
        mm["oni_lag"] = mm.oni_anom.shift(k)
        mm = mm.dropna(subset=["oni_lag"])
        l = smf.ols("precio_usd_ton ~ oni_lag", mm).fit(**HAC)
        q = smf.ols("precio_usd_ton ~ oni_lag + I(oni_lag**2)", mm).fit(**HAC)
        mods[k] = (l, q)
        fil.append({"lag": k, "b_lineal_usd_por_1C": l.params["oni_lag"], "p_lineal": l.pvalues["oni_lag"], "r2_lineal": l.rsquared,
                    "b1_poly": q.params["oni_lag"], "b2_poly": q.params["I(oni_lag ** 2)"], "p_b2": q.pvalues["I(oni_lag ** 2)"],
                    "r2_poly": q.rsquared, "aic_lineal": l.aic, "aic_poly": q.aic,
                    "oni_precio_minimo": -q.params["oni_lag"] / (2 * q.params["I(oni_lag ** 2)"])})
    poly = _save(pd.DataFrame(fil).round(4), "q2_lineal_vs_polinomico.csv")
    out.update(poly=poly, mod_lin=mods[lag_opt][0], mod_poly=mods[lag_opt][1])
    best_poly = int(poly.loc[poly.r2_poly.idxmax(), "lag"])
    out["lag_mejor_poly"] = best_poly
    out["mod_poly_best"] = mods[best_poly][1]

    # E) Pronóstico condicional al ONI observado (lag óptimo), con intervalo de predicción
    ult = m.dropna(subset=["oni_anom"]).iloc[-1]
    lq = mods[lag_opt][1]
    pr = lq.get_prediction(pd.DataFrame({"oni_lag": [ult.oni_anom]})).summary_frame(alpha=0.05)
    out["pronostico"] = {"fecha_oni": f"{ult.fecha:%Y-%m}", "oni_actual": float(ult.oni_anom),
                         "precio_ultimo_con_oni": float(m.precio_usd_ton.iloc[-1]),
                         "horizonte_meses": lag_opt, "precio_esperado": float(pr["mean"].iloc[0]),
                         "pi95_inf": float(pr["obs_ci_lower"].iloc[0]), "pi95_sup": float(pr["obs_ci_upper"].iloc[0])}
    return out


# ======================================================================================
# Q3 — pérdidas potenciales, break-even, VaR, escenarios
# ======================================================================================
ESCENARIOS = {
    "Mínimo histórico (oct-2019)": 900,
    "Piso El Niño 2015": 1100,
    "Precio promedio 2024": 1438,
    "Precio promedio 2025": 1573,
    "Moderado alto (prom. 2013)": 1800,
    "Severo (prom. 2012)": 2100,
    "Extremo (pico oct-2017 / sep-2026)": 2300,
    "Estrés extremo": 2500,
}


def q3(d: pd.DataFrame, a: pd.DataFrame, res_q1: dict) -> dict:
    out = {}
    base_anio = int(a.anio.max())
    p_base = float(a[a.anio == base_anio].precio_prom.iloc[0])

    # A) Break-even por tipo: precio que lleva el margen operativo agregado a 0
    be = []
    for tipo in TIPOS:
        r = res_q1["modelos_agr"][(tipo, "margen_operativo")]
        b0, b1 = r.params["Intercept"], r.params["p100"]
        cov = r.cov_params().loc[["Intercept", "p100"], ["Intercept", "p100"]].values
        pbe = -b0 / b1 * 100
        # IC por método delta
        g = np.array([-1 / b1, b0 / b1 ** 2]) * 100
        se = float(np.sqrt(g @ cov @ g))
        sa = a[a.tipo_empresa == tipo]
        be.append({"tipo": tipo, "precio_breakeven_usd_t": pbe, "ic95_inf": pbe - 1.96 * se, "ic95_sup": pbe + 1.96 * se,
                   "efecto_100usd_pp": b1 * 100, "efecto_ic95_inf": r.conf_int().loc["p100", 0] * 100,
                   "efecto_ic95_sup": r.conf_int().loc["p100", 1] * 100, "r2": r.rsquared,
                   "precio_min_observado": float(sa.precio_prom.min()), "precio_max_observado": float(sa.precio_prom.max()),
                   "dentro_rango_observado": bool(sa.precio_prom.min() <= pbe <= sa.precio_prom.max()),
                   "anios_con_margen_operativo_negativo": ", ".join(str(int(x)) for x in sa[sa.margen_operativo_agr < 0].anio)})
    be = _save(pd.DataFrame(be).round(4), "q3_breakeven.csv")
    out["breakeven"] = be

    # B) VaR 95% (percentil 5) — firma-año y agregado
    var = []
    for tipo in TIPOS:
        for m in ["margen_bruto", "margen_operativo", "margen_neto"]:
            s = d[d.tipo_empresa == tipo][m + "_c"].dropna()
            sa = a[a.tipo_empresa == tipo][m + "_agr"].dropna()
            var.append({"tipo": tipo, "metrica": m, "media_empresa": s.mean(), "mediana_empresa": s.median(),
                        "VaR95_empresa": np.percentile(s, 5), "CVaR95_empresa": s[s <= np.percentile(s, 5)].mean(),
                        "media_agregado": sa.mean(), "min_agregado": sa.min(),
                        "VaR95_agregado": np.percentile(sa, 5), "n_empresa_anio": len(s), "n_anios": len(sa)})
    var = _save(pd.DataFrame(var).round(4), "q3_var95.csv")
    out["var"] = var

    # C) % de empresas en pérdida operativa por año
    perd = d.groupby(["anio", "tipo_empresa"]).agg(n=("ruc", "nunique"), pct_perdida_operativa=("perdida_operativa", "mean"),
                                                   pct_perdida_neta=("perdida_neta", "mean")).reset_index()
    cob = d.groupby(["anio", "tipo_empresa"])["utilidad_antes_part_ir"].apply(lambda x: x.notna().mean()).values
    perd.loc[cob < 0.5, "pct_perdida_operativa"] = np.nan  # 2014: cuenta no reportada
    perd = perd.merge(a[["anio", "precio_prom", "oni_prom"]].drop_duplicates(), on="anio")
    _save(perd.round(4), "q3_pct_empresas_perdida.csv")
    out["perdidas_anio"] = perd

    # D) Escenarios de estrés (empresa representativa + distribución por empresa)
    panel = res_q1["panel"]
    filas = []
    for tipo in TIPOS:
        r = res_q1["modelos_agr"][(tipo, "margen_operativo")]
        ing = float(a[(a.tipo_empresa == tipo) & (a.anio == base_anio)].ingresos.iloc[0])
        mo_base = float(a[(a.tipo_empresa == tipo) & (a.anio == base_anio)].margen_operativo_agr.iloc[0])
        beta_fe = float(panel[(panel.tipo == tipo) & (panel.metrica == "margen_operativo") & (panel.variable == "precio_prom_100")].coef_pp.iloc[0]) / 100
        beta_agr = r.params["p100"]
        firms = d[(d.tipo_empresa == tipo) & (d.anio == base_anio)].dropna(subset=["margen_operativo_c"])
        for nom, pr_ in ESCENARIOS.items():
            pred = r.get_prediction(pd.DataFrame({"p100": [pr_ / 100]})).summary_frame(alpha=0.05)
            delta = beta_agr * (pr_ - p_base) / 100
            sim = firms.margen_operativo_c + delta
            filas.append({"tipo": tipo, "escenario": nom, "precio_usd_t": pr_,
                          "margen_op_esperado_pct": pred["mean"].iloc[0] * 100,
                          "pi95_inf_pct": pred["obs_ci_lower"].iloc[0] * 100, "pi95_sup_pct": pred["obs_ci_upper"].iloc[0] * 100,
                          "cambio_vs_2025_pp": delta * 100,
                          "impacto_utilidad_operativa_musd": delta * ing / 1e6,
                          "pct_empresas_en_perdida": (sim < 0).mean() * 100,
                          "pct_empresas_perdida_2025": (firms.margen_operativo_c < 0).mean() * 100})
    esc = _save(pd.DataFrame(filas).round(2), "q3_escenarios_estres.csv")
    out["escenarios"] = esc

    # E) Shock de velocidad de precio para manufactureras (margen bruto ~ Δ% precio)
    pm = panel[(panel.tipo == "Manufacturera") & (panel.metrica == "margen_bruto") & (panel.variable == "dp10")].iloc[0]
    ing_m = float(a[(a.tipo_empresa == "Manufacturera") & (a.anio == base_anio)].ingresos.iloc[0])
    out["shock_velocidad_manuf"] = {"coef_pp_por_10pct": float(pm.coef_pp), "ic95": [float(pm.ic95_inf_pp), float(pm.ic95_sup_pp)],
                                    "p_value": float(pm.p_value),
                                    "impacto_musd_shock_30pct": float(pm.coef_pp) * 3 / 100 * ing_m / 1e6}
    out["p_base"] = p_base
    out["base_anio"] = base_anio
    return out


# ======================================================================================
def correr_todo() -> dict:
    d = panel_analitico()
    a = agregados()
    r1 = q1(d, a)
    r2 = q2()
    r3 = q3(d, a, r1)
    df_all = pd.read_parquet(PROC / "dataset_maestro_manabi.parquet")

    pm = r1["panel"]
    agr = r1["agr"]

    def g(tbl, **kw):
        s = tbl
        for k, v in kw.items():
            s = s[s[k] == v]
        return s.iloc[0]

    t0 = r2["tests_enso"].iloc[0]
    tl = r2["tests_enso"].iloc[-1]
    be = r3["breakeven"].set_index("tipo")
    hall = {
        "cobertura": {"empresas_universo": int(df_all.ruc.nunique()), "obs_empresa_anio": int(len(df_all)),
                      "empresas_analisis_econometrico": int(d.ruc.nunique()), "obs_analisis": int(len(d)),
                      "manufactureras": int(d[d.tipo_empresa == "Manufacturera"].ruc.nunique()),
                      "pesqueras": int(d[d.tipo_empresa == "Pesquera"].ruc.nunique()),
                      "periodo_financiero": "2011–2025 (precio desde 2011)", "periodo_mensual": r2["periodo"],
                      "n_meses": r2["n_meses"]},
        "q1": {t: {"margen_op_agr_por_100usd_pp": float(g(agr, tipo=t, metrica="margen_operativo", modelo="solo nivel").coef_pp),
                   "ic95": [float(g(agr, tipo=t, metrica="margen_operativo", modelo="solo nivel").ic95_inf_pp),
                            float(g(agr, tipo=t, metrica="margen_operativo", modelo="solo nivel").ic95_sup_pp)],
                   "p": float(g(agr, tipo=t, metrica="margen_operativo", modelo="solo nivel").p_value),
                   "r2": float(g(agr, tipo=t, metrica="margen_operativo", modelo="solo nivel").r2),
                   "margen_bruto_fe_por_100usd_pp": float(g(pm, tipo=t, metrica="margen_bruto", variable="precio_prom_100").coef_pp),
                   "margen_bruto_fe_ic95": [float(g(pm, tipo=t, metrica="margen_bruto", variable="precio_prom_100").ic95_inf_pp),
                                            float(g(pm, tipo=t, metrica="margen_bruto", variable="precio_prom_100").ic95_sup_pp)],
                   "margen_bruto_fe_p": float(g(pm, tipo=t, metrica="margen_bruto", variable="precio_prom_100").p_value),
                   "margen_bruto_fe_por_10pct_var_pp": float(g(pm, tipo=t, metrica="margen_bruto", variable="dp10").coef_pp),
                   "margen_bruto_fe_var_p": float(g(pm, tipo=t, metrica="margen_bruto", variable="dp10").p_value),
                   "ventas_por_10pct_var_precio_pct": float(g(agr, tipo=t, metrica="crec_ventas_pct").coef_pp),
                   "ventas_p": float(g(agr, tipo=t, metrica="crec_ventas_pct").p_value)} for t in TIPOS},
        "q1_asimetria": r1["asimetria"],
        "q2": {"lag_optimo_meses": r2["lag_optimo"], "ccf_lag_optimo": r2["ccf_lag_optimo"],
               "granger_min_p": r2["granger_min_p"], "adf_p": r2["adf"],
               "contemporaneo": {"precio_nino": None, "dif_nino_nina_usd": float(t0.dif_nino_menos_nina_usd),
                                 "welch_p": float(t0.welch_p), "hac_p": float(t0.dif_HAC_p), "anova_p": float(t0.anova_p),
                                 "kruskal_p": float(t0.kruskal_p)},
               "rezagado": {"rezago": int(tl.rezago_meses), "dif_nino_nina_usd": float(tl.dif_nino_menos_nina_usd),
                            "welch_p": float(tl.welch_p), "hac_p": float(tl.dif_HAC_p), "hac_ic95": tl.dif_HAC_ic95,
                            "anova_p": float(tl.anova_p)},
               "r2_lineal_lag_opt": float(r2["mod_lin"].rsquared), "r2_poly_lag_opt": float(r2["mod_poly"].rsquared),
               "lag_mejor_poly": r2["lag_mejor_poly"], "r2_mejor_poly": float(r2["mod_poly_best"].rsquared),
               "pronostico": r2["pronostico"]},
        "q3": {"breakeven": {t: {k: (float(v) if isinstance(v, (int, float, np.floating)) else v) for k, v in be.loc[t].items()} for t in TIPOS},
               "shock_velocidad_manuf": r3["shock_velocidad_manuf"], "precio_base": r3["p_base"], "anio_base": r3["base_anio"]},
    }
    with open(TAB / "hallazgos_clave.json", "w", encoding="utf-8") as f:
        json.dump(hall, f, ensure_ascii=False, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    return {"d": d, "a": a, "q1": r1, "q2": r2, "q3": r3, "hallazgos": hall}


if __name__ == "__main__":
    r = correr_todo()
    print(json.dumps(r["hallazgos"], ensure_ascii=False, indent=2, default=str))
