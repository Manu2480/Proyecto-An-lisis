"""
Benchmark aproximado K-QGMIP (KL + MC-EMD).

Mas rapido que benchmark.py:
  - k=2: solo GeometricSIA (find_mip cacheado)
  - k=3,4,5: solo KL_MC (Kernighan-Lin con evaluacion MC-EMD interna)
  - TPM float32 streaming para n>=21
  - Sin QNodes ni corrida greedy separada

Salida: GeoMIP/data/results/aprox/

Uso:
  cd GeoMIP/src/Method2_Dynamic_Programming_Reformulation
  uv run python ../benchmark_aprox.py --n 10 15
  uv run python ../benchmark_aprox.py --n 20 22 25 --timeout 14400
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BENCHMARK_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCHMARK_ROOT))

from geomip_paths import SAMPLES_DIR, RESULTS_DIR, METHOD2_ROOT  # noqa: E402
from tpm_io import load_tpm  # noqa: E402

if str(METHOD2_ROOT) not in sys.path:
    sys.path.insert(0, str(METHOD2_ROOT))

from benchmark import (  # noqa: E402
    CASOS,
    letters_to_binary,
    run_strategy,
    _install_large_n_logging,
    _uninstall_large_n_logging,
)
from src.controllers.manager import Manager  # noqa: E402
from src.controllers.strategies.geometric import GeometricSIA, limpiar_cache_find_mip  # noqa: E402
from src.controllers.strategies.kpartition import KPartitionSIA  # noqa: E402
from src.models.base.sia import limpiar_cache_subsistemas  # noqa: E402
from src.middlewares.profile import profiler_manager  # noqa: E402

profiler_manager.enabled = False

APPROX_DIR = RESULTS_DIR / "aprox"
APPROX_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_TIMEOUT = 7200


def heuristica_k_aprox(fila: dict) -> dict:
    base_p = fila.get("Geo_k2_perdida")
    base_t = fila.get("Geo_k2_tiempo_ms") or 1
    best_k, best_score = 2, -1.0

    for k in [3, 4, 5]:
        p = fila.get(f"KLmc_k{k}_perdida")
        t = fila.get(f"KLmc_k{k}_tiempo_ms") or 1
        if base_p is not None and p is not None:
            mejora = max(0, base_p - p)
            razon = mejora / (t / base_t) if t > 0 else 0
            if razon > best_score:
                best_score, best_k = razon, k

    return {
        "heuristica_k": best_k,
        "heuristica_estrategia": "KL_MC",
        "heuristica_score": round(best_score, 6),
    }


def _carpeta_n(n: int) -> Path:
    p = APPROX_DIR / f"n{n}"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _checkpoint(df: pd.DataFrame, n: int):
    ts = datetime.now().strftime("%Y-%m-%d_%Hh%M")
    path = _carpeta_n(n) / f"checkpoint_{ts}.xlsx"
    try:
        df.to_excel(path, index=False)
    except Exception:
        pass


def save_results_aprox(resultados: dict[int, pd.DataFrame]) -> Path:
    ts = datetime.now().strftime("%Y-%m-%d_%Hh%M")
    for n, df in sorted(resultados.items()):
        out_n = _carpeta_n(n) / f"n{n}_aprox_{ts}.xlsx"
        df.to_excel(out_n, index=False)
        print(f"  n={n} guardado en: {out_n}")

    out = APPROX_DIR / f"benchmark_aprox_{ts}.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as xw:
        for n, df in sorted(resultados.items()):
            df.to_excel(xw, sheet_name=f"n{n}", index=False)
        filas = []
        for n, df in sorted(resultados.items()):
            if "heuristica_k" in df.columns:
                dist = df["heuristica_k"].value_counts().to_dict()
                filas.append({"n": n, **{f"k={k}": dist.get(k, 0) for k in [2, 3, 4, 5]}})
        if filas:
            pd.DataFrame(filas).to_excel(xw, sheet_name="Heuristica_resumen", index=False)

    print(f"\nConsolidado aprox: {out}")
    return out


def mc_samples_para_red(n: int) -> int:
    if n <= 15:
        return -1
    if n <= 20:
        return 1500
    return 2500


def run_benchmark_aprox(ns: list[int], timeout: int) -> dict[int, pd.DataFrame]:
    os.environ.setdefault("KQGMIP_QUIET", "1")
    resultados = {}

    for n in ns:
        if n not in CASOS:
            print(f"[SKIP] n={n}: sin configuracion")
            continue

        n_val, estado, pares = CASOS[n]()
        tpm_path = None
        for suf in ["A", "B", "C"]:
            p = SAMPLES_DIR / f"N{n}{suf}.csv"
            if p.exists():
                tpm_path = p
                break
        if tpm_path is None:
            print(f"[SKIP] n={n}: sin TPM")
            continue

        if n <= 10:
            case_to = min(timeout, 600)
        elif n <= 15:
            case_to = min(timeout, 1200)
        else:
            case_to = min(timeout, 86400)

        n_mc = mc_samples_para_red(n)

        print(f"\n{'='*65}")
        print(
            f"[APROX] n={n}  TPM={tpm_path.name}  casos={len(pares)}"
            f"  timeout={case_to}s  mc_samples={n_mc}"
        )
        print(f"{'='*65}")

        tpm = load_tpm(tpm_path, n_val)
        rows = []

        for idx, (purview, mec_str) in enumerate(pares, 1):
            alcance = letters_to_binary(purview, n_val)
            mecanismo = letters_to_binary(mec_str, n_val)
            condicion = "1" * n_val

            print(
                f"  #{idx:>3}/{len(pares)}  {purview[:14]:<14} / {mec_str[:14]}",
                end="",
                flush=True,
            )

            limpiar_cache_subsistemas()
            limpiar_cache_find_mip()

            row = {"#Prueba": idx, "Purview": purview, "Mecanismo": mec_str}
            gestor = lambda: Manager(estado_inicial=estado)

            r = run_strategy(
                GeometricSIA,
                {"gestor": gestor()},
                {},
                condicion,
                alcance,
                mecanismo,
                tpm,
                case_to,
            )
            row["Geo_k2_particion"] = r["particion"]
            row["Geo_k2_perdida"] = r["perdida"]
            row["Geo_k2_tiempo_ms"] = r["tiempo_ms"]
            print(f"  Geo2={'.' if r['convergio'] else 'X'}", end="", flush=True)

            for k in [3, 4, 5]:
                r = run_strategy(
                    KPartitionSIA,
                    {"gestor": gestor()},
                    {
                        "k": k,
                        "forzar_heuristica": "kl_mc",
                        "n_samples_mc": n_mc,
                    },
                    condicion,
                    alcance,
                    mecanismo,
                    tpm,
                    case_to,
                )
                row[f"KLmc_k{k}_particion"] = r["particion"]
                row[f"KLmc_k{k}_perdida"] = r["perdida"]
                row[f"KLmc_k{k}_tiempo_ms"] = r["tiempo_ms"]
                print(f"  k{k}={'.' if r['convergio'] else 'X'}", end="", flush=True)

            row.update(heuristica_k_aprox(row))
            print()
            rows.append(row)

            if idx % 5 == 0:
                _checkpoint(pd.DataFrame(rows), n)

        df = pd.DataFrame(rows)
        _checkpoint(df, n)
        resultados[n] = df
        print(f"  n={n} completado: {len(df)} filas")

    return resultados


def main():
    parser = argparse.ArgumentParser(description="Benchmark aproximado KL+MC-EMD")
    parser.add_argument("--n", nargs="+", type=int, default=[10, 15, 20, 22, 25])
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--no-run-log", action="store_true")
    args = parser.parse_args()

    out_f = err_f = prev_out = prev_err = None
    if not args.no_run_log:
        out_f, err_f, prev_out, prev_err = _install_large_n_logging(args.n)

    try:
        print(f"Benchmark APROX - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"  n={args.n}  timeout={args.timeout}s")
        print(f"  salida: {APPROX_DIR}")

        resultados = run_benchmark_aprox(args.n, args.timeout)
        if resultados:
            save_results_aprox(resultados)
            total = sum(len(df) for df in resultados.values())
            print(f"Total filas: {total}")
        else:
            print("Sin resultados.")
    finally:
        if not args.no_run_log:
            _uninstall_large_n_logging(out_f, err_f, prev_out, prev_err)


if __name__ == "__main__":
    main()
