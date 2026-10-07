"""
Scraper del precio de materia prima de Thai Union (Frozen Whole Skipjack, Bangkok landings WPO, USD/t).
Fuente: https://investor.thaiunion.com/en/financial-info/raw-material-price-trend

La página publica una tabla con meses en filas y años en columnas. La estructura HTML puede cambiar;
si el parseo falla, el CSV versionado en data/external/ es la fuente de verdad del estudio.
"""
from __future__ import annotations

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .data_loader import EXT

URL = "https://investor.thaiunion.com/en/financial-info/raw-material-price-trend"
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
         "Septiembre", "Octubre", "Noviembre", "Diciembre"]
EN = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def descargar_precio(guardar: bool = True) -> pd.DataFrame:
    r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    filas = []
    for table in soup.find_all("table"):
        head = [th.get_text(strip=True) for th in table.find_all("th")]
        anios = [int(h) for h in head if h.isdigit() and len(h) == 4]
        if not anios:
            continue
        for tr in table.find_all("tr"):
            celdas = [td.get_text(strip=True).replace(",", "") for td in tr.find_all(["td", "th"])]
            if not celdas or celdas[0][:3].lower() not in EN:
                continue
            mes = EN.index(celdas[0][:3].lower()) + 1
            for anio, val in zip(anios, celdas[1:]):
                try:
                    filas.append({"año": anio, "mes": MESES[mes - 1], "mes_num": mes, "precio_usd_ton": float(val)})
                except ValueError:
                    pass
    df = pd.DataFrame(filas)
    if df.empty:
        raise RuntimeError("No se pudo parsear la tabla de Thai Union; usar el CSV de data/external/")
    df["fecha"] = pd.to_datetime(dict(year=df["año"], month=df["mes_num"], day=1))
    df = df.sort_values("fecha").drop_duplicates("fecha")
    if guardar:
        df.to_csv(EXT / f"precio_atun_bangkok_skipjack_{df['año'].min()}_{df['año'].max()}.csv", index=False)
    return df


if __name__ == "__main__":
    print(descargar_precio().tail())
