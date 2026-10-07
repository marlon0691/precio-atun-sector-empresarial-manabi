"""
FASE 2–3 (PREPARE / PROCESS): construcción del dataset maestro empresa-año.

Fuentes
-------
- SUPERCIAS: base atunera Manabí (Manta, Montecristi, Jaramijó; CIIU A0311 y C1020),
  consolidada desde los balances anuales 2010–2025 (Superintendencia de Compañías,
  Valores y Seguros, 2026). https://appscvsmovil.supercias.gob.ec/ranking/reporte.html
- Thai Union IR: Frozen Whole Skipjack, Bangkok landings WPO (USD/t), 2011-01 a 2026-09.
- NOAA CPC: ONI (anomalía SST Niño 3.4, media móvil 3 meses), 2010–2026.

Todas las decisiones de limpieza quedan registradas en outputs/tables/log_limpieza_datos.txt
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "supercias"
EXT = ROOT / "data" / "external"
PROC = ROOT / "data" / "processed"
TAB = ROOT / "outputs" / "tables"
for p in (PROC, TAB):
    p.mkdir(parents=True, exist_ok=True)

_LOG = logging.getLogger("limpieza")


def _setup_log(reset: bool = True) -> None:
    _LOG.handlers.clear()
    _LOG.setLevel(logging.INFO)
    fh = logging.FileHandler(TAB / "log_limpieza_datos.txt", mode="w" if reset else "a", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    _LOG.addHandler(fh)


def registrar(msg: str, antes: int | None = None, despues: int | None = None, verbose: bool = True) -> None:
    """Documenta cada paso con conteo antes/después."""
    det = ""
    if antes is not None and despues is not None:
        elim = antes - despues
        det = f" | {antes:,} → {despues:,} ({elim:,} eliminados, {elim / max(antes, 1) * 100:.1f}%)"
    _LOG.info(f"PASO: {msg}{det}")
    if verbose:
        print(f"  ✓ {msg}{det}")


# --------------------------------------------------------------------------------------
# Códigos de "costo de ventas" por tipo de formulario (verificados contra el catálogo)
#   NIIF jerárquico (2011–2013, 2022–2025 y algunos años intermedios): 501 / 51 "COSTO DE VENTAS Y PRODUCCIÓN"
#   Casilleros 2010–2011 (formulario 101 antiguo): 797 "TOTAL COSTOS"
#   Casilleros 2014–2021 (formulario 101): 7991 "TOTAL COSTOS" / "TOTAL COSTOS OPERATIVOS"
# --------------------------------------------------------------------------------------
COD_COSTO = {"NIIF_jerarquico": ["501", "51"], "casilleros": ["797", "7991"]}
COD_ING_ORD = {"NIIF_jerarquico": ["401", "41"], "casilleros": ["1005"]}

# IPC Ecuador (2010 = 100) — tabla provista en el protocolo del estudio. Sólo se usa para
# expresar montos en USD constantes; los ratios (márgenes, ROA, ROE) no se deflactan.
# PENDIENTE: validar contra la serie oficial del INEC antes de publicar cifras en niveles.
IPC_ECUADOR = {
    2010: 100.0, 2011: 104.5, 2012: 109.1, 2013: 113.3, 2014: 117.6, 2015: 121.2,
    2016: 122.8, 2017: 124.4, 2018: 125.9, 2019: 127.3, 2020: 126.8, 2021: 129.6,
    2022: 137.5, 2023: 143.2, 2024: 147.1,
}

TIPO_MAP = {
    "Armadores / pesca marítima": "Pesquera",
    "Industria: elaboración y conservación de pescado": "Manufacturera",
}


def clasif_enso(oni: float) -> str:
    if pd.isna(oni):
        return np.nan
    if oni >= 0.5:
        return "El Niño"
    if oni <= -0.5:
        return "La Niña"
    return "Neutro"


def clasificar_tamano(activos: float) -> str:
    if pd.isna(activos):
        return "Sin clasificar"
    if activos < 100_000:
        return "Microempresa"
    if activos < 1_000_000:
        return "Pequeña"
    if activos < 5_000_000:
        return "Mediana"
    return "Grande"


# --------------------------------------------------------------------------------------
def cargar_precio() -> pd.DataFrame:
    df = pd.read_csv(EXT / "precio_atun_bangkok_skipjack_2011_2026.csv", parse_dates=["fecha"])
    df = df.rename(columns={"año": "anio"})
    return df.sort_values("fecha").reset_index(drop=True)


def cargar_oni() -> pd.DataFrame:
    """ONI NOAA CPC. La estación 'DJF' se asigna al mes central (enero) — convención estándar."""
    df = pd.read_csv(EXT / "oni_noaa_2010_2026.csv", parse_dates=["fecha"])
    df = df.rename(columns={"año": "anio"})
    df["episodio_enso"] = df["oni_anom"].apply(clasif_enso)
    return df.sort_values("fecha").reset_index(drop=True)


def precio_anual(df_precio: pd.DataFrame) -> pd.DataFrame:
    a = df_precio.groupby("anio").agg(
        precio_prom=("precio_usd_ton", "mean"),
        precio_max=("precio_usd_ton", "max"),
        precio_min=("precio_usd_ton", "min"),
        precio_std=("precio_usd_ton", "std"),
        n_meses_precio=("precio_usd_ton", "size"),
    ).reset_index()
    a["precio_var_yoy_pct"] = a["precio_prom"].pct_change() * 100
    return a


def oni_anual(df_oni: pd.DataFrame) -> pd.DataFrame:
    a = df_oni.groupby("anio").agg(oni_prom=("oni_anom", "mean"), oni_max=("oni_anom", "max"),
                                   oni_min=("oni_anom", "min")).reset_index()
    a["enso_dominante"] = a["oni_prom"].apply(clasif_enso)
    a["es_anio_nino"] = (a["oni_max"] >= 1.0).astype(int)  # algún trimestre con El Niño moderado+
    a["es_anio_nina"] = (a["oni_min"] <= -1.0).astype(int)
    return a


# --------------------------------------------------------------------------------------
def diagnostico_rocc(df: pd.DataFrame, nombre: str, id_col="ruc", anio_col="anio") -> dict:
    """Evalúa calidad de datos con framework ROCC (Reliable, Original, Comprehensive, Current)."""
    rep = {
        "fuente": nombre,
        "total_registros": int(len(df)),
        "anios_disponibles": sorted(int(x) for x in df[anio_col].unique()) if anio_col in df else "N/A",
        "n_empresas": int(df[id_col].nunique()) if id_col in df else "N/A",
        "pct_nulos": {k: float(v) for k, v in (df.isna().mean() * 100).round(1).items() if v > 0},
        "ROCC": {
            "Reliable": "SUPERCIAS = regulador oficial | Thai Union = empresa cotizada SET | NOAA = agencia federal EE.UU.",
            "Original": "Balances tal como los presentan las compañías; 2 formularios (NIIF jerárquico y casilleros) no comparables código a código",
            "Comprehensive": f"Período {df[anio_col].min()}–{df[anio_col].max()}" if anio_col in df else "Verificar",
            "Current": "SUPERCIAS: rezago ~4–16 meses | Bangkok: mensual | NOAA: mensual",
        },
    }
    if id_col in df and anio_col in df:
        n_anios = df[anio_col].nunique()
        rep["empresas_serie_completa"] = int((df.groupby(id_col)[anio_col].nunique() == n_anios).sum())
        rep["pct_series_completas"] = round(rep["empresas_serie_completa"] / max(rep["n_empresas"], 1) * 100, 1)
        n_anios_obs = df[anio_col].nunique()
        rep["suficiencia_estadistica"] = {
            "OLS_pooled": "SUFICIENTE" if len(df) >= 30 else "INSUFICIENTE",
            "Panel_efectos_fijos": "SUFICIENTE" if len(df) >= 50 else "INSUFICIENTE",
            "Variacion_temporal_del_precio": f"LIMITADA ({n_anios_obs} años): el precio es común a todas las empresas; "
                                             "la identificación del efecto precio descansa en ~{n} observaciones temporales".format(n=n_anios_obs),
        }
    with open(TAB / f"rocc_{nombre.lower().replace(' ', '_')}.json", "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2, default=str)
    return rep


# --------------------------------------------------------------------------------------
def extraer_cuentas(largo: pd.DataFrame) -> pd.DataFrame:
    """Extrae costo de ventas e ingresos ordinarios desde el formato largo (por empresa-año)."""
    out = []
    for nombre, codmap in (("costo_ventas", COD_COSTO), ("ingresos_ord_largo", COD_ING_ORD)):
        parts = []
        for form, cods in codmap.items():
            sub = largo[(largo.tipo_formulario == form) & (largo.codigo_cuenta.isin(cods))]
            # si coexisten 2 códigos equivalentes, tomar el mayor valor absoluto (evita doble conteo)
            parts.append(sub.groupby(["anio", "ruc", "tipo_formulario"])["valor"].max())
        out.append(pd.concat(parts).rename(nombre))
    return pd.concat(out, axis=1).reset_index()


def construir_dataset_maestro(verbose: bool = True) -> pd.DataFrame:
    _setup_log()
    registrar("=== INICIO PROCESO — Base atunera Manabí (SUPERCIAS) + Bangkok + ONI ===", verbose=verbose)

    # [1] Carga
    panel = pd.read_csv(RAW / "panel_variables_clave.csv", dtype={"ruc": str, "expediente": str})
    n0 = len(panel)
    registrar(f"[1] Panel SUPERCIAS cargado: {n0:,} empresa-año, {panel.ruc.nunique()} empresas, "
              f"{panel.anio.min()}–{panel.anio.max()}", verbose=verbose)
    rocc_raw = diagnostico_rocc(panel, "SUPERCIAS panel bruto")

    # [2] Cuentas adicionales desde formato largo
    largo = pd.read_parquet(RAW / "balances_largo.parquet")
    cuentas = extraer_cuentas(largo)
    panel = panel.merge(cuentas, on=["anio", "ruc", "tipo_formulario"], how="left")
    registrar(f"[2] Costo de ventas extraído (códigos {COD_COSTO}): disponible en "
              f"{panel.costo_ventas.notna().mean() * 100:.1f}% de registros", verbose=verbose)

    # [3] Tipo de empresa (filtro geográfico y CIIU ya aplicado en la consolidación)
    panel["tipo_empresa"] = panel["grupo"].map(TIPO_MAP)
    registrar(f"[3] Tipo empresa: {panel.tipo_empresa.value_counts().to_dict()} "
              "(Manabí: Manta/Montecristi/Jaramijó; CIIU A0311 → Pesquera, C1020 → Manufacturera)", verbose=verbose)

    # [4] Duplicados
    antes = len(panel)
    panel = panel.sort_values("n_cuentas_no_cero").drop_duplicates(["ruc", "anio"], keep="last")
    registrar("[4] Duplicados ruc-año eliminados (se conserva el registro más completo)", antes, len(panel), verbose)

    # [5] Empresas operativas
    antes = len(panel)
    panel["ingresos"] = panel["ingresos_ordinarios"].where(panel["ingresos_ordinarios"] > 0, panel["ingresos_totales"])
    panel["ingresos"] = panel["ingresos"].where(panel["ingresos"] > 0, panel["ingresos_ord_largo"])
    activas = (panel["activo_total"] > 0) & (panel["ingresos"] > 0)
    panel["inactiva"] = (~activas).astype(int)
    df = panel[activas].copy()
    registrar("[5] Excluidas empresa-año sin activos o sin ingresos (inactivas / 'de papel')", antes, len(df), verbose)

    # [6] Ratios
    df["margen_bruto"] = (df["ingresos"] - df["costo_ventas"]) / df["ingresos"]
    df.loc[df["costo_ventas"].isna() | (df["costo_ventas"] <= 0), "margen_bruto"] = np.nan
    df["margen_operativo"] = df["utilidad_antes_part_ir"] / df["ingresos"]
    df["margen_neto"] = df["utilidad_neta"] / df["ingresos"]
    df["roa"] = df["utilidad_neta"] / df["activo_total"]
    df["roe"] = (df["utilidad_neta"] / df["patrimonio_total"]).where(df["patrimonio_total"] > 0)
    df["perdida_operativa"] = (df["utilidad_antes_part_ir"] < 0).astype(float).where(df["utilidad_antes_part_ir"].notna())
    df["perdida_neta"] = (df["utilidad_neta"] < 0).astype(float)
    df = df.sort_values(["ruc", "anio"])
    df["ventas_var_yoy_pct"] = df.groupby("ruc")["ingresos"].pct_change() * 100
    df.loc[df.groupby("ruc")["anio"].diff() != 1, "ventas_var_yoy_pct"] = np.nan
    registrar(f"[6] Ratios calculados. Margen bruto disponible: {df.margen_bruto.notna().sum():,} obs", verbose=verbose)

    # [7] Outliers: marcar (no eliminar) y crear versión winsorizada (p1–p99) para estimaciones
    for m in ["margen_bruto", "margen_operativo", "margen_neto", "roa", "roe", "ventas_var_yoy_pct"]:
        s = df[m]
        z = (s - s.mean()) / s.std()
        df[f"{m}_outlier"] = (z.abs() > 3).astype(int)
        lo, hi = s.quantile([0.01, 0.99])
        df[f"{m}_w"] = s.clip(lo, hi)
        registrar(f"[7] Outliers |z|>3 en {m}: {int(df[f'{m}_outlier'].sum())} (conservados y marcados); "
                  f"winsorización p1–p99 en {m}_w [{lo:.3f}, {hi:.3f}]", verbose=verbose)

    # [8] Imputación: NO se imputan ratios (interpolar márgenes inventaría rentabilidad);
    #     se documentan los faltantes.
    for m in ["margen_bruto", "margen_operativo", "roe"]:
        registrar(f"[8] {m}: {df[m].isna().sum():,} nulos — no imputados (decisión conservadora)", verbose=verbose)
    registrar("[8] 2014 (formulario casilleros): solo ~9% reporta utilidad antes de part./IR y ~7% costo de ventas → "
              "márgenes bruto/operativo 2014 se excluyen de agregados (regla: cobertura < 50%)", verbose=verbose)

    # [9] Tamaño y deflactación
    df["tamano_empresa"] = df["activo_total"].apply(clasificar_tamano)
    df["ipc"] = df["anio"].map(IPC_ECUADOR)
    for c in ["ingresos", "utilidad_neta", "activo_total", "patrimonio_total", "costo_ventas"]:
        df[f"{c}_real"] = df[c] / df["ipc"] * 100
    registrar("[9] Tamaño por activos y montos en USD constantes 2010 (2025 sin IPC en tabla → NaN)", verbose=verbose)

    # [10–11] Precio y ONI
    pa, oa = precio_anual(cargar_precio()), oni_anual(cargar_oni())
    df = df.merge(pa, on="anio", how="left").merge(oa, on="anio", how="left")
    df["precio_prom_100"] = df["precio_prom"] / 100  # efecto por cada USD 100/t
    registrar(f"[10] Precio Bangkok anual unido (2011–2026). Obs sin precio (2010): {df.precio_prom.isna().sum()}", verbose=verbose)
    registrar("[11] ONI anual unido (promedio, máx., mín.)", verbose=verbose)

    # [12] Guardar
    df.to_parquet(PROC / "dataset_maestro_manabi.parquet", index=False)
    df.to_csv(PROC / "dataset_maestro_manabi.csv", index=False, encoding="utf-8")
    diagnostico_rocc(df, "SUPERCIAS dataset maestro")
    registrar(f"[12] Dataset maestro: {len(df):,} obs empresa-año, {df.ruc.nunique()} empresas, "
              f"{df.anio.nunique()} años ({df.anio.min()}–{df.anio.max()})", verbose=verbose)
    return df


def dataset_mensual() -> pd.DataFrame:
    p, o = cargar_precio(), cargar_oni()
    m = p.merge(o[["fecha", "oni_anom", "episodio_enso"]], on="fecha", how="inner").sort_values("fecha")
    m["log_precio"] = np.log(m["precio_usd_ton"])
    m["dlog_precio"] = m["log_precio"].diff() * 100
    return m.reset_index(drop=True)


def agregados_sector(df: pd.DataFrame) -> pd.DataFrame:
    """Márgenes agregados (ponderados por ingresos) por tipo y año — la 'empresa representativa'."""
    g = df.dropna(subset=["tipo_empresa"]).copy()
    g["gb"] = (g["ingresos"] - g["costo_ventas"]).where(g["margen_bruto"].notna())
    g["ing_mb"] = g["ingresos"].where(g["margen_bruto"].notna())
    a = g.groupby(["tipo_empresa", "anio"]).agg(
        n_empresas=("ruc", "nunique"), ingresos=("ingresos", "sum"), utilidad_neta=("utilidad_neta", "sum"),
        uai=("utilidad_antes_part_ir", "sum"), activos=("activo_total", "sum"), patrimonio=("patrimonio_total", "sum"),
        gb=("gb", "sum"), ing_mb=("ing_mb", "sum"),
        pct_perdida_operativa=("perdida_operativa", "mean"), pct_perdida_neta=("perdida_neta", "mean"),
        margen_bruto_mediana=("margen_bruto", "median"),
    ).reset_index()
    # margen operativo solo sobre empresas que reportan utilidad antes de part. e IR
    g["ing_uai"] = g["ingresos"].where(g["utilidad_antes_part_ir"].notna())
    cov = g.groupby(["tipo_empresa", "anio"]).agg(ing_uai=("ing_uai", "sum"),
                                                  cob_uai=("utilidad_antes_part_ir", lambda s: s.notna().mean()),
                                                  cob_mb=("margen_bruto", lambda s: s.notna().mean())).reset_index()
    a = a.merge(cov, on=["tipo_empresa", "anio"])
    a["margen_bruto_agr"] = (a["gb"] / a["ing_mb"]).where(a["cob_mb"] >= 0.5)
    a["margen_operativo_agr"] = (a["uai"] / a["ing_uai"]).where(a["cob_uai"] >= 0.5)
    a["pct_perdida_operativa"] = a["pct_perdida_operativa"].where(a["cob_uai"] >= 0.5)
    # Regla: si < 50% de las empresas reporta la cuenta en el año (2014, formulario casilleros), el agregado es NaN
    a["margen_neto_agr"] = a["utilidad_neta"] / a["ingresos"]
    a["roa_agr"] = a["utilidad_neta"] / a["activos"]
    a["roe_agr"] = a["utilidad_neta"] / a["patrimonio"]
    a = a.merge(precio_anual(cargar_precio()), on="anio", how="left").merge(oni_anual(cargar_oni()), on="anio", how="left")
    return a


if __name__ == "__main__":
    construir_dataset_maestro()
