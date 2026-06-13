"""Carga eficiente de TPMs CSV (estado-nodo)."""
from __future__ import annotations

from pathlib import Path

import numpy as np


def load_tpm_csv(path: Path, n_nodes: int, dtype=np.float32) -> np.ndarray:
    """Lee linea a linea; evita MemoryError de genfromtxt en n>=25."""
    n_rows = 2**n_nodes
    tpm = np.empty((n_rows, n_nodes), dtype=dtype)
    report_every = max(1, n_rows // 20)
    loaded = 0

    with open(path, encoding="utf-8", buffering=8 * 1024 * 1024) as f:
        for line in f:
            if loaded >= n_rows:
                raise ValueError(
                    f"{path.name}: mas de {n_rows:,} filas (esperadas para n={n_nodes})"
                )
            row = np.fromstring(line.strip(), sep=",", dtype=dtype)
            if row.size != n_nodes:
                raise ValueError(
                    f"{path.name} fila {loaded + 1}: {row.size} columnas, esperadas {n_nodes}"
                )
            tpm[loaded] = row
            loaded += 1
            if loaded % report_every == 0 or loaded == n_rows:
                pct = 100 * loaded / n_rows
                print(
                    f"  TPM {pct:5.1f}%  ({loaded:,} / {n_rows:,} filas)",
                    flush=True,
                )

    if loaded != n_rows:
        raise ValueError(
            f"{path.name}: solo {loaded:,} filas, se esperaban {n_rows:,} para n={n_nodes}"
        )
    return tpm


def load_tpm(path: Path, n_nodes: int, stream_threshold: int = 21) -> np.ndarray:
    """float32 streaming para n grande; genfromtxt para n pequeno."""
    if n_nodes >= stream_threshold:
        print(f"  Cargando {path.name} (streaming float32)...", flush=True)
        return load_tpm_csv(path, n_nodes, dtype=np.float32)
    return np.asarray(np.genfromtxt(path, delimiter=","), dtype=np.float64)
