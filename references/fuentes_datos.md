# Fuentes de datos

| Fuente | Variable | Período | Archivo | Frecuencia |
|---|---|---|---|---|
| Superintendencia de Compañías, Valores y Seguros (2026). Ranking de Compañías y balances. https://appscvsmovil.supercias.gob.ec/ranking/reporte.html | Balances de compañías atuneras de Manabí | 2010–2025 | `data/raw/supercias/panel_variables_clave.csv` (+ formato largo, no versionado) | Anual |
| Thai Union Group PCL, Investor Relations. https://investor.thaiunion.com/en/financial-info/raw-material-price-trend | Frozen Whole Skipjack, Bangkok landings WPO (USD/t) | ene-2011 a sep-2026 | `data/external/precio_atun_bangkok_skipjack_2011_2026.csv` | Mensual |
| NOAA Climate Prediction Center. https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt | ONI: anomalía SST Niño 3.4 (°C), media móvil de 3 meses | ene-2010 a ago-2026 (JAS) | `data/external/oni_noaa_2010_2026.csv` | Mensual |

## Base atunera Manabí (SUPERCIAS)
- **Universo:** 378 compañías con domicilio en Manta, Montecristi o Jaramijó y CIIU A0311 (pesca marítima / armadores) o C1020 (elaboración y conservación de pescado). 336 tienen al menos un balance 2010–2025.
- **Consolidación:** script `consolidar_base_atunera.py` (fuera de este repo). Decodifica cada `balances_AAAA_k.txt` con su catálogo; hay dos formularios (NIIF jerárquico y casilleros 101) **no comparables** código a código.
- **Costo de ventas por formulario:** NIIF `501`/`51` "Costo de ventas y producción"; casilleros 2010–2011 `797` "Total costos"; casilleros 2014–2021 `7991` "Total costos (operativos)".
- **Limitaciones:** ubicación según el directorio actual (no histórica); 2014 sin total de costos ni utilidad antes de IR para la mayoría; ~30% de empresa-año con ingresos cero (excluidas); el CIIU incluye algunas empresas no estrictamente atuneras.

## Clasificación ENSO
El Niño: ONI ≥ +0,5 · La Niña: ONI ≤ −0,5 · Neutro: entre ambos. Cada estación trimestral se asigna a su mes central (DJF → enero).
