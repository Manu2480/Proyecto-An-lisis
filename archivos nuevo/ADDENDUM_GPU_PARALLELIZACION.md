# ADDENDUM — Paralelización CPU y Aceleración GPU
## Complemento al PROMPT_PROYECTO_KQMIP.md

---

## CONTEXTO

Este addendum añade una **Fase 4B** al plan de acción original. Aplica
**después** de que el benchmark base (Fase 3) haya identificado los cuellos
de botella reales. No implementar antes — optimizar sin medir es trabajo perdido.

---

## ANÁLISIS DE PARALELIZABILIDAD POR COMPONENTE

| Componente | GPU útil | CPU multicore | Motivo |
|---|---|---|---|
| Generación de TPMs | ✓ MUY | ✓ MUY | Ops matriciales independientes |
| Distancias Hamming | ✓ MUY | ✓ MUCHO | Bitops vectorizables sobre 2^n pares |
| Tabla de costos T | ✓ MUCHO | ✓ MUCHO | Variables v independientes entre sí |
| BFS recursivo (tabla T) | ✗ NO | ✗ NO | Dependencias de datos entre niveles |
| EMD (pyemd actual) | ✗ NO | ✗ NO | Librería CPU-only y secuencial |
| EMD con POT | ✓ SÍ | — | Reemplaza pyemd con soporte GPU |
| Clustering k-partición | ✓ ALGO | ✓ ALGO | cuML/sklearn paralelo |
| Evaluación batch filas | — | ✓ MUY | Filas del Excel son independientes |

---

## FASE 4B — IMPLEMENTACIÓN

### 4B.1 CPU Multicore (implementar primero, sin dependencias nuevas)

El cálculo de `T[v, i, j]` para cada variable `v` es completamente
independiente. Paralelizar con `ProcessPoolExecutor`:

```python
# src/controllers/strategies/geometric.py

from concurrent.futures import ProcessPoolExecutor
from os import cpu_count

def calcular_tabla_completa(self, tensors: dict) -> dict:
    """
    Calcula la tabla de costos T para todas las variables en paralelo.
    Cada variable se procesa en un proceso hijo independiente.
    """
    variables = list(tensors.keys())
    
    with ProcessPoolExecutor(max_workers=cpu_count()) as pool:
        resultados = pool.map(
            calcular_tabla_variable,          # función standalone (picklable)
            variables,
            [tensors[v] for v in variables],
            [self.n] * len(variables)
        )
    
    return {v: tabla for v, tabla in zip(variables, resultados)}


def calcular_tabla_variable(variable, tensor, n):
    """
    Standalone (fuera de la clase) para ser picklable por ProcessPoolExecutor.
    Calcula T[i,j] para todos los pares de estados para UNA variable.
    """
    states = 2**n
    T = {}
    state_indices = list(range(states))
    
    for i in state_indices:
        for j in state_indices:
            T[(i, j)] = _costo_transicion(i, j, tensor, n, memo={})
    
    return T
```

**Speedup esperado: ×n_cores** (lineal con núcleos disponibles).

---

### 4B.2 Reemplazar pyemd → POT para soporte GPU

`pyemd` no tiene soporte GPU. Reemplazarlo con
[POT (Python Optimal Transport)](https://pythonot.github.io/):

```bash
pip install POT
```

```python
# src/funcs/base.py  (o iit.py según la rama)

import ot
import numpy as np

# ── CPU (drop-in replacement de pyemd) ──────────────────────────
def emd_cpu(u: np.ndarray, v: np.ndarray, cost_matrix: np.ndarray) -> float:
    """Reemplaza emd() de pyemd. Misma firma, misma semántica."""
    return ot.emd2(u, v, cost_matrix)


# ── GPU (requiere PyTorch + CUDA) ────────────────────────────────
def emd_gpu(u: np.ndarray, v: np.ndarray, cost_matrix: np.ndarray) -> float:
    """
    EMD en GPU via POT + PyTorch.
    Solo se llama si torch.cuda.is_available() == True.
    """
    import torch
    device = 'cuda'
    u_t  = torch.tensor(u,           dtype=torch.float64, device=device)
    v_t  = torch.tensor(v,           dtype=torch.float64, device=device)
    M_t  = torch.tensor(cost_matrix, dtype=torch.float64, device=device)
    return float(ot.emd2(u_t, v_t, M_t))


# ── Selector automático ──────────────────────────────────────────
def emd_auto(u, v, cost_matrix) -> float:
    """Usa GPU si está disponible, CPU si no."""
    try:
        import torch
        if torch.cuda.is_available():
            return emd_gpu(u, v, cost_matrix)
    except ImportError:
        pass
    return emd_cpu(u, v, cost_matrix)
```

Reemplazar **todas** las llamadas a `emd()` de pyemd por `emd_auto()`.

---

### 4B.3 Distancias Hamming vectorizadas (CuPy / NumPy)

```python
# src/funcs/hamming.py  (módulo nuevo)

import numpy as np

def hamming_desde_estado(estado_i: int, n: int,
                          use_gpu: bool = False) -> np.ndarray:
    """
    Calcula dH(estado_i, j) para todos los j en {0, ..., 2^n - 1}.
    Devuelve array de shape (2^n,) con las distancias.
    """
    states = np.arange(2**n, dtype=np.int32)
    xor    = np.bitwise_xor(estado_i, states)

    if use_gpu:
        try:
            import cupy as cp
            xor_gpu = cp.array(xor)
            # popcount vectorizado en GPU
            bits = cp.unpackbits(
                xor_gpu.view(cp.uint8)
            ).reshape(-1, 32)[:, -n:]
            return cp.asnumpy(bits.sum(axis=1))
        except ImportError:
            pass  # fallback a CPU

    # CPU: popcount via lookup table (rápido)
    bits = np.unpackbits(
        xor.view(np.uint8)
    ).reshape(-1, 32)[:, -n:]
    return bits.sum(axis=1).astype(np.int32)


def matriz_hamming_completa(n: int, use_gpu: bool = False) -> np.ndarray:
    """
    Calcula la matriz completa de distancias Hamming (2^n x 2^n).
    ADVERTENCIA: solo viable para n ≤ 15 en RAM. Para n > 15, usar
    hamming_desde_estado() fila a fila dentro del BFS.
    """
    states = 2**n
    if use_gpu:
        try:
            import cupy as cp
            idx = cp.arange(states, dtype=cp.int32)
            # Broadcasting: xor[i,j] = i XOR j
            xor = cp.bitwise_xor(idx[:, None], idx[None, :])
            bits = cp.unpackbits(
                xor.ravel().view(cp.uint8)
            ).reshape(states * states, 32)[:, -n:]
            return cp.asnumpy(bits.sum(axis=1).reshape(states, states))
        except ImportError:
            pass
    
    # CPU
    idx  = np.arange(states, dtype=np.int32)
    xor  = np.bitwise_xor(idx[:, None], idx[None, :])
    bits = np.unpackbits(xor.ravel().view(np.uint8)).reshape(-1, 32)[:, -n:]
    return bits.sum(axis=1).reshape(states, states).astype(np.int32)
```

---

### 4B.4 Clustering GPU para k-partición (cuML)

```python
# src/controllers/strategies/kpartition.py

def clustering_jerarquico(cost_matrix: np.ndarray, k: int,
                          use_gpu: bool = False):
    """
    Clustering jerárquico sobre la matriz de costos T para k-partición.
    Usa cuML en GPU si está disponible, scipy en CPU si no.
    """
    if use_gpu:
        try:
            from cuml.cluster import AgglomerativeClustering as GPUAgg
            model = GPUAgg(n_clusters=k, linkage='average')
            labels = model.fit_predict(cost_matrix)
            return labels
        except ImportError:
            pass
    
    # CPU fallback
    from scipy.cluster.hierarchy import linkage, fcluster
    Z      = linkage(cost_matrix, method='average')
    labels = fcluster(Z, k, criterion='maxclust')
    return labels
```

---

### 4B.5 Generación de TPMs grandes en paralelo

Para generar N23–N25 en la máquina local, usar el script incluido con
paralelización por variante:

```python
# Dentro de generate_large_tpms.py — modo paralelo
from concurrent.futures import ProcessPoolExecutor

configs = [(n, v, seed) for n in [23,24,25] for v, seed in SEEDS.items()]

with ProcessPoolExecutor(max_workers=2) as pool:  # 2 workers por RAM
    pool.map(generar_y_guardar, configs)
```

---

## DEPENDENCIAS NUEVAS

Añadir a `pyproject.toml` bajo `[project.optional-dependencies]`:

```toml
[project.optional-dependencies]
gpu = [
    "POT>=0.9",           # EMD con soporte GPU (reemplaza pyemd)
    "cupy-cuda12x>=13.0", # Arrays GPU (ajustar versión CUDA)
    "torch>=2.0",         # Backend para POT GPU
]
clustering-gpu = [
    "cuml-cu12>=24.0",    # AgglomerativeClustering GPU (RAPIDS)
]
```

Instalación:
```bash
uv sync --extra gpu            # solo GPU
uv sync --extra clustering-gpu # clustering GPU
uv sync                        # solo CPU (comportamiento actual sin cambios)
```

---

## BANDERA DE CONTROL GLOBAL

Agregar a `src/constants/config.py` (o equivalente):

```python
import torch

USE_GPU: bool = torch.cuda.is_available()   # False si no hay CUDA
N_WORKERS: int = os.cpu_count()             # Para ProcessPoolExecutor
GPU_MIN_N: int = 12   # Solo activar GPU para n >= este valor
                      # Para n pequeño, overhead GPU > ganancia
```

---

## SPEEDUP ESPERADO (estimación empírica)

| n  | CPU 1 core | CPU 8 cores | GPU (RTX 3060) |
|----|-----------|-------------|----------------|
| 15 | ~30s      | ~4s         | ~1s            |
| 20 | ~15min    | ~2min       | ~15s           |
| 22 | ~2h       | ~15min      | ~3min          |
| 25 | inviable  | ~8h         | ~45min         |

*Estimaciones aproximadas. El EMD domina el tiempo total.*

---

## ARCHIVOS GENERADOS PARA EL DATASET

Los siguientes archivos `.csv` han sido generados y están listos para
copiar a `GeoMIP/data/samples/`:

| Archivo | Nodos | Filas | Tamaño | Semilla |
|---------|-------|-------|--------|---------|
| N6A.csv  | 6  | 64        | <1 MB  | 42  |
| N6B.csv  | 6  | 64        | <1 MB  | 137 |
| N17A.csv | 17 | 131,072   | 9 MB   | 42  |
| N17B.csv | 17 | 131,072   | 9 MB   | 137 |
| N18A.csv | 18 | 262,144   | 19 MB  | 42  |
| N18B.csv | 18 | 262,144   | 19 MB  | 137 |
| N19A.csv | 19 | 524,288   | 40 MB  | 42  |
| N19B.csv | 19 | 524,288   | 40 MB  | 137 |
| N20A.csv | 20 | 1,048,576 | 84 MB  | 42  |
| N20B.csv | 20 | 1,048,576 | 84 MB  | 137 |
| N21A.csv | 21 | 2,097,152 | 176 MB | 42  |
| N21B.csv | 21 | 2,097,152 | 176 MB | 137 |
| N22A.csv | 22 | 4,194,304 | 369 MB | 42  |
| N22B.csv | 22 | 4,194,304 | 369 MB | 137 |

Para n=23, 24, 25: ejecutar `generate_large_tpms.py` localmente.
Ver instrucciones en el encabezado de ese script.

Formato de todos los archivos:
- Sin header
- Separador: coma
- Valores: 0.0 o 1.0 (red booleana determinista)
- Encoding: UTF-8, line endings Unix (\n)
- Igual al formato de N15B.csv del dataset original

