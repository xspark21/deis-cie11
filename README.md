# DEIS-CIE11

Normalización de glosas operacionales del sistema de urgencias chileno (SADU/DEIS) hacia CIE-11.

El objetivo del proyecto es construir un puente reproducible entre las categorías
históricas usadas por DEIS y la estructura vigente de la OMS bajo CIE-11,
permitiendo trabajar series de urgencia con una codificación internacional consistente.

El repositorio contiene únicamente el pipeline de estandarización.  
El análisis epidemiológico y los datasets derivados viven en un repositorio separado.

## Qué genera

A partir del archivo oficial de CIE-11 MMS y un consolidado histórico de
urgencias DEIS (2019–2025), el pipeline produce tres tablas:

| Archivo | Descripción |
|---|---|
| `icd11_master.parquet` | Tabla maestra ICD-11 MMS (35.679 códigos codificables) |
| `deis_to_icd11_resolver.parquet` | Diccionario glosa DEIS → código CIE-11 |
| `emergency_care_curated.parquet` | Dataset curado con glosas normalizadas y mapeadas |

Cobertura observada sobre ~55M registros:

| Precisión semántica | Registros | % |
|---|---|---|
| Exacta | 30.201.941 | 54.3% |
| Agregada | 18.386.445 | 33.0% |
| Proxy | 7.071.379 | 12.7% |

## Criterio de mapeo

El resolver distingue tres niveles:

- **Exacta** → equivalencia clínica directa
- **Agregada** → el formulario SADU solo entrega nivel de capítulo o grupo
- **Proxy** → mejor aproximación disponible cuando no existe equivalencia uno a uno

Algunos diagnósticos cambian de capítulo entre CIE-10 y CIE-11.
Por ejemplo:

- ACV pasa desde circulatorio a neurológico
- Influenza pasa desde respiratorio a enfermedades infecciosas
- COVID-19 queda bajo “Codes for special purposes”

Esos casos quedan marcados mediante `riesgo_quiebre_serie`
para evitar comparaciones históricas incorrectas.

El detalle metodológico está documentado en `metodologia.md`.

## Uso

```bash
git clone https://github.com/xspark21/deis-cie11.git
cd deis-cie11

# para sincronizar las dependencias
uv sync
# pipeline completo
make build
```
O ejecutar cada etapa manualmente:
```bash
uv run src/ingestion/master.py
uv run src/ingestion/resolver.py
uv run src/ingestion/curator.py
```
## Requisitos
- Python ≥ 3.14
- uv
- Archivo OMS:
  `data/raw/LinearizationMiniOutput-MMS-en.xlsx`
- Dataset consolidado DEIS:
  `data/raw/urgencias_deis_2019_2025.parquet`
## Fuentes
- OMS — CIE-11 MMS Linearization: https://icd.who.int/browse/2024-01/mms
- DEIS — Atenciones de Urgencia: https://deis.minsal.cl/#datosabiertos
- Manual de Registro SADU v1.1 — DEIS, diciembre 2020