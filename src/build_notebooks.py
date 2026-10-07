"""Genera y ejecuta los 7 notebooks del framework Ask → Prepare → Process → Analyze → Share → Act."""
from __future__ import annotations

import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

from .data_loader import ROOT

NB = ROOT / "notebooks"
NB.mkdir(exist_ok=True)

SETUP = """import sys, warnings, json
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent))
warnings.filterwarnings('ignore')
import pandas as pd, numpy as np
pd.set_option('display.width', 200); pd.set_option('display.max_columns', 30)
from IPython.display import Image, display"""

REFS = """**Literatura de referencia:** Lehodey et al. (1997, *Nature*); Ormaza-González et al. (2016, *Adv. Geosci.*);
Kim et al. (2020, *Sci. Rep.*); Hou et al. (2022, *Front. Mar. Sci.*). Ver `references/literatura_cientifica.md`."""

NOTEBOOKS = {
    "01_ask_preguntas_hipotesis": [
        ("md", """# 01 · ASK — Preguntas de negocio e hipótesis
**Cliente:** gerentes generales de plantas procesadoras (CIIU C1020) y armadores (CIIU A0311) de Manta, Montecristi y Jaramijó.

| # | Pregunta | Hipótesis a priori (protocolo) |
|---|---|---|
| Q1 | ¿El precio del atún afecta el desempeño financiero? | H1a manufactureras: precio ↑ → margen ↓ · H1b pesqueras: precio ↑ → ingresos/margen ↑ |
| Q2 | ¿El Niño (ONI) se relaciona con el precio Bangkok? | H2a El Niño → precio ↑ (3–6 m) · H2b relación no lineal · H2c rezago 3–6 meses |
| Q3 | ¿Cuánto pueden perder las empresas? | Existe un precio de quiebre identificable |

### Mecanismo propuesto por la literatura
- **Lehodey et al. (1997):** El Niño desplaza la *warm pool* y con ella al barrilete hacia el **este** del Pacífico.
  El paper documenta una **redistribución** de la biomasa, no necesariamente una caída de las capturas globales.
- **Ormaza-González et al. (2016):** en Ecuador, El Niño 1997-98 elevó capturas de barrilete +22,7%; La Niña 2009-10 las redujo −38%;
  la relación es **no lineal** (R² 0,44 con MEI; 0,18 con ONI).
- **Kim et al. (2020):** el ONI clásico subestima el efecto; mejores predictores son la temperatura a 100 m y la salinidad a 5 m.
- **Hou et al. (2022):** el vínculo ENSO–atún es **no estacionario** (depende de la fase PDO).

> Por lo tanto, la dirección de H2a (El Niño → precio ↑) **no está garantizada** por la literatura: si El Niño redistribuye
> el atún en lugar de reducirlo, el precio de Bangkok puede incluso **bajar**. Lo contrastamos con datos en el notebook 05."""),
        ("code", SETUP + "\nfrom src.data_loader import cargar_precio, cargar_oni\np, o = cargar_precio(), cargar_oni()\nprint(p.shape, p.fecha.min().date(), p.fecha.max().date())\nprint(o.shape, o.fecha.min().date(), o.fecha.max().date())"),
        ("md", "### Métricas por pregunta\n| Métrica | Fórmula |\n|---|---|\n| Margen bruto | (Ingresos − Costo de ventas) / Ingresos |\n| Margen operativo | Utilidad antes de part. trabajadores e IR / Ingresos |\n| Margen neto | Utilidad neta / Ingresos |\n| ROA / ROE | Utilidad neta / Activos · / Patrimonio |\n| Sensibilidad | Δ margen (pp) por +USD 100/t, con IC 95% |\n\n" + REFS),
    ],
    "02_prepare_diagnostico_rocc": [
        ("md", "# 02 · PREPARE — Diagnóstico ROCC de calidad de datos\nReliable · Original · Comprehensive · Current. Fuente financiera: base atunera Manabí consolidada desde balances SUPERCIAS 2010–2025 (Superintendencia de Compañías, Valores y Seguros, 2026)."),
        ("code", SETUP + "\nfrom src.data_loader import RAW, diagnostico_rocc\npanel = pd.read_csv(RAW/'panel_variables_clave.csv', dtype={'ruc':str})\nrep = diagnostico_rocc(panel, 'SUPERCIAS panel bruto')\nprint(json.dumps(rep, ensure_ascii=False, indent=1, default=str))"),
        ("code", "display(panel.groupby(['anio','grupo']).size().unstack())\ndisplay(panel.groupby('anio').tipo_formulario.value_counts().unstack().fillna(0).astype(int))"),
        ("code", "print('Cuadre Activo = Pasivo + Patrimonio:', f\"{(panel.cuadre_A_P_Pt.abs()<1).mean():.1%}\")\nprint('Ingresos totales = 0:', f\"{(panel.ingresos_totales<=0).mean():.1%} de empresa-año\")"),
        ("md", """### Hallazgos ROCC
- **Reliable:** regulador oficial (SUPERCIAS), empresa cotizada (Thai Union, SET), agencia federal (NOAA). ✔
- **Original:** dos formularios no comparables código a código (NIIF jerárquico vs. casilleros 101) → se usan variables homologadas y se mapea el costo de ventas por formulario (501/51; 797; 7991).
- **Comprehensive:** 336 empresas, 2010–2025. **2014** solo reporta utilidad antes de IR en ~9% y costo de ventas en ~7% → márgenes bruto/operativo 2014 excluidos.
- **Current:** balances 2025 ya disponibles; precio a sep-2026; ONI a ago-2026 (JAS).
- **Suficiencia:** muchas empresas, pero el precio es **común a todas** → la variación identificadora son ~15 años. Toda inferencia sobre el efecto precio se trata como evidencia de series cortas."""),
    ],
    "03_process_limpieza_datos": [
        ("md", "# 03 · PROCESS — Limpieza documentada con log de auditoría\nCada paso registra conteos antes/después en `outputs/tables/log_limpieza_datos.txt`."),
        ("code", SETUP + "\nfrom src.data_loader import construir_dataset_maestro\ndf = construir_dataset_maestro()"),
        ("code", "print(open('../outputs/tables/log_limpieza_datos.txt', encoding='utf-8').read())"),
        ("code", "display(df.groupby(['anio','tipo_empresa']).ruc.nunique().unstack())\ndisplay(df[['margen_bruto','margen_operativo','margen_neto','roa','roe']].describe(percentiles=[.05,.5,.95]).round(3))"),
        ("md", """### Decisiones de limpieza (y por qué)
1. **No se imputan ratios.** Interpolar márgenes inventaría rentabilidad que no existió.
2. **Outliers se marcan, no se eliminan**; para estimar se acotan los ratios a [−1, 1] y se exige ingresos ≥ USD 100 mil.
3. **Sin efectos fijos de año en las regresiones:** el precio anual es igual para todas las empresas → colinealidad perfecta.
4. IPC Ecuador del protocolo usado solo para niveles en USD constantes (**pendiente validar con INEC**); los ratios no requieren deflactación."""),
    ],
    "04_analyze_q1_precio_vs_desempeno": [
        ("md", "# 04 · ANALYZE — Q1: precio Bangkok ↔ desempeño financiero\nTres lentes: (A) correlaciones, (B) panel con efectos fijos de empresa y errores Driscoll-Kraay, (C) empresa representativa (agregados ponderados por ingresos) con errores HAC."),
        ("code", SETUP + "\nfrom src.analysis import correr_todo\nR = correr_todo()\nq1 = R['q1']"),
        ("code", "display(q1['corr'])"),
        ("code", "p = q1['panel']\ndisplay(p[p.variable=='precio_prom_100'].round(3))\nprint('Efecto de la VARIACIÓN anual del precio (+10%):')\ndisplay(p[p.variable=='dp10'].round(3))"),
        ("code", "display(q1['agr'].round(3))\nprint('Test de asimetría (panel, margen operativo):', {k: round(v,4) for k,v in q1['asimetria'].items()})"),
        ("code", "display(Image('../outputs/figures/fig2_precio_vs_margen_operativo.png', width=900))\ndisplay(Image('../outputs/figures/fig3_scatter_precio_margen_por_tipo.png', width=900))"),
        ("md", """### Lectura
- **H1b (pesqueras) — CONFIRMADA y fuerte.** Margen operativo agregado ≈ +1,0 pp por cada +USD 100/t (R² ≈ 0,74). Las ventas crecen ≈ +4,9% por cada +10% de precio.
- **H1a (manufactureras) — RECHAZADA en niveles.** El margen de las plantas **no cae** cuando el precio es alto (+0,3 pp por USD 100, p≈0,02 agregado; no significativo a nivel empresa): el costo se traslada al precio de la conserva/lomo.
- **Pero sí hay un efecto de VELOCIDAD:** a nivel empresa, cada +10% de **alza anual** del precio reduce el margen bruto de las plantas ≈ 0,7 pp (p≈0,002). El daño es transitorio: ocurre el año del salto, mientras los contratos de venta se reajustan.
- La diferencia de sensibilidad entre tipos es significativa (interacción tipo×precio, p<0,001)."""),
    ],
    "05_analyze_q2_elnino_vs_precio": [
        ("md", "# 05 · ANALYZE — Q2: El Niño (ONI) ↔ precio Bangkok\nSerie mensual ene-2011 a ago-2026 (188 meses). Errores HAC (Newey-West, 12 rezagos)."),
        ("code", SETUP + "\nfrom src.analysis import q2\nr = q2()\nprint('ADF p-values:', {k: round(v,3) for k,v in r['adf'].items()})\nprint('Lag óptimo CCF:', r['lag_optimo'], 'meses; r =', round(r['ccf_lag_optimo'],3))"),
        ("code", "display(r['ccf_df'].round(3))"),
        ("code", "g = r['granger']\ndisplay(g.pivot(index='lag', columns='hipotesis', values='p_value').round(3))"),
        ("code", "display(pd.read_csv('../outputs/tables/q2_precio_por_episodio_enso.csv'))\ndisplay(r['tests_enso'])\nprint(open('../outputs/tables/q2_tukey_hsd.txt').read())"),
        ("code", "display(r['poly'].round(3))\nprint(r['mod_poly'].summary())"),
        ("code", "display(Image('../outputs/figures/fig1_precio_bangkok_enso.png', width=900))\ndisplay(Image('../outputs/figures/fig4_ccf_oni_precio.png', width=900))\ndisplay(Image('../outputs/figures/fig5_boxplot_precio_episodio_enso.png', width=700))"),
        ("md", """### Lectura
- **H2a — RECHAZADA (signo opuesto).** El Niño se asocia con precios Bangkok **más bajos**: ≈ −USD 434/t frente a La Niña a 7 meses (IC95 HAC −667 a −201; p<0,001).
  Es coherente con Lehodey et al. (1997): El Niño **redistribuye** el barrilete hacia el este y mantiene la oferta. La escasez que supone el protocolo no aparece en los datos.
- **H2c — rezago ~7 meses** (CCF máxima en valor absoluto, r ≈ −0,39). Advertencia: tras pre-blanquear, la correlación desaparece casi por completo, y **Granger no es significativo** (p mín ≈ 0,17).
  El ONI marca el **régimen** de precios de los meses siguientes, pero no mejora el pronóstico mes a mes una vez considerada la inercia del precio.
- **H2b — no linealidad parcial.** El término cuadrático es significativo con rezagos ≥ 10–12 meses (R² sube de ~0,12 a ~0,22). El precio mínimo se da con ONI ≈ +1 °C y repunta en los extremos, en línea con Ormaza-González et al. (2016).
- **2026 es una anomalía:** con ONI +2,16 el precio está en USD 2.275/t, por encima del intervalo de predicción del modelo. Hay que vigilar si el patrón histórico se reafirma (caída) o si dominan otros factores (Hou et al., 2022: no estacionariedad)."""),
    ],
    "06_analyze_q3_perdidas_escenarios": [
        ("md", "# 06 · ANALYZE — Q3: pérdidas potenciales, precio de quiebre, VaR y escenarios"),
        ("code", SETUP + "\nfrom src.analysis import correr_todo\nR = correr_todo(); q3 = R['q3']\ndisplay(q3['breakeven'].T)"),
        ("code", "display(q3['var'].round(3))"),
        ("code", "display(q3['escenarios'])"),
        ("code", "display(q3['perdidas_anio'].pivot(index='anio', columns='tipo_empresa', values='pct_perdida_operativa').round(3))\nprint(q3['shock_velocidad_manuf'])"),
        ("code", "display(Image('../outputs/figures/fig6_escenarios_estres.png', width=950))"),
        ("md", """### Lectura
- **Armadores:** precio de quiebre operativo ≈ **USD 1.340/t** (IC95 ≈ 1.210–1.460), dentro del rango observado. Los años con margen operativo agregado negativo (2015, 2019) son justamente los de precio < USD 1.250.
  Con USD 900/t, ~74% de las empresas tendría pérdida operativa; impacto ≈ −USD 74 M en utilidad operativa frente a 2025.
- **Plantas:** el margen operativo agregado **nunca** fue negativo en 2011–2025. El quiebre extrapolado (≈ USD 160/t) está fuera de rango y no es interpretable.
  Su riesgo real es de **velocidad**: un salto de +30% en el año implica ≈ −2 pp de margen bruto (≈ −USD 27 M sobre las ventas de 2025).
- **VaR 95% (empresa-año):** margen operativo −2,7% en plantas vs −17,7% en flota. La flota tiene una cola mucho más pesada."""),
    ],
    "07_share_act_visualizaciones_hedging": [
        ("md", "# 07 · SHARE & ACT — Visualizaciones y opciones de cobertura"),
        ("code", SETUP + "\nfrom src.analysis import correr_todo\nfrom src.visualization import generar_todas\nR = correr_todo(); generar_todas(R)\ndisplay(Image('../outputs/figures/fig8_dashboard_ejecutivo.png', width=1100))\ndisplay(Image('../outputs/figures/fig7_heatmap_correlaciones.png', width=750))"),
        ("md", """## Marco regulatorio y de mercado (resumen; detalle en README §Act)
- **No existe un contrato de futuros listado y líquido para atún skipjack** (CME/SGX). La cobertura es bilateral (OTC) u operativa.
- **Res. JPRFM-2026-009-M (6-mar-2026):** crea el servicio del BCE como agente para coberturas de commodities con derivados internacionales, **solo para empresas públicas nacionales**. No es una vía para empresas privadas.
- Opciones viables: contratos forward/precio fijo con proveedores, **contratos de banda de precio planta–armador**, integración vertical y gestión de inventario guiada por el ONI.

## Recomendación #1
**Contrato de suministro con banda de precio (piso/techo) entre plantas y armadores de Manta**, indexado al Bangkok skipjack:
- La flota necesita un **piso** (pierde bajo ~USD 1.340/t) y la planta necesita un **techo** o suavizar alzas rápidas (−0,7 pp de margen bruto por cada +10% de alza anual).
- Los riesgos son opuestos y se compensan: es una **cobertura natural** que no exige mercados de derivados.

## Protocolo ONI (revisado con la evidencia)
| Señal | Lectura histórica | Armadores | Plantas |
|---|---|---|---|
| ONI ≥ +0,5 dos meses | precio tiende a bajar en 6–9 m | activar piso / vender forward | no sobre-comprar; esperar |
| ONI ≥ +1,0 | precio medio tras El Niño ≈ USD 1.320 | piso cerca del equilibrio (~1.340) | contratar volumen escalonado |
| ONI ≤ −0,5 | precio tiende a subir (≈ USD 1.760) | capturar precio alto | asegurar techo **antes** del alza |"""),
    ],
}


def construir(ejecutar: bool = True):
    for nombre, celdas in NOTEBOOKS.items():
        nb = nbf.v4.new_notebook()
        nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
        nb.cells = [nbf.v4.new_markdown_cell(c) if t == "md" else nbf.v4.new_code_cell(c) for t, c in celdas]
        if ejecutar:
            ExecutePreprocessor(timeout=600, kernel_name="python3").preprocess(nb, {"metadata": {"path": str(NB)}})
        nbf.write(nb, NB / f"{nombre}.ipynb")
        print("  ✓", nombre)


if __name__ == "__main__":
    construir()
