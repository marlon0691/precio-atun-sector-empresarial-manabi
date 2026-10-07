# Precio del atún, El Niño y sector empresarial atunero de Manabí (2011–2025)

**Análisis econométrico de 230 empresas de Manta, Montecristi y Jaramijó**, con balances SUPERCIAS, precio *skipjack* Bangkok (Thai Union) e índice ONI (NOAA). Se sigue el framework **Ask → Prepare → Process → Analyze → Share → Act**.

> Autor: Marlon Andrade Ortega, economista y consultor en finanzas corporativas (Quito, Ecuador). Licencia MIT.

---

## Abstract (EN)
Using 1,692 firm-year observations (230 tuna firms in Manabí, Ecuador, 2011–2025), monthly Bangkok skipjack prices (2011-01 to 2026-09) and NOAA's ONI, we find that **(i)** fishing-fleet profitability is highly price-elastic: +USD 100/t raises the fleet's aggregate operating margin by ~1.0 pp (R² 0.74). The fleet breaks even near **USD 1,340/t**. **(ii)** Processors are *not* hurt by high price **levels**, since they pass costs through. They are hurt by **fast price increases**: each +10% annual rise cuts their gross margin by ~0.7 pp. **(iii)** Contrary to the scarcity hypothesis, **El Niño is associated with *lower* Bangkok prices**, about USD 430/t below La Niña 7 months later (HAC p<0.001). This fits Lehodey et al. (1997), where the stock is redistributed rather than depleted. However, ONI does not Granger-cause prices: it signals a regime, not a month-ahead forecast. The fleet and the processors face opposite risks. The recommended hedge is a **bilateral price-band (floor/cap) supply contract** between them.

---

**Dashboard interactivo:** `dashboard/dashboard_ejecutivo.html` (abre en cualquier navegador) · versión publicada en Claude: https://claude.ai/artifact/DNhaeWaFoARc41XroUxxcV

## Resumen ejecutivo para gerentes

| # | Pregunta | Respuesta corta | Evidencia |
|---|---|---|---|
| 1 | **Rezago óptimo ONI → precio Bangkok** | **7 meses** (correlación −0,39). La señal es de *régimen*, no un pronóstico mes a mes | CCF; Granger no significativo (p mín 0,17); la correlación pre-blanqueada ≈ 0 |
| 2 | **Precio de quiebre** | **Flota: USD 1.340/t** (IC95 1.210–1.460). **Plantas:** su margen operativo agregado nunca fue negativo en 2011–2025; no hay quiebre dentro del rango observado | Regresión del margen operativo agregado sobre el precio (HAC) |
| 3 | **Sensibilidad a +USD 100/t** | Flota: **+0,98 pp** de margen operativo (IC95 0,66–1,31). Plantas: **+0,30 pp** (IC95 0,05–0,55) | Serie agregada 2011–2025 |
| 3b | **Sensibilidad de las plantas a la *velocidad*** | Cada **+10% de alza anual** → **−0,68 pp de margen bruto** (IC95 −1,11 a −0,25; p=0,002) | Panel con efectos fijos de empresa y errores Driscoll-Kraay |
| 4 | **El Niño vs. La Niña** | Tras El Niño la tonelada vale **USD 434 menos** (7 meses: USD 1.324 vs. 1.758; IC95 HAC −667 a −201; p<0,001) | ANOVA, Kruskal-Wallis, Welch, Tukey, HAC |
| 5 | **Cobertura #1 para plantas** | **Contrato de suministro con banda de precio (piso/techo) con armadores**, indexado al Bangkok skipjack | Las dos partes tienen riesgos opuestos y se compensan |
| 6 | **Cobertura** | **288 empresas** en el dataset maestro (2.086 obs., 2010–2025); **230 empresas / 1.692 obs.** en la econometría (53 plantas, 177 pesqueras), 2011–2025; 188 meses de precio y ONI | |

### Lo que cambia respecto de la hipótesis inicial
El protocolo suponía que **El Niño → escasez en el Pacífico occidental → precio Bangkok ↑**. En 2011–2026 los datos dicen lo **contrario**:

| | Hipótesis inicial | Lo que muestran los datos |
|---|---|---|
| El Niño y precio Bangkok | ↑ | **↓** (≈ −USD 300/t frente a neutro; −USD 434/t frente a La Niña) |
| Armadores durante El Niño | "doble beneficio" | **Riesgo**: precio bajo y margen menor. Correlación del ONI anual con el margen operativo de la flota: **−0,67** (p<0,01). Los años de pérdida agregada fueron **2015 y 2019**, ambos El Niño con precio < USD 1.250 |
| Plantas durante El Niño | pérdida | Materia prima **más barata**; el margen operativo se mantiene positivo |
| Plantas: precio alto | margen ↓ | **No** en niveles (traslado de costos). **Sí** cuando el precio **sube rápido** |

Es consistente con **Lehodey et al. (1997)**: El Niño *redistribuye* el barrilete hacia el este, no lo hace escasear. También con **Ormaza-González et al. (2016)**: la relación es no lineal (R² con ONI de 0,18 en su estudio y de 0,16–0,22 en este).

### ⚠️ Situación actual (octubre 2026)
- El ONI de jul–sep 2026 está en **+2,16**, un El Niño fuerte comparable a 2015 (+2,6) y 2023 (+2,0).
- El precio no ha seguido el patrón: **USD 2.275/t en septiembre de 2026**. El patrón histórico apunta a **≈ USD 1.370/t hacia marzo de 2027**, con un intervalo de predicción al 95% muy amplio (USD 790–1.950). El precio actual ya está **por encima** de ese intervalo.
- Lectura: 2026 es atípico y puede haber factores no climáticos detrás (demanda, flota, regulación). Hou et al. (2022) advierten que la relación ENSO–atún es **no estacionaria**.
- **Plantas:** el promedio 2026 a septiembre (≈ USD 1.846/t) es **+17% vs. 2025**. Por el efecto velocidad, eso implica ≈ **−1,2 pp de margen bruto** este año.
- **Flota:** si el patrón histórico reaparece en 2027, el precio podría acercarse al equilibrio de ~USD 1.340/t. Es momento de **asegurar un piso**.

---

## Metodología

### Datos
| Fuente | Contenido | Período |
|---|---|---|
| SUPERCIAS (Superintendencia de Compañías, Valores y Seguros, 2026) | Balances de 336 compañías CIIU A0311 / C1020 de Manta, Montecristi y Jaramijó | 2010–2025 |
| Thai Union IR | Frozen Whole Skipjack, Bangkok landings WPO (USD/t) | 2011-01 a 2026-09 |
| NOAA CPC | ONI (Niño 3.4, media móvil de 3 meses) | 2010-01 a 2026-08 |

Detalle en [`references/fuentes_datos.md`](references/fuentes_datos.md).

### Decisiones clave (auditables en `outputs/tables/log_limpieza_datos.txt`)
1. **Costo de ventas mapeado por formulario** (NIIF `501/51`; casilleros `797` y `7991`). Los códigos no son comparables entre formularios.
2. **Empresas inactivas excluidas** (sin activos o sin ingresos: 897 de 2.983 empresa-año, 30,1%).
3. **2014 excluido** de los márgenes bruto y operativo: menos del 10% de las empresas reporta esas cuentas en ese formulario.
4. **No se imputan ratios.** Los outliers se marcan; para estimar, los ratios se acotan a [−1, 1] y se exigen ingresos ≥ USD 100 mil.
5. **Sin efectos fijos de año:** el precio anual es común a todas las empresas y sería perfectamente colineal. Se usan efectos fijos de **empresa** y errores **Driscoll-Kraay**. El efecto precio se identifica con ~15 años, así que la serie agregada (ponderada por ingresos, errores HAC) se reporta en paralelo.
6. **Series mensuales con errores HAC** (Newey-West, 12 rezagos). La CCF se reporta bruta y **pre-blanqueada** (filtro AR(3) del ONI).
7. El IPC del protocolo se usa solo para montos en USD constantes. Los ratios no se deflactan. **Pendiente: validar el IPC contra la serie oficial del INEC.**

### Q1 — Precio ↔ desempeño
- **Pesqueras (H1b confirmada):** margen bruto, operativo, neto, ROA y ROE suben con el precio (p<0,01 en la serie agregada). Las ventas crecen +4,9% por cada +10% de precio.
- **Manufactureras (H1a rechazada en niveles):** en la serie agregada, margen operativo +0,30 pp, ROA +0,46 pp y ROE +0,95 pp por cada USD 100/t. El **efecto velocidad** es negativo y significativo tanto en el panel (margen bruto −0,68 pp por +10%) como en la serie agregada (margen operativo −0,43 pp; ROE −1,09 pp).
- **Asimetría formal:** la sensibilidad de las pesqueras supera a la de las plantas en +0,75 pp por cada USD 100 (interacción, p<0,001).

### Q2 — El Niño ↔ precio
- **ANOVA** F=30,3 y **Kruskal-Wallis** H=47,7 (ambos p<0,001) con rezago de 7 meses. Tukey HSD en `outputs/tables/q2_tukey_hsd.txt`.
- **No linealidad:** el término ONI² es significativo con rezagos ≥ 10 meses. El precio mínimo ocurre con ONI ≈ +1,1 °C y repunta en los extremos.
- **Granger:** no significativo en niveles ni en Δlog (p ≥ 0,17). El ONI no añade poder predictivo de corto plazo una vez considerada la inercia del precio. ADF: el precio es casi estacionario (p=0,07) y el ONI estacionario (p=0,04).

### Q3 — Pérdidas potenciales
| Escenario (USD/t) | Flota: margen op. esperado | % de empresas de la flota en pérdida | Plantas: margen op. esperado | Impacto en la flota vs. 2025 |
|---|---|---|---|---|
| 900 (mín. oct-2019) | −4,3% | 74% | +2,2% | −USD 74 M |
| 1.100 (El Niño 2015) | −2,3% | 68% | +2,8% | −USD 52 M |
| 1.573 (prom. 2025) | +2,3% | 16% | +4,3% | — |
| 2.300 (pico 2017 / sep-2026) | +9,5% | 8% | +6,5% | +USD 80 M |

- **VaR 95% del margen operativo (empresa-año):** plantas −2,7%; flota −17,7%. La flota tiene una cola mucho más pesada.
- **Plantas, shock de velocidad:** un alza de +30% en el año equivale a ≈ −2,0 pp de margen bruto, unos **−USD 27 M** sobre las ventas de 2025.

Todas las tablas están en [`outputs/tables/`](outputs/tables) y los hallazgos en formato máquina en `outputs/tables/hallazgos_clave.json`.

---

## Act — Opciones de cobertura

### Marco regulatorio y de mercado
- **No hay un contrato de futuros líquido y listado para atún skipjack** (CME y SGX no lo ofrecen). La cobertura es bilateral (OTC) u operativa.
- **Resolución JPRFM-2026-009-M (6-mar-2026):** el BCE actúa como agente para coberturas de commodities con derivados internacionales, pero **solo para empresas públicas nacionales**, con garantías líquidas y sin garantía del BCE. **No aplica a empresas privadas atuneras.**
- Los derivados OTC con bancos internacionales exigen líneas de crédito y documentación ISDA. Solo son realistas para exportadores grandes.

### Matriz de opciones
| Instrumento | Viabilidad en Ecuador | Costo | Complejidad | Para quién |
|---|---|---|---|---|
| **Contrato con banda de precio planta–armador** (piso/techo indexado a Bangkok) | ⭐⭐⭐ Alta | Nulo | Baja | **Plantas y flota (cobertura natural)** |
| Forward de precio fijo con proveedor | ⭐⭐⭐ Alta | Bajo | Baja | Plantas |
| Compra escalonada guiada por el ONI | ⭐⭐⭐ Alta | Nulo | Baja | Plantas |
| Cláusulas de reajuste en contratos de venta (UE/EE.UU.) | ⭐⭐ Media | Bajo | Media | Plantas: atacan el efecto velocidad |
| Integración vertical (planta + barco) | ⭐⭐ Media | Alto | Alta | Grupos grandes |
| Opciones OTC con bancos internacionales | ⭐ Baja | Alto | Muy alta | Exportadores con más de USD 10 M |
| Futuros listados de atún | ✖ No existen | — | — | — |
| Servicio de coberturas del BCE | ✖ Solo empresas públicas | — | — | — |

### Recomendación #1 — contrato de banda de precio
La **flota** pierde cuando el precio cae bajo ~USD 1.340/t. Las **plantas** sufren cuando el precio **sube rápido**. Un contrato anual con **piso ≈ USD 1.350** y **techo ≈ USD 1.900–2.000**, liquidado mensualmente contra el precio Bangkok publicado por Thai Union, reduce la cola de ambos. No requiere mercado de derivados.

### Protocolo de alerta ONI (revisado con la evidencia)
| Señal ONI (NOAA, mensual) | Patrón histórico del precio | Armadores | Plantas |
|---|---|---|---|
| ≥ +0,5 dos meses seguidos | Tiende a **bajar** en 6–9 meses | Negociar el **piso** ahora | No sobre-comprar; escalonar |
| ≥ +1,0 | Promedio tras El Niño ≈ USD 1.320/t | Piso cerca del equilibrio | Comprar en tramos a precios en descenso |
| ≤ −0,5 | Tiende a **subir** (≈ USD 1.760/t) | Capturar el precio alto | **Asegurar techo antes** del alza |
| Precio fuera del rango del modelo (como 2026) | Patrón roto | Prudencia, sin apalancarse en precio alto | Vigilar el ritmo de alza mensual |

ONI en tiempo real: https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/

---

## Limitaciones
- El precio Bangkok (Pacífico occidental) es un proxy. Las plantas de Manta compran sobre todo pesca del Pacífico oriental y precios locales; la correlación es alta, pero no es la misma serie.
- Con ~15 años, la identificación del efecto precio es de **series cortas**. Los IC son amplios y los quiebres fuera del rango observado no son interpretables (p. ej., el quiebre de las plantas).
- Las asociaciones ONI–precio son correlacionales; Granger no confirma precedencia predictiva.
- La ubicación de las empresas viene del directorio actual y el filtro CIIU incluye algunas empresas no estrictamente atuneras.

## Reproducir
```bash
pip install -r requirements.txt
python -m src.data_loader        # Prepare/Process → data/processed/dataset_maestro_manabi.parquet
python -m src.analysis           # Q1–Q3 → outputs/tables/
python -m src.visualization      # figuras → outputs/figures/
python -m src.build_notebooks    # genera y ejecuta notebooks/01–07
```
`data/raw/supercias/balances_largo.parquet` (34 MB) no se versiona. Se regenera con `consolidar_base_atunera.py` desde los balances SUPERCIAS.

## Estructura
```
├── README.md · LICENSE · requirements.txt · .gitignore
├── references/   literatura_cientifica.md · fuentes_datos.md
├── notebooks/    01_ask … 07_share_act (ejecutados)
├── src/          data_loader · analysis · visualization · price_fetcher · oni_fetcher · build_notebooks
├── data/         raw/supercias · processed/dataset_maestro_manabi.(parquet|csv) · external/(precio, ONI)
├── dashboard/    dashboard_ejecutivo.html
└── outputs/      figures/ (PNG 300 dpi + SVG) · tables/ (CSV, JSON ROCC, log de limpieza)
```

## Referencias
1. Lehodey, P., Bertignac, M., Hampton, J., Lewis, A. & Picaut, J. (1997). El Niño Southern Oscillation and tuna in the western Pacific. *Nature*, 389, 715–718. https://doi.org/10.1038/39575
2. Ormaza-González, F.I., Mora-Cervetto, A. & Bermúdez-Martínez, R.M. (2016). Relationships between tuna catch and variable frequency oceanographic conditions. *Advances in Geosciences*, 42, 83–90. https://doi.org/10.5194/adgeo-42-83-2016
3. Kim, J., Na, H., Park, Y.-G. & Kim, Y.H. (2020). Potential predictability of skipjack tuna catches in the Western Central Pacific. *Scientific Reports*, 10, 3193. https://doi.org/10.1038/s41598-020-59947-8
4. Hou, X., Ma, S., Tian, Y. & Zhang, S. (2022). The Effects of Trans-Basin Climate Variability on Skipjack Tuna in the Northwest Pacific Ocean: Causal and Nonstationary. *Frontiers in Marine Science*, 9, 895219. https://doi.org/10.3389/fmars.2022.895219
5. Cámara Nacional de Pesquería del Ecuador / Primicias (2023). El Niño comienza a impactar en la industria pesquera de Ecuador. https://primicias.ec/noticias/economia/fenomeno-elnino-impacto-pesca-ecuador
6. Superintendencia de Compañías, Valores y Seguros. (06 de 10 de 2026). Ranking de Compañías. https://appscvsmovil.supercias.gob.ec/ranking/reporte.html
7. Thai Union Group PCL. Raw material price trend. https://investor.thaiunion.com/en/financial-info/raw-material-price-trend
8. NOAA Climate Prediction Center. Oceanic Niño Index. https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
9. Junta de Política y Regulación Financiera y Monetaria (2026). Resolución JPRFM-2026-009-M. https://asobanca.org.ec/wp-content/uploads/2026/03/JPRFM-2026-009-M-Servicio-agencia-fiscal-y-financiera-BCE-coberturas-commodities.pdf
