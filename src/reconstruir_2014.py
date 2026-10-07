"""
Reconstrucción del estado de resultados 2014 (formulario 101 'casilleros').

En los balances SUPERCIAS 2014 los casilleros de totales (6999 Total ingresos, 7991 Total costos,
7992 Total gastos, 7999 Total costos y gastos, 801/802 Utilidad/Pérdida del ejercicio) vienen vacíos
para ~95% de las compañías, pero las partidas de detalle sí están. Este módulo suma el detalle:

- Ingresos = Σ casilleros 6xxx, excepto 'VALOR EXENTO …' (subconjuntos), informativos y 6999.
- Costo de ventas = Σ partidas 'COSTO …' − Σ '(-) COSTO INVENTARIO FINAL …'.
- Gastos = Σ partidas 'GASTO …' y 'GASTOS …' (gestión, viaje, transacción, ajustes).
- Se excluyen siempre los 'VALOR NO DEDUCIBLE …' (son subconjuntos de la partida principal) y los totales.
- Utilidad antes de part. e IR = Ingresos − Costo de ventas − Gastos.

Validación: para las empresas que sí reportan 803 (15% participación trabajadores), 803/0,15 debe
aproximar la utilidad reconstruida; para las que reportan 7991/7999 se compara el total.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TOTALES = {"6999", "7991", "7992", "7999"}


def clasificar(codigo: str, cuenta: str) -> str | None:
    c, d = str(codigo), str(cuenta).upper().strip()
    if c in TOTALES or "VALOR NO DEDUCIBLE" in d or "VALOR EXENTO" in d or "INFORMATIVO" in d:
        return None
    if len(c) == 4 and c.startswith("6"):
        return "ingreso"
    if len(c) == 4 and c.startswith("7"):
        if d.startswith("(-) COSTO") and "INVENTARIO FINAL" in d:
            return "costo_neg"
        if d.startswith("COSTO") or d.startswith("IVA QUE SE CARGA AL COSTO") or d.startswith("AJUSTES - COSTO"):
            return "costo"
        if d.startswith("GASTO") or d.startswith("IVA QUE SE CARGA AL GASTO") or d.startswith("AJUSTES - GASTO") \
                or d.startswith("PAGO POR REEMBOLSO"):
            return "gasto"
        return "gasto" if "GASTO" in d else None
    return None


def reconstruir(largo: pd.DataFrame, anio: int = 2014) -> pd.DataFrame:
    x = largo[(largo.anio == anio) & (largo.tipo_formulario == "casilleros")].copy()
    x["clase"] = [clasificar(c, d) for c, d in zip(x.codigo_cuenta, x.cuenta)]
    x["v"] = np.where(x.clase == "costo_neg", -x.valor, x.valor)
    x.loc[x.clase == "costo_neg", "clase"] = "costo"
    piv = x.dropna(subset=["clase"]).pivot_table(index="ruc", columns="clase", values="v", aggfunc="sum").fillna(0)
    for col in ["ingreso", "costo", "gasto"]:
        if col not in piv:
            piv[col] = 0.0
    part = x[x.codigo_cuenta.astype(str) == "803"].groupby("ruc").valor.sum()
    out = pd.DataFrame({
        "anio": anio,
        "ingresos_rec": piv["ingreso"],
        "costo_ventas_rec": piv["costo"].where(piv["costo"] > 0),
        "gastos_rec": piv["gasto"],
    })
    out["utilidad_antes_part_ir_rec"] = out["ingresos_rec"] - out["costo_ventas_rec"].fillna(0) - out["gastos_rec"]
    out["uai_desde_803"] = (part / 0.15).reindex(out.index)
    return out.reset_index()
