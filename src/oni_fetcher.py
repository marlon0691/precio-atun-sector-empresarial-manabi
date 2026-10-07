"""Descarga y estandariza el ONI (NOAA CPC). Fuente: https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"""
from __future__ import annotations

import pandas as pd
import requests

from .data_loader import EXT, clasif_enso

URL_ONI = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
SEASON = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
          "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}


def descargar_oni(desde: int = 2010, guardar: bool = True) -> pd.DataFrame:
    """Cada estación de 3 meses se asigna a su mes central (DJF → enero, …, NDJ → diciembre)."""
    r = requests.get(URL_ONI, timeout=20)
    r.raise_for_status()
    rows = [l.split() for l in r.text.strip().splitlines()[1:] if l.strip()]
    df = pd.DataFrame(rows, columns=["temporada", "año", "total", "anom"])
    df["año"] = df["año"].astype(int)
    df["mes"] = df["temporada"].map(SEASON)
    df["oni_anom"] = df["anom"].astype(float)
    df["fecha"] = pd.to_datetime(dict(year=df["año"], month=df["mes"], day=1))
    df["episodio_enso"] = df["oni_anom"].apply(clasif_enso)
    df = df[df["año"] >= desde][["temporada", "año", "mes", "fecha", "oni_anom", "episodio_enso"]]
    if guardar:
        df.to_csv(EXT / f"oni_noaa_{desde}_{df['año'].max()}.csv", index=False)
    return df


if __name__ == "__main__":
    print(descargar_oni().tail())
