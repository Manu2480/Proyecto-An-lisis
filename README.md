# Proyecto K-QGMIP 2026-01

Implementaciones de System Irreducibility Analysis (SIA / IIT) para el
análisis de particiones mínimas (MIP) en redes de transición de estados.

## Estrategias implementadas

| Estrategia         | Módulo                    | Descripción                                    |
|--------------------|---------------------------|------------------------------------------------|
| `BruteForce`       | Method2 + QNodes          | Evalúa todas las biparticiones (exacto, O(2^n))|
| `QNodes`           | Method2 + QNodes          | Heurística greedy de nodos                     |
| `GeometricSIA`     | Method2 + Method3         | Programación dinámica (KGeoMIP, k=2)           |
| `KPartitionSIA`    | Method2                   | K-particiones greedy + clustering jerárquico   |

## Requisitos

- Python 3.11+
- `uv` instalado (`pip install uv`)
- Windows 10/11 o Linux (probado en ambos)

## Instalación

```bash
cd GeoMIP/src/Method2_Dynamic_Programming_Reformulation
uv sync
```

## Ejecución rápida

### Caso de prueba único (QNodes)

```bash
cd QNodes
uv sync
uv run exec.py
```

### Batch por Excel (Method2 — GeometricSIA + KPartition)

```bash
cd GeoMIP/src/Method2_Dynamic_Programming_Reformulation
uv run exec.py
```

Entrada: `GeoMIP/results/Pruebas_Metodo2.xlsx`  
Salida:  `GeoMIP/results/resultados_Geometric.xlsx`

### Benchmark completo

```bash
cd GeoMIP/src/Method2_Dynamic_Programming_Reformulation
uv run python ../../benchmark.py --n 20 22 25 --timeout 21600
```

Salida: `GeoMIP/results/benchmark_YYYY-MM-DD_HHhMM.xlsx`

`--timeout` es el **tope por estrategia y por caso** (segundos). Para n≥20 cada caso ejecuta **7 corridas** (Geométrica k=2 + Greedy/KL × k ∈ {3,4,5}) — sin `QNodes`. Conviene `--timeout ≥ 21600` (6 h) o más según máquina; ~5 h por corrida suele estar en ese rango si el caso es pesado. `find_mip()` se memoiza dentro del mismo caso tras la corrida Geométrica inicial.

```bash
cd GeoMIP/src/Method2_Dynamic_Programming_Reformulation
uv run python ../../benchmark.py --n 10 15 --timeout 300
```

Salida: `GeoMIP/results/benchmark_YYYY-MM-DD_HHhMM.xlsx`

### Suite de tests

```bash
cd GeoMIP/src/Method2_Dynamic_Programming_Reformulation
uv run pytest ../../../tests/ -v
```

### Validar TPMs

```bash
cd GeoMIP/src/Method2_Dynamic_Programming_Reformulation
uv run python ../../data/validate_tpms.py
```

## Datasets disponibles

| Archivo        | n  | Filas      | Tipo           |
|----------------|----|------------|----------------|
| N3A/B/C.csv    |  3 |          8 | bin / prob     |
| N4A/B/C.csv    |  4 |         16 | bin / prob     |
| N5A/B.csv      |  5 |         32 | binaria        |
| N6A/B/C.csv    |  6 |         64 | binaria        |
| N8A.csv        |  8 |        256 | binaria        |
| N10A.csv       | 10 |      1 024 | binaria        |
| N15A/B.csv     | 15 |     32 768 | probabilística |
| N17A/B.csv     | 17 |    131 072 | binaria        |
| N18A/B.csv     | 18 |    262 144 | binaria        |
| N19A/B.csv     | 19 |    524 288 | binaria        |
| N20A/B.csv     | 20 |  1 048 576 | binaria        |
| N21A/B.csv     | 21 |  2 097 152 | binaria        |
| N22A/B.csv     | 22 |  4 194 304 | binaria        |

Generación de n=23,24,25: `uv run python GeoMIP/data/generate_large_tpms.py`

## Límites prácticos (CPU single-core)

| Estrategia     | n práctico | n máximo teórico | Notas                                         |
|----------------|------------|------------------|-----------------------------------------------|
| BruteForce     | ≤ 6        | —                | Exponencial en n; solo para validación cruzada|
| QNodes         | ≤ 15       | ~20              | Greedy, rápido; no garantiza optimalidad      |
| GeometricSIA   | ≤ 15       | ~20              | DP sobre hipercubo; memoria O(2^n · n)        |
| KPartitionSIA  | ≤ 12       | ~18              | Agrega overhead del clustering por k          |

> Para n > 20 se recomienda reducir el subsistema (alcance/mecanismo parcial) o usar paralelismo
> (ver `ADDENDUM_GPU_PARALLELIZACION.md`).

## Estructura del repositorio

```
projecto-analisis-20261/
├── QNodes/                          # Implementación base (BruteForce + QNodes)
├── GeoMIP/
│   ├── data/
│   │   ├── samples/                 # TPMs *.csv
│   │   ├── generate_large_tpms.py   # Genera n=23,24,25
│   │   └── validate_tpms.py         # Validador de CSVs
│   ├── results/                     # Salidas Excel + benchmark
│   └── src/
│       ├── benchmark.py             # Benchmark completo
│       ├── Method2_Dynamic_Programming_Reformulation/
│       └── Method3_Batch_Processing/
├── tests/                           # Suite pytest (34 tests)
├── bitacoras/                       # Log de cambios por sesión
├── docs/                            # Manual técnico LaTeX
└── Información para el Proyecto/    # Guías del curso y especificaciones
```

## Nomenclatura

- **KGeoMIP**: estrategia GeometricSIA extendida a k particiones.
- **KQNodes**: estrategia QNodes extendida a k particiones.
- **SIA**: System Irreducibility Analysis (φ = EMD entre repertorio completo y partido).
- **MIP**: Minimum Information Partition.

## Historial de cambios relevantes

- `force.py` (Method2/3): corregido bug en llamada a `sia_preparar_subsistema` (faltaba `tpm`).
- `q_nodes.py` (Method2): mismo fix, acepta `tpm` opcional.
- `solution.py` (Method2/QNodes): añadidos campos `n_nodos`, `k`, propiedad `tiempo_ms`.
- `geometric.py` / `kpartition.py`: propagan `n_nodos` y `k` al construir `Solution`.
- `np.infty` → `np.inf` en `force.py` (NumPy 2.0).

