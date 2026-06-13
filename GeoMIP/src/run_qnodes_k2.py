"""
Ejecuta únicamente QNodes (bipartición, k=2) sobre la matriz DatosPruebas2026
para un tamaño de red n dado.

Uso (desde Method2_Dynamic_Programming_Reformulation):
  uv run python ../run_qnodes_k2.py --n 25
  uv run python ../run_qnodes_k2.py --n 25 --timeout 86400
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

BENCHMARK_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCHMARK_ROOT))
from geomip_paths import GEOMIP_ROOT, SAMPLES_DIR, RESULTS_DIR, METHOD2_ROOT  # noqa: E402

if str(METHOD2_ROOT) not in sys.path:
    sys.path.insert(0, str(METHOD2_ROOT))

from src.controllers.manager import Manager
from src.controllers.strategies.q_nodes import QNodes
from src.models.base.sia import limpiar_cache_subsistemas

# Reutilizar casos y utilidades del benchmark principal
sys.path.insert(0, str(BENCHMARK_ROOT))
from benchmark import (  # noqa: E402
    CASOS,
    letters_to_binary,
    run_strategy,
)

DEFAULT_TIMEOUT = 86400  # 24 h por caso (QNodes en n grande puede ser muy lento)


def load_tpm_csv(path: Path, n_nodes: int, dtype=np.float32) -> np.ndarray:
    """Carga TPM estado-nodo sin genfromtxt (evita MemoryError en n>=25).

    genfromtxt materializa listas Python intermedias (~2-3× la RAM final).
    Aquí se pre-asigna el arreglo y se lee línea a línea en float32 (~3.4 GB para n=25).
    """
    n_rows = 2**n_nodes
    tpm = np.empty((n_rows, n_nodes), dtype=dtype)
    report_every = max(1, n_rows // 20)

    loaded = 0
    with open(path, encoding="utf-8", buffering=8 * 1024 * 1024) as f:
        for line in f:
            if loaded >= n_rows:
                raise ValueError(
                    f"{path.name}: más de {n_rows:,} filas (esperadas para n={n_nodes})"
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


def _carpeta_n(n: int) -> Path:
    p = RESULTS_DIR / f"n{n}"
    p.mkdir(parents=True, exist_ok=True)
    return p


def run_qnodes_k2(n: int, timeout: int) -> pd.DataFrame:
    os.environ.setdefault("KQGMIP_QUIET", "1")

    if n not in CASOS:
        raise SystemExit(f"[ERROR] n={n}: sin casos en DatosPruebas2026")

    n_val, estado, pares = CASOS[n]()

    tpm_path = None
    for suf in ("A", "B", "C"):
        p = SAMPLES_DIR / f"N{n}{suf}.csv"
        if p.exists():
            tpm_path = p
            break
    if tpm_path is None:
        raise SystemExit(
            f"[ERROR] Falta TPM N{n}A/B/C en {SAMPLES_DIR}. "
            f"Generar con: python GeoMIP/data/generate_large_tpms.py --n {n} --output samples/"
        )

    print(f"QNodes k=2 — n={n}  TPM={tpm_path.name}  casos={len(pares)}  timeout={timeout}s")
    print(f"Cargando TPM ({tpm_path.stat().st_size / 1e6:.0f} MB en disco, float32)...", flush=True)
    tpm = load_tpm_csv(tpm_path, n_val)
    ram_mb = tpm.nbytes / 1e6
    print(f"TPM en memoria: shape={tpm.shape}  dtype={tpm.dtype}  ~{ram_mb:.0f} MB", flush=True)

    rows = []
    for idx, (purview, mec_str) in enumerate(pares, 1):
        alcance = letters_to_binary(purview, n_val)
        mecanismo = letters_to_binary(mec_str, n_val)
        condicion = "1" * n_val

        print(f"  #{idx:>3}/{len(pares)}  {purview[:18]:<18} / {mec_str[:18]}", end="", flush=True)

        limpiar_cache_subsistemas()

        r = run_strategy(
            QNodes,
            {"gestor": Manager(estado_inicial=estado)},
            {},
            condicion,
            alcance,
            mecanismo,
            tpm,
            timeout,
        )

        row = {
            "#Prueba": idx,
            "Purview": purview,
            "Mecanismo": mec_str,
            "QN_k2_particion": r["particion"],
            "QN_k2_perdida": r["perdida"],
            "QN_k2_tiempo_ms": r["tiempo_ms"],
            "QN_k2_convergio": r["convergio"],
            "QN_k2_error": r["error"],
        }
        rows.append(row)
        print(f"  {'OK' if r['convergio'] else 'FAIL'}", flush=True)

        if idx % 5 == 0:
            ts = datetime.now().strftime("%Y-%m-%d_%Hh%M")
            out = _carpeta_n(n) / f"qnodes_k2_checkpoint_{ts}.xlsx"
            pd.DataFrame(rows).to_excel(out, index=False)
            print(f"    checkpoint → {out.name}", flush=True)

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description="QNodes k=2 — matriz DatosPruebas2026")
    parser.add_argument("--n", type=int, default=25, help="Tamaño de red (10,15,20,22,25)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help="Segundos máximos por caso")
    args = parser.parse_args()

    df = run_qnodes_k2(args.n, args.timeout)
    ts = datetime.now().strftime("%Y-%m-%d_%Hh%M")
    out = _carpeta_n(args.n) / f"qnodes_k2_n{args.n}_{ts}.xlsx"
    df.to_excel(out, index=False)
    ok = int(df["QN_k2_convergio"].sum())
    print(f"\nCompletado: {ok}/{len(df)} convergieron")
    print(f"Salida: {out}")


if __name__ == "__main__":
    main()
