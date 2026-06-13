"""
Benchmark rapido: MCTS + MC-EMD para k=2,3,4,5 sin find_mip.

Objetivo: llenar todas las matrices DatosPruebas (n10-n25) en tiempo record
para comparar despues contra el benchmark exacto (Geo/KL en data/results/n{n}/).

Salida: GeoMIP/data/results/rapido/

Uso:
  cd GeoMIP/src/Method2_Dynamic_Programming_Reformulation
  uv run python ../benchmark_rapido.py --n 10 15 20 22 25
  uv run python ../benchmark_rapido.py --n 25 --desde 2
"""
from __future__ import annotations

import argparse
import gc
import os
import sys
from datetime import datetime
from pathlib import Path

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
from src.controllers.strategies.kpartition import KPartitionSIA  # noqa: E402
from src.models.base.sia import limpiar_cache_subsistemas  # noqa: E402
from src.middlewares.profile import profiler_manager  # noqa: E402

profiler_manager.enabled = False

RAPIDO_DIR = RESULTS_DIR / "rapido"
RAPIDO_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_TIMEOUT = 300


def _latest_rapido(n: int) -> Path | None:
    folder = RAPIDO_DIR / f"n{n}"
    if not folder.exists():
        return None
    files = sorted(folder.glob("n*_rapido_*.xlsx"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def merge_with_previous(n: int, new_df: pd.DataFrame) -> pd.DataFrame:
    """Combina corrida parcial (--desde N) con el ultimo n{n}_rapido_*.xlsx."""
    if new_df.empty or "#Prueba" not in new_df.columns:
        return new_df
    prev_path = _latest_rapido(n)
    if prev_path is None:
        return new_df
    old = pd.read_excel(prev_path)
    if "#Prueba" not in old.columns:
        return new_df
    merged = old.set_index("#Prueba")
    merged.update(new_df.set_index("#Prueba"))
    merged = merged.reset_index().sort_values("#Prueba")
    print(f"  merge: {len(new_df)} filas nuevas + base {prev_path.name} -> {len(merged)} total")
    return merged


def mcts_params(n_red: int) -> dict:
    """Parametros agresivos por tamano de red (prioriza velocidad)."""
    if n_red <= 10:
        return dict(
            mcts_n_iter=80,
            mcts_n_samples=350,
            mcts_rollout_depth=4,
            perdida_mc_final=True,
        )
    if n_red <= 15:
        return dict(
            mcts_n_iter=60,
            mcts_n_samples=450,
            mcts_rollout_depth=4,
            perdida_mc_final=True,
        )
    if n_red <= 20:
        return dict(
            mcts_n_iter=45,
            mcts_n_samples=500,
            mcts_rollout_depth=3,
            perdida_mc_final=True,
        )
    if n_red <= 22:
        return dict(
            mcts_n_iter=30,
            mcts_n_samples=350,
            mcts_rollout_depth=3,
            perdida_mc_final=True,
        )
    return dict(
        mcts_n_iter=18,
        mcts_n_samples=220,
        mcts_rollout_depth=2,
        perdida_mc_final=True,
    )


def mc_samples(n_red: int) -> int:
    if n_red <= 15:
        return 800
    if n_red <= 20:
        return 1500
    if n_red <= 22:
        return 2000
    return 2500


def call_kwargs_for_k(n_red: int, k: int, mcts_kw: dict) -> dict:
    """n>=25: KL+MC-EMD sin find_mip (MCTS/find_mip agotan timeout)."""
    if n_red >= 25:
        return {
            "k": k,
            "forzar_heuristica": "kl_mc",
            "n_samples_mc": mc_samples(n_red),
            "perdida_mc_final": True,
        }
    return {"k": k, "forzar_heuristica": "mcts", **mcts_kw}


def modo_label(n_red: int) -> str:
    return "KL+MC-EMD" if n_red >= 25 else "MCTS+MC-EMD"


def case_timeout(n_red: int, timeout: int) -> int:
    if n_red <= 10:
        return min(timeout, 90)
    if n_red <= 15:
        return min(timeout, 120)
    if n_red <= 20:
        return min(timeout, 240)
    if n_red <= 22:
        return min(timeout, 480)
    return min(timeout, 900)


def _carpeta_n(n: int) -> Path:
    p = RAPIDO_DIR / f"n{n}"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _checkpoint(df: pd.DataFrame, n: int):
    ts = datetime.now().strftime("%Y-%m-%d_%Hh%M")
    try:
        df.to_excel(_carpeta_n(n) / f"checkpoint_{ts}.xlsx", index=False)
    except Exception:
        pass


def save_results_rapido(resultados: dict[int, pd.DataFrame]) -> Path:
    ts = datetime.now().strftime("%Y-%m-%d_%Hh%M")
    for n, df in sorted(resultados.items()):
        out = _carpeta_n(n) / f"n{n}_rapido_{ts}.xlsx"
        df.to_excel(out, index=False)
        print(f"  n={n} guardado en: {out}")

    out = RAPIDO_DIR / f"benchmark_rapido_{ts}.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as xw:
        for n, df in sorted(resultados.items()):
            df.to_excel(xw, sheet_name=f"n{n}", index=False)
    print(f"\nConsolidado rapido: {out}")
    return out


def run_benchmark_rapido(
    ns: list[int],
    timeout: int,
    desde: int = 1,
    hasta: int | None = None,
    merge: bool = True,
) -> dict[int, pd.DataFrame]:
    os.environ.setdefault("KQGMIP_QUIET", "1")
    resultados: dict[int, pd.DataFrame] = {}

    for n in ns:
        if n not in CASOS:
            print(f"[SKIP] n={n}")
            continue

        n_val, estado, pares = CASOS[n]()
        tpm_path = next(
            (SAMPLES_DIR / f"N{n}{s}.csv" for s in ("A", "B", "C") if (SAMPLES_DIR / f"N{n}{s}.csv").exists()),
            None,
        )
        if tpm_path is None:
            print(f"[SKIP] n={n}: sin TPM")
            continue

        case_to = case_timeout(n, timeout)
        mcts_kw = mcts_params(n)

        print(f"\n{'='*65}")
        print(
            f"[RAPIDO] n={n}  TPM={tpm_path.name}  casos={len(pares)}"
            f"  timeout={case_to}s  {modo_label(n)} k=2..5"
        )
        if n >= 25:
            print(f"  mc_samples={mc_samples(n)}  (k=2..5 sin find_mip)")
        else:
            print(f"  params: {mcts_kw}")
        print(f"{'='*65}")

        tpm = load_tpm(tpm_path, n_val)
        rows: list[dict] = []
        fin = hasta or len(pares)

        for idx, (purview, mec_str) in enumerate(pares, 1):
            if idx < desde:
                continue
            if idx > fin:
                break

            alcance = letters_to_binary(purview, n_val)
            mecanismo = letters_to_binary(mec_str, n_val)
            condicion = "1" * n_val

            print(
                f"  #{idx:>3}/{len(pares)}  {purview[:14]:<14} / {mec_str[:14]}",
                end="",
                flush=True,
            )

            limpiar_cache_subsistemas()
            gc.collect()

            row = {"#Prueba": idx, "Purview": purview, "Mecanismo": mec_str}
            gestor = lambda: Manager(estado_inicial=estado)

            for k in [2, 3, 4, 5]:
                kw = call_kwargs_for_k(n, k, mcts_kw)
                r = run_strategy(
                    KPartitionSIA,
                    {"gestor": gestor()},
                    kw,
                    condicion,
                    alcance,
                    mecanismo,
                    tpm,
                    case_to,
                )
                row[f"MCTS_k{k}_particion"] = r["particion"]
                row[f"MCTS_k{k}_perdida"] = r["perdida"]
                row[f"MCTS_k{k}_tiempo_ms"] = r["tiempo_ms"]
                row[f"MCTS_k{k}_ok"] = r["convergio"]
                if not r["convergio"] and r.get("error"):
                    row[f"MCTS_k{k}_error"] = r["error"]
                print(f"  k{k}={'.' if r['convergio'] else 'X'}", end="", flush=True)

            print()
            rows.append(row)

            if len(rows) % 5 == 0:
                _checkpoint(pd.DataFrame(rows), n)

        df = pd.DataFrame(rows)
        if merge and desde > 1:
            df = merge_with_previous(n, df)
        _checkpoint(df, n)
        resultados[n] = df
        print(f"  n={n} completado: {len(df)} filas")

    return resultados


def main():
    parser = argparse.ArgumentParser(description="Benchmark rapido MCTS+MC-EMD")
    parser.add_argument("--n", nargs="+", type=int, default=[10, 15, 20, 22, 25])
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--desde", type=int, default=1, help="Primer caso (1-based)")
    parser.add_argument("--hasta", type=int, default=None, help="Ultimo caso (1-based)")
    parser.add_argument("--no-run-log", action="store_true")
    parser.add_argument("--no-merge", action="store_true", help="No fusionar con rapido previo al usar --desde")
    args = parser.parse_args()

    out_f = err_f = prev_out = prev_err = None
    if not args.no_run_log:
        out_f, err_f, prev_out, prev_err = _install_large_n_logging(args.n)

    try:
        print(f"Benchmark RAPIDO - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"  n={args.n}  timeout={args.timeout}s  desde={args.desde}")
        print(f"  salida: {RAPIDO_DIR}")

        resultados = run_benchmark_rapido(
            args.n, args.timeout, desde=args.desde, hasta=args.hasta,
            merge=not args.no_merge,
        )
        if resultados:
            save_results_rapido(resultados)
            print(f"Total filas: {sum(len(d) for d in resultados.values())}")
        else:
            print("Sin resultados.")
    finally:
        if not args.no_run_log:
            _uninstall_large_n_logging(out_f, err_f, prev_out, prev_err)


if __name__ == "__main__":
    main()
