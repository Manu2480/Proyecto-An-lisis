"""
generate_large_tpms.py
======================
Genera TPMs en formato estado-nodo (2^n x n) para n = 23, 24, 25.
Ejecutar en la máquina local donde estén los samples del proyecto.

Uso:
    python generate_large_tpms.py --output GeoMIP/data/samples/
    python generate_large_tpms.py --n 23 --variants AB --output ./samples/

Requisitos:
    pip install numpy

Memoria necesaria (float32):
    n=23 → ~800 MB RAM
    n=24 → ~1.6 GB RAM
    n=25 → ~3.2 GB RAM
"""

import numpy as np
import argparse
import os
import time

SEEDS = {'A': 42, 'B': 137, 'C': 999}

def generate_tpm(n: int, seed: int = 42, k_inputs: int = 3) -> np.ndarray:
    """
    Genera TPM determinista en formato estado-nodo (2^n x n).
    
    Modelo: red booleana aleatoria con k_inputs entradas por nodo.
    Formato idéntico al de los archivos N*A/B.csv del dataset del proyecto.
    
    Args:
        n: número de nodos
        seed: semilla para reproducibilidad
        k_inputs: entradas por nodo (default 3, igual que redes biológicas)
    
    Returns:
        numpy array float32 de shape (2^n, n)
        Cada entry [i,j] = P(nodo_j=1 | estado=i) ∈ {0.0, 1.0}
    """
    rng = np.random.default_rng(seed)
    states = 2 ** n
    tpm = np.zeros((states, n), dtype=np.float32)
    state_indices = np.arange(states, dtype=np.int64)

    for j in range(n):
        n_in = min(k_inputs, n)
        inputs = rng.choice(n, size=n_in, replace=False)
        truth_table = rng.integers(0, 2, size=2**n_in, dtype=np.uint8)
        tt_idx = np.zeros(states, dtype=np.int32)
        for pos, inp in enumerate(inputs):
            tt_idx |= ((state_indices >> inp) & 1).astype(np.int32) << pos
        tpm[:, j] = truth_table[tt_idx]

    return tpm


def save_csv_chunked(tpm: np.ndarray, filepath: str, chunk_size: int = 100_000):
    """Escribe el CSV en bloques para no pegar picos de memoria adicionales."""
    os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
    with open(filepath, 'w', buffering=1 << 20) as f:
        for start in range(0, len(tpm), chunk_size):
            chunk = tpm[start:start + chunk_size]
            lines = [','.join(f'{v:.1f}' for v in row) for row in chunk]
            f.write('\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser(description='Generador de TPMs grandes')
    parser.add_argument('--n', type=int, nargs='+', default=[23, 24, 25])
    parser.add_argument('--variants', type=str, default='AB',
                        help='Letras de variante, ej: AB o ABC')
    parser.add_argument('--k_inputs', type=int, default=3)
    parser.add_argument('--output', type=str, default='.')
    args = parser.parse_args()

    for n in args.n:
        states = 2 ** n
        ram_gb = states * n * 4 / 1e9  # float32
        print(f"\n{'='*50}")
        print(f"n={n}: {states:,} estados, RAM estimada ≈ {ram_gb:.2f} GB")

        for v in args.variants.upper():
            if v not in SEEDS:
                print(f"  Variante '{v}' no soportada (usar A, B o C)")
                continue

            fname = f"N{n}{v}.csv"
            fpath = os.path.join(args.output, fname)

            if os.path.exists(fpath):
                print(f"  {fname}: ya existe, saltando.")
                continue

            print(f"  Generando {fname}...", end=' ', flush=True)
            t0 = time.perf_counter()
            tpm = generate_tpm(n, seed=SEEDS[v], k_inputs=args.k_inputs)
            t1 = time.perf_counter()
            print(f"gen={t1-t0:.1f}s, guardando...", end=' ', flush=True)

            save_csv_chunked(tpm, fpath)
            t2 = time.perf_counter()
            size_mb = os.path.getsize(fpath) / 1e6
            zeros = np.mean(tpm == 0) * 100
            del tpm

            print(f"save={t2-t1:.1f}s | {size_mb:.0f} MB | {zeros:.1f}% ceros ✓")

    print("\nListo. Copiar los .csv a GeoMIP/data/samples/")


if __name__ == '__main__':
    main()
