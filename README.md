# Proyecto K-QGMIP 2026-01

Extensión del repositorio base (QNodes + GeoMIP Method2) para **k-particiones**
(k = 3, 4, 5), manteniendo bipartición k = 2.

## Comparación con el repo base

| Aspecto | Repo base (`proyecto base/`) | Este repo |
|---------|------------------------------|-----------|
| Estrategias k=2 | `QNodes`, `GeometricSIA`, `BruteForce` | Igual en Method2 |
| k ≥ 3 | No implementado | `KPartitionSIA` (greedy, KL, clustering, MCTS) |
| Módulos GeoMIP | Solo Method2 | Method2 (canónico); Method3 eliminado (duplicado) |
| Datos | `.samples` locales | `GeoMIP/data/samples/` centralizado (N3–N25) |
| Benchmark | No | `benchmark.py` + `run_qnodes_k2.py` |
| Tests | No | `tests/` (pytest) |
| Resultados | — | `GeoMIP/data/results/` |

**Módulo de trabajo:** `GeoMIP/src/Method2_Dynamic_Programming_Reformulation/`  
`QNodes/` se conserva como referencia del código original (k=2); no duplicar lógica allí.

## Estrategias

| Clase (código) | Alias (enunciado) | k | Descripción |
|----------------|-------------------|---|-------------|
| `QNodes` | `KQNodes` | 2 | Heurística greedy de nodos |
| `GeometricSIA` | `KGeoMIP` | 2 | Programación dinámica geométrica |
| `KPartitionSIA` | — | 3–5 | Greedy + KL + clustering + MCTS |
| `BruteForce` | — | 2 | Exacto (solo validación, n pequeño) |

Todas heredan de `SIA` → `Manager` orquesta la estrategia elegida.

## Requisitos

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (`pip install uv`)

## Instalación

```powershell
cd GeoMIP/src/Method2_Dynamic_Programming_Reformulation
uv sync
```

## Ejecución

### Benchmark aproximado (KL + MC-EMD, mas rapido)

```powershell
cd GeoMIP/src/Method2_Dynamic_Programming_Reformulation
uv run python ../benchmark_aprox.py --n 10 15 20 22 25 --timeout 14400
```

Salida: `GeoMIP/data/results/aprox/` (Geo k=2 + KLmc k=3,4,5; sin QNodes ni greedy duplicado).

### Benchmark completo (DatosPruebas2026)

```powershell
cd GeoMIP/src/Method2_Dynamic_Programming_Reformulation
uv run python ../benchmark.py --n 10 15 --timeout 300
uv run python ../benchmark.py --n 20 22 25 --timeout 21600
```

Salida: `GeoMIP/data/results/n{n}/` (checkpoints) y `GeoMIP/data/results/benchmark_completo_*.xlsx`  
Logs n≥20: `GeoMIP/data/results/logs/n20_plus/`

### Solo QNodes k=2 (p. ej. n=25)

```powershell
uv run python ../run_qnodes_k2.py --n 25 --timeout 86400
```

### Batch Excel (GeometricSIA k=2)

```powershell
uv run exec.py
```

Entrada/salida por defecto: `GeoMIP/data/results/Pruebas_Metodo2.xlsx` → `resultados_Geometric.xlsx`

### Batch k-particiones (k=3,4,5)

```powershell
uv run python run_kpart.py
```

### Tests

```powershell
uv run pytest ../../../tests/ -v
```

### Validar TPMs

```powershell
uv run python ../../data/validate_tpms.py
```

## Estructura del repositorio

```
projecto-analisis-20261/
├── QNodes/                          # Código original (referencia k=2)
├── GeoMIP/
│   ├── data/
│   │   ├── samples/                 # TPMs *.csv
│   │   ├── results/                 # Excel, checkpoints, logs
│   │   ├── generate_large_tpms.py
│   │   └── validate_tpms.py
│   └── src/
│       ├── geomip_paths.py          # Rutas canónicas (única fuente)
│       ├── benchmark.py             # Benchmark DatosPruebas2026
│       ├── run_qnodes_k2.py         # QNodes k=2 por red
│       └── Method2_Dynamic_Programming_Reformulation/
│           ├── exec.py
│           ├── run_kpart.py
│           └── src/
│               ├── controllers/strategies/
│               │   ├── q_nodes.py      # QNodes / KQNodes
│               │   ├── geometric.py    # GeometricSIA / KGeoMIP
│               │   ├── kpartition.py   # KPartitionSIA
│               │   └── force.py        # BruteForce
│               └── models/base/sia.py
├── tests/
├── docs/
├── bitacoras/                       # Diario del proyecto (empezar por 00_indice.txt)
└── Información para el Proyecto/
```

## Rutas canónicas

Definidas en `GeoMIP/src/geomip_paths.py`:

- Muestras: `GeoMIP/data/samples/`
- Resultados: `GeoMIP/data/results/`
- Código: `GeoMIP/src/Method2_Dynamic_Programming_Reformulation/`

## Límites prácticos (CPU single-core)

| Estrategia | n práctico | Notas |
|------------|------------|-------|
| BruteForce | ≤ 6 | Solo validación |
| QNodes | ≤ 15 | Rápido; n=25 puede tardar horas en caso completo |
| GeometricSIA | ≤ 15 | DP; memoria O(2^n · n) |
| KPartitionSIA | ≤ 12–18 | Depende de heurística y subsistema |

Para n > 15 usar subsistemas parciales (alcance/mecanismo) según DatosPruebas2026.
