"""Exporta los datos que alimentan dashboard/dashboard_ejecutivo.html."""
import json
import numpy as np
import pandas as pd
from .analysis import correr_todo
from .data_loader import ROOT, cargar_precio, cargar_oni


def exportar():
    R = correr_todo()
    h = R["hallazgos"]
    p, o = cargar_precio(), cargar_oni()
    m = p.merge(o[["fecha", "oni_anom"]], on="fecha", how="left")
    a = R["a"]
    d = R["d"]
    modelos = {t: {"b0": float(R["q1"]["modelos_agr"][(t, "margen_operativo")].params["Intercept"]),
                   "b1": float(R["q1"]["modelos_agr"][(t, "margen_operativo")].params["p100"])} for t in ["Manufacturera", "Pesquera"]}
    base = int(a.anio.max())
    firmas = {t: [round(float(x), 4) for x in d[(d.tipo_empresa == t) & (d.anio == base)].margen_operativo_c.dropna()] for t in modelos}
    ingresos = {t: float(a[(a.tipo_empresa == t) & (a.anio == base)].ingresos.iloc[0]) for t in modelos}
    ep = pd.read_csv(ROOT / "outputs/tables/q2_precio_por_episodio_enso.csv")
    lag = h["q2"]["lag_optimo_meses"]
    ep = ep[ep.rezago_meses == lag]
    data = {
        "mensual": [{"f": f"{r.fecha:%Y-%m}", "p": float(r.precio_usd_ton), "o": (None if pd.isna(r.oni_anom) else float(r.oni_anom))} for r in m.itertuples()],
        "anual": [{"t": r.tipo_empresa, "a": int(r.anio), "mo": None if pd.isna(r.margen_operativo_agr) else round(float(r.margen_operativo_agr) * 100, 2),
                   "n": int(r.n_empresas), "pp": round(float(r.precio_prom))} for r in a.itertuples()],
        "modelos": modelos, "firmas": firmas, "ingresos": ingresos, "p_base": h["q3"]["precio_base"], "anio_base": base,
        "episodios": {r.ep: {"media": round(r.mean), "n": int(r["count"])} for _, r in ep.rename(columns={"ep": "ep"}).iterrows()} if False else
                     {row["ep"]: {"media": round(row["mean"]), "n": int(row["count"])} for _, row in ep.iterrows()},
        "h": h,
    }
    (ROOT / "dashboard" / "data.json").write_text(json.dumps(data, ensure_ascii=False, default=lambda x: x.item() if hasattr(x, "item") else str(x)), encoding="utf-8")
    return data




def construir_html():
    data = exportar()
    tpl = (ROOT / "dashboard" / "template.html").read_text(encoding="utf-8")
    body = tpl.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False, default=lambda x: x.item() if hasattr(x, "item") else str(x)))
    (ROOT / "dashboard" / "dashboard_ejecutivo_artifact.html").write_text(body, encoding="utf-8")
    full = ('<!doctype html>\n<html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"></head><body>\n' + body + "\n</body></html>")
    (ROOT / "dashboard" / "dashboard_ejecutivo.html").write_text(full, encoding="utf-8")
    return ROOT / "dashboard" / "dashboard_ejecutivo.html"


if __name__ == "__main__":
    print(construir_html())
