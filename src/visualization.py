"""
FASE 5 (SHARE): figuras para gerentes atuneros (PNG 300 dpi + SVG).

Reglas de diseño: máximo 3 mensajes por figura, título = implicación práctica, sin fórmulas,
un solo eje Y por panel (nada de doble eje: dos series de distinta escala → dos paneles).
Paleta: Manufacturera = azul, Pesquera = naranja (paleta categórica validada para daltonismo);
ENSO = rojo (El Niño) / azul (La Niña) / gris (Neutro), par divergente cálido-frío.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .data_loader import ROOT, cargar_oni, cargar_precio

FIG = ROOT / "outputs" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

C = {"Manufacturera": "#2a78d6", "Pesquera": "#eb6834", "El Niño": "#e34948", "La Niña": "#2a78d6",
     "Neutro": "#a3a29c", "precio": "#2b2b2b", "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#8a8984",
     "grid": "#e6e5e1", "surface": "#fcfcfb", "breakeven": "#e34948"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "figure.dpi": 110, "savefig.dpi": 300, "axes.titlesize": 12,
    "axes.titleweight": "bold", "axes.labelsize": 10, "axes.edgecolor": C["grid"], "axes.linewidth": 0.8,
    "axes.labelcolor": C["ink2"], "xtick.color": C["ink2"], "ytick.color": C["ink2"], "axes.grid": True,
    "grid.color": C["grid"], "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": C["surface"], "axes.facecolor": C["surface"], "legend.frameon": False,
    "text.color": C["ink"],
})
def es(x, dec=0):
    """Formato numérico español: miles con punto, decimales con coma."""
    t = f"{x:,.{dec}f}"
    return t.replace(",", "X").replace(".", ",").replace("X", ".")


FUENTE = "Fuentes: SUPERCIAS (2026), Thai Union IR (skipjack Bangkok), NOAA CPC (ONI). Elaboración propia."


def _save(fig, name):
    fig.text(0.01, 0.005, FUENTE, fontsize=7, color=C["muted"])
    fig.savefig(FIG / f"{name}.png", bbox_inches="tight", facecolor=C["surface"])
    fig.savefig(FIG / f"{name}.svg", bbox_inches="tight", facecolor=C["surface"])
    plt.close(fig)


def _bandas_enso(ax, oni: pd.DataFrame, alpha=0.13):
    """Sombrea meses El Niño / La Niña."""
    for _, r in oni.iterrows():
        if r.episodio_enso in ("El Niño", "La Niña"):
            ax.axvspan(r.fecha - pd.Timedelta(days=15), r.fecha + pd.Timedelta(days=15),
                       color=C[r.episodio_enso], alpha=alpha, lw=0)


# --------------------------------------------------------------------------------------
def fig1_precio_enso(res):
    p, o = cargar_precio(), cargar_oni()
    o = o[o.fecha >= p.fecha.min()]
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(11, 6.2), sharex=True, gridspec_kw={"height_ratios": [3, 1.3]})
    _bandas_enso(ax, o)
    ax.plot(p.fecha, p.precio_usd_ton, color=C["precio"], lw=2)
    ax.set_ylabel("USD por tonelada")
    ax.set_title("El precio del atún oscila entre USD 900 y 2.300/t — y históricamente BAJA durante El Niño",
                 loc="left")
    for f, lab in [("2015-03-01", "El Niño 2015-16:\nmínimos ~USD 1.000"), ("2019-10-01", "Mín. histórico\nUSD 900"),
                   ("2026-09-01", f"Sep-2026\nUSD {p.precio_usd_ton.iloc[-1]:,.0f}")]:
        r = p[p.fecha == f].iloc[0]
        ax.annotate(lab, (r.fecha, r.precio_usd_ton), xytext=(0, -38) if ("Mín" in lab or "El Niño" in lab) else (-45, 0),
                    textcoords="offset points", ha="center", fontsize=8, color=C["ink2"],
                    arrowprops=dict(arrowstyle="-", color=C["muted"], lw=0.6))
    ax.set_ylim(700, 2500)
    ax2.bar(o.fecha, o.oni_anom, width=25, color=[C[e] for e in o.episodio_enso])
    ax2.axhline(0.5, color=C["El Niño"], lw=0.6)
    ax2.axhline(-0.5, color=C["La Niña"], lw=0.6)
    ax2.set_ylabel("ONI (°C)")
    ax2.text(o.fecha.iloc[-1], 2.4, "ONI +2,16\n(El Niño fuerte)", fontsize=8, ha="right", color=C["El Niño"], va="top")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=C["El Niño"], alpha=0.35, label="Meses El Niño (ONI ≥ +0,5)"),
                       Patch(color=C["La Niña"], alpha=0.35, label="Meses La Niña (ONI ≤ −0,5)")],
              loc="lower left", fontsize=8, ncol=2)
    fig.tight_layout()
    _save(fig, "fig1_precio_bangkok_enso")


def fig2_precio_vs_margen(res):
    a = res["a"]
    fig, axes = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True, gridspec_kw={"height_ratios": [1, 1.4]})
    pa = a.drop_duplicates("anio")
    axes[0].plot(pa.anio, pa.precio_prom, "-o", color=C["precio"], lw=2, ms=5)
    axes[0].set_ylabel("Precio prom. USD/t")
    axes[0].set_title("Cuando el precio sube, el margen operativo SUBE en ambos tipos de empresa — mucho más en los barcos",
                      loc="left")
    for t in ["Manufacturera", "Pesquera"]:
        s = a[a.tipo_empresa == t]
        axes[1].plot(s.anio, s.margen_operativo_agr * 100, "-o", color=C[t], lw=2, ms=5, label=t)
        axes[1].annotate(t, (s.anio.iloc[-1], s.margen_operativo_agr.iloc[-1] * 100), xytext=(6, 0),
                         textcoords="offset points", color=C["ink2"], fontsize=9, va="center")
    axes[1].axhline(0, color=C["breakeven"], lw=1)
    axes[1].set_ylabel("Margen operativo agregado (%)")
    axes[1].legend(loc="lower left", fontsize=8)
    axes[1].set_xticks(range(2011, 2026, 2))
    axes[1].annotate("2015: precio USD 1.170 →\nbarcos −4,4%", (2015, -4.4), xytext=(2016.2, -3.6), fontsize=8,
                     color=C["ink2"], arrowprops=dict(arrowstyle="-", color=C["muted"], lw=0.6))
    fig.tight_layout()
    _save(fig, "fig2_precio_vs_margen_operativo")


def fig3_scatter_tipos(res):
    a = res["a"]
    be = res["q3"]["breakeven"].set_index("tipo")
    fig, ax = plt.subplots(figsize=(9.5, 6))
    xs = np.linspace(1100, 2200, 50)
    for t in ["Manufacturera", "Pesquera"]:
        s = a[a.tipo_empresa == t]
        ax.scatter(s.precio_prom, s.margen_operativo_agr * 100, s=60, color=C[t], edgecolor=C["surface"], lw=1.5, label=t, zorder=3)
        mod = res["q1"]["modelos_agr"][(t, "margen_operativo")]
        ax.plot(xs, mod.predict(pd.DataFrame({"p100": xs / 100})) * 100, color=C[t], lw=1.6)
        for _, r in s[s.anio.isin([2012, 2015, 2019])].iterrows():
            ax.annotate(str(int(r.anio)), (r.precio_prom, r.margen_operativo_agr * 100), xytext=(5, 4),
                        textcoords="offset points", fontsize=8, color=C["ink2"])
    ax.axhline(0, color=C["breakeven"], lw=1)
    pbe = be.loc["Pesquera", "precio_breakeven_usd_t"]
    ax.axvline(pbe, color=C["Pesquera"], lw=0.8, ls=(0, (1, 0)), alpha=0.6)
    ax.text(pbe + 12, -3.8, f"Punto de equilibrio\nflota ≈ USD {pbe:,.0f}/t".replace(",", "."), fontsize=9, color=C["ink"])
    ax.set_xlabel("Precio promedio anual Bangkok (USD/t)")
    ax.set_ylabel("Margen operativo agregado (%)")
    b_m, b_p = (res["hallazgos"]["q1"][t]["margen_op_agr_por_100usd_pp"] for t in ["Manufacturera", "Pesquera"])
    ax.set_title(f"Precio bajo castiga a los barcos: +USD 100/t = +{b_p:.1f} pp de margen (plantas: +{b_m:.1f} pp)".replace(".", ","),
                 loc="left")
    ax.legend(loc="upper left", fontsize=9)
    fig.tight_layout()
    _save(fig, "fig3_scatter_precio_margen_por_tipo")


def fig4_ccf(res):
    c = res["q2"]["ccf_df"]
    lag = res["q2"]["lag_optimo"]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(c.lag_meses - 0.2, c.ccf_bruta, width=0.38, color=C["La Niña"], label="Correlación directa")
    ax.bar(c.lag_meses + 0.2, c.ccf_preblanqueada, width=0.38, color=C["Neutro"], label="Correlación pre-blanqueada (sin inercia)")
    b = c.banda_95.iloc[0]
    ax.axhspan(-b, b, color=C["grid"], alpha=0.6, lw=0)
    ax.axhline(0, color=C["ink2"], lw=0.6)
    ax.annotate(f"Máximo: {lag} meses (r = {c.ccf_bruta[lag]:+.2f})".replace(".", ","), (lag - 0.2, c.ccf_bruta[lag]),
                xytext=(lag + 2, -0.47), fontsize=9, arrowprops=dict(arrowstyle="-", color=C["muted"], lw=0.6))
    ax.set_xlabel("Meses que el ONI se adelanta al precio")
    ax.set_ylabel("Correlación")
    ax.set_xticks(range(0, len(c)))
    ax.set_ylim(-0.5, 0.25)
    ax.set_title(f"El Niño anticipa precios MÁS BAJOS ~{lag} meses después — señal de régimen, no pronóstico mes a mes",
                 loc="left")
    ax.legend(loc="lower right", fontsize=8)
    ax.text(18, 0.17, "Franja gris = no significativo (95%)", ha="right", fontsize=8, color=C["muted"])
    fig.tight_layout()
    _save(fig, "fig4_ccf_oni_precio")


def fig5_box_enso(res):
    from .data_loader import dataset_mensual
    m = dataset_mensual()
    lag = res["q2"]["lag_optimo"]
    m["ep"] = m.episodio_enso.shift(lag)
    m = m.dropna(subset=["ep"])
    orden = ["La Niña", "Neutro", "El Niño"]
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    data = [m[m.ep == e].precio_usd_ton for e in orden]
    bp = ax.boxplot(data, widths=0.45, patch_artist=True, showfliers=True,
                    medianprops=dict(color=C["ink"], lw=1.5), whiskerprops=dict(color=C["ink2"]),
                    capprops=dict(color=C["ink2"]), flierprops=dict(marker="o", ms=4, mfc=C["muted"], mec="none"))
    for patch, e in zip(bp["boxes"], orden):
        patch.set_facecolor(C[e]); patch.set_alpha(0.35); patch.set_edgecolor(C[e])
    for i, d in enumerate(data, 1):
        ax.text(i, d.max() + 50, f"Prom. USD {d.mean():,.0f}\n(n={len(d)} meses)".replace(",", "."), ha="center", fontsize=8, color=C["ink2"])
    ax.set_xticks([1, 2, 3], [f"{e}" for e in orden])
    ax.set_ylabel(f"Precio Bangkok (USD/t), {lag} meses después del episodio")
    t = res["hallazgos"]["q2"]["rezagado"]
    ax.set_ylim(700, 2650)
    ax.set_title(f"Tras El Niño la tonelada vale USD {abs(t['dif_nino_nina_usd']):,.0f} menos que tras La Niña (p<0,001)".replace(",", "."),
                 loc="left")
    fig.tight_layout()
    _save(fig, "fig5_boxplot_precio_episodio_enso")


def fig6_escenarios(res):
    e = res["q3"]["escenarios"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), sharey=True)
    for ax, t in zip(axes, ["Pesquera", "Manufacturera"]):
        s = e[e.tipo == t]
        ax.fill_between(s.precio_usd_t, s.pi95_inf_pct, s.pi95_sup_pct, color=C[t], alpha=0.15, lw=0, label="Intervalo 95%")
        ax.plot(s.precio_usd_t, s.margen_op_esperado_pct, "-o", color=C[t], lw=2, ms=6, label="Margen esperado")
        ax.axhline(0, color=C["breakeven"], lw=1)
        ax.set_title(t, loc="left", fontsize=11)
        ax.set_xlabel("Precio Bangkok (USD/t)")
        for _, r in s[s.precio_usd_t.isin([900, 1573, 2300])].iterrows():
            ax.annotate(f"{r.margen_op_esperado_pct:+.1f}%\n{r.pct_empresas_en_perdida:.0f}% en pérdida".replace(".", ","),
                        (r.precio_usd_t, r.margen_op_esperado_pct), xytext=(0, 12), textcoords="offset points",
                        ha="center", fontsize=8, color=C["ink2"])
    axes[0].set_ylabel("Margen operativo agregado esperado (%)")
    axes[0].legend(loc="lower right", fontsize=8)
    pbe = res["q3"]["breakeven"].set_index("tipo").loc["Pesquera", "precio_breakeven_usd_t"]
    fig.suptitle(f"¿Dónde está el punto de quiebre? Flota: bajo ~USD {es(round(pbe, -1))}/t. Plantas: no se cruza en el rango histórico",
                 x=0.01, ha="left", fontweight="bold", fontsize=12)
    fig.tight_layout()
    _save(fig, "fig6_escenarios_estres")


def fig7_heatmap(res):
    c = res["q1"]["corr"]
    piv = c.pivot(index="metrica", columns="tipo", values="r_agregado").loc[list(["margen_bruto", "margen_operativo", "margen_neto", "roa", "roe"])]
    pv = c.pivot(index="metrica", columns="tipo", values="p_agregado").loc[piv.index]
    # agregar correlación con ONI anual
    a = res["a"]
    for t in ["Manufacturera", "Pesquera"]:
        s = a[a.tipo_empresa == t]
        for mtr in piv.index:
            col = f"{mtr}_agr"
            ss = s.dropna(subset=[col])
            from scipy import stats
            r, p = stats.pearsonr(ss.oni_prom, ss[col])
            piv.loc[mtr, f"{t}\nvs ONI"] = r
            pv.loc[mtr, f"{t}\nvs ONI"] = p
    piv = piv.rename(columns={"Manufacturera": "Manufacturera\nvs precio", "Pesquera": "Pesquera\nvs precio"})
    pv.columns = piv.columns
    import matplotlib.colors as mcolors
    cmap = mcolors.LinearSegmentedColormap.from_list("div", ["#e34948", "#f0efec", "#2a78d6"])
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    im = ax.imshow(piv.values.astype(float), cmap=cmap, vmin=-1, vmax=1, aspect="auto")
    ax.grid(False)
    lbl = {"margen_bruto": "Margen bruto", "margen_operativo": "Margen operativo", "margen_neto": "Margen neto", "roa": "ROA", "roe": "ROE"}
    ax.set_yticks(range(len(piv)), [lbl[i] for i in piv.index])
    ax.set_xticks(range(piv.shape[1]), piv.columns, fontsize=9)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            p = pv.values[i, j]
            star = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
            ax.text(j, i, f"{piv.values[i, j]:+.2f}{star}".replace(".", ","), ha="center", va="center", fontsize=10, color=C["ink"])
    fig.colorbar(im, ax=ax, shrink=0.8, label="Correlación (Pearson, serie agregada 2011–2025)")
    ax.set_title("Años El Niño = peor rentabilidad para la flota (r ≈ −0,7); el precio es el canal", loc="left")
    fig.text(0.01, -0.03, "* p<0,10  ** p<0,05  *** p<0,01 (n = 14–15 años)", fontsize=8, color=C["muted"])
    fig.tight_layout()
    _save(fig, "fig7_heatmap_correlaciones")


def fig8_dashboard(res):
    h = res["hallazgos"]
    p, o = cargar_precio(), cargar_oni()
    a = res["a"]
    fig, axes = plt.subplots(2, 4, figsize=(22, 10))
    fig.suptitle("Precio del atún, El Niño y sector atunero de Manabí (2011–2025)", fontsize=16, fontweight="bold", x=0.01, ha="left")
    # 1 serie precio
    ax = axes[0, 0]; _bandas_enso(ax, o[o.fecha >= p.fecha.min()], 0.12)
    ax.plot(p.fecha, p.precio_usd_ton, color=C["precio"], lw=1.6); ax.set_title("Precio Bangkok (USD/t) y episodios ENSO", loc="left", fontsize=11)
    # 2 margen operativo por tipo
    ax = axes[0, 1]
    for t in ["Manufacturera", "Pesquera"]:
        s = a[a.tipo_empresa == t]; ax.plot(s.anio, s.margen_operativo_agr * 100, "-o", color=C[t], ms=4, label=t)
    ax.axhline(0, color=C["breakeven"], lw=1); ax.legend(fontsize=8); ax.set_title("Margen operativo agregado (%)", loc="left", fontsize=11)
    # 3 CCF
    ax = axes[0, 2]; c = res["q2"]["ccf_df"]
    ax.axhspan(-c.banda_95[0], c.banda_95[0], color=C["grid"], lw=0, zorder=0); ax.bar(c.lag_meses, c.ccf_bruta, color=C["La Niña"], zorder=2); ax.set_ylim(-0.45, 0.2); ax.set_xlabel("meses de adelanto del ONI")
    ax.set_title(f"ONI → precio: correlación por rezago (máx. {h['q2']['lag_optimo_meses']} m)", loc="left", fontsize=11)
    # 4 precio por episodio
    ax = axes[0, 3]
    from .data_loader import dataset_mensual
    m = dataset_mensual(); lag = h["q2"]["lag_optimo_meses"]; m["ep"] = m.episodio_enso.shift(lag)
    orden = ["La Niña", "Neutro", "El Niño"]; vals = [m[m.ep == e].precio_usd_ton.mean() for e in orden]
    ax.bar(orden, vals, color=[C[e] for e in orden], width=0.55)
    for i, v in enumerate(vals): ax.text(i, v + 20, f"{v:,.0f}".replace(",", "."), ha="center", fontsize=9)
    ax.set_ylim(0, 2000); ax.set_title(f"Precio medio {lag} meses después (USD/t)", loc="left", fontsize=11)
    # 5 escenarios
    ax = axes[1, 0]; e = res["q3"]["escenarios"]
    for t in ["Manufacturera", "Pesquera"]:
        s = e[e.tipo == t]; ax.plot(s.precio_usd_t, s.margen_op_esperado_pct, "-o", color=C[t], ms=4, label=t)
    ax.axhline(0, color=C["breakeven"], lw=1); ax.legend(fontsize=8); ax.set_title("Escenarios: margen operativo esperado (%)", loc="left", fontsize=11)
    # 6 % empresas en pérdida
    ax = axes[1, 1]; pl = res["q3"]["perdidas_anio"]
    for t in ["Manufacturera", "Pesquera"]:
        s = pl[pl.tipo_empresa == t]; ax.plot(s.anio, s.pct_perdida_operativa * 100, "-o", color=C[t], ms=4, label=t)
    ax.legend(fontsize=8); ax.set_title("% de empresas con pérdida operativa", loc="left", fontsize=11)
    # 7 semáforo
    ax = axes[1, 2]; ax.axis("off"); ax.set_aspect("equal"); ax.set_xlim(0, 1.6); ax.set_ylim(0, 1)
    pr = h["q2"]["pronostico"]
    ax.add_patch(plt.Circle((0.15, 0.55), 0.12, color="#eda100"))
    ax.text(0.33, 0.78, "SEMÁFORO ONI — AMARILLO", fontsize=13, fontweight="bold")
    ax.text(0.33, 0.25, f"ONI {pr['fecha_oni']}: +{es(pr['oni_actual'], 2)} (El Niño fuerte)\n"
                        f"Patrón histórico: precio cae a ~USD {es(pr['precio_esperado'])}\n"
                        f"en ~{pr['horizonte_meses']} meses (IC95 {es(pr['pi95_inf'])}–{es(pr['pi95_sup'])})\n"
                        f"Hoy: USD {es(p.precio_usd_ton.iloc[-1])}, sobre el rango esperado\n"
                        f"Flota: riesgo si el precio baja de ~{es(round(h['q3']['breakeven']['Pesquera']['precio_breakeven_usd_t'], -1))}\nPlantas: riesgo por el alza rápida en curso",
            fontsize=10, va="bottom", color=C["ink2"])
    # 8 tabla hallazgos
    ax = axes[1, 3]; ax.axis("off")
    be = h["q3"]["breakeven"]["Pesquera"]
    txt = (f"HALLAZGOS CLAVE\n\n"
           f"• {h['cobertura']['empresas_analisis_econometrico']} empresas · {es(h['cobertura']['obs_analisis'])} obs. empresa-año\n"
           f"• Equilibrio flota: USD {es(be['precio_breakeven_usd_t'])}/t (IC95 {es(be['ic95_inf'])}–{es(be['ic95_sup'])})\n"
           f"• +USD 100/t: flota +{es(h['q1']['Pesquera']['margen_op_agr_por_100usd_pp'], 2)} pp; plantas +{es(h['q1']['Manufacturera']['margen_op_agr_por_100usd_pp'], 2)} pp\n"
           f"• Plantas: +10% de alza anual → −{es(abs(h['q1']['Manufacturera']['margen_bruto_fe_por_10pct_var_pp']), 2)} pp margen bruto\n"
           f"• El Niño vs La Niña: −USD {es(abs(h['q2']['rezagado']['dif_nino_nina_usd']))}/t ({lag} m)\n"
           f"• Cobertura #1: contrato con banda de precio\n   planta–armador (techo/piso)")
    ax.text(0, 0.95, txt, fontsize=11, va="top", linespacing=1.5)
    fig.tight_layout(rect=[0, 0.02, 1, 0.95])
    _save(fig, "fig8_dashboard_ejecutivo")


def generar_todas(res):
    for f in [fig1_precio_enso, fig2_precio_vs_margen, fig3_scatter_tipos, fig4_ccf, fig5_box_enso,
              fig6_escenarios, fig7_heatmap, fig8_dashboard]:
        f(res)
        print(f"  ✓ {f.__name__}")


if __name__ == "__main__":
    from .analysis import correr_todo
    generar_todas(correr_todo())
