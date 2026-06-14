"""
Ejecuta únicamente QNodes (bipartición, k=2) sobre DatosPruebas2026
para n in {10, 15, 20, 22, 25}.

Salida: GeoMIP/data/results/n{n}/qnodes_k2_n{n}_<fecha>.xlsx

Uso (desde Method2_Dynamic_Programming_Reformulation):
  uv run python ../run_qnodes_k2.py --n 10 15 20 22 25
  uv run python ../run_qnodes_k2.py --n 25 --desde 2 --timeout 86400
  uv run python ../run_qnodes_k2.py --n 15 --merge
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

from src.controllers.manager import Manager  # noqa: E402
from src.controllers.strategies.q_nodes import QNodes  # noqa: E402
from src.models.base.sia import limpiar_cache_subsistemas  # noqa: E402
from src.middlewares.profile import profiler_manager  # noqa: E402

from benchmark import CASOS, letters_to_binary, run_strategy  # noqa: E402

profiler_manager.enabled = False

QN_COLS = [
    "QN_k2_particion",
    "QN_k2_perdida",
    "QN_k2_tiempo_ms",
    "QN_k2_convergio",
    "QN_k2_error",
]

# Timeout por caso (segundos). QNodes escala mal en redes grandes.
TIMEOUT_POR_N = {
    10: 600,
    15: 3600,
    20: 21600,
    22: 21600,
    25: 86400,
}


def _carpeta_n(n: int) -> Path:
    p = RESULTS_DIR / f"n{n}"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _latest_qnodes(n: int) -> Path | None:
    folder = _carpeta_n(n)
    files = sorted(
        list(folder.glob(f"qnodes_k2_n{n}_*.xlsx"))
        + list(folder.glob("qnodes_k2_checkpoint_*.xlsx")),
        key=lambda p: p.stat().st_mtime,
    )
    return files[-1] if files else None


def merge_with_previous(n: int, new_df: pd.DataFrame) -> pd.DataFrame:
    """Combina corrida parcial con el último qnodes_k2_*.xlsx del mismo n."""
    if new_df.empty or "#Prueba" not in new_df.columns:
        return new_df
    prev_path = _latest_qnodes(n)
    if prev_path is None:
        return new_df
    old = pd.read_excel(prev_path)
    if "#Prueba" not in old.columns:
        return new_df
    merged = (
        pd.concat([old, new_df], ignore_index=True)
        .drop_duplicates(subset="#Prueba", keep="last")
        .sort_values("#Prueba")
        .reset_index(drop=True)
    )
    print(f"  merge: {len(new_df)} filas nuevas + {prev_path.name} -> {len(merged)} total")
    return merged


def patch_completo(n: int, qn_df: pd.DataFrame) -> Path | None:
    """Actualiza columnas QN_k2_* en el último n*_completo_*.xlsx si existe."""
    folder = _carpeta_n(n)
    files = sorted(folder.glob("n*_completo_*.xlsx"), key=lambda p: p.stat().st_mtime)
    if not files:
        return None
    path = files[-1]
    base = pd.read_excel(path)
    if "#Prueba" not in base.columns:
        return None
    qn = qn_df.set_index("#Prueba")
    base = base.set_index("#Prueba")
    for col in QN_COLS:
        if col in qn.columns:
            base[col] = qn[col]
    out = folder / f"{path.stem}_qn_k2.xlsx"
    base.reset_index().to_excel(out, index=False)
    print(f"  parche completo: {out.name}")
    return out


def run_qnodes_k2(
    n: int,
    timeout: int,
    desde: int = 1,
    merge: bool = False,
    patch: bool = True,
    casos: list[int] | None = None,
) -> pd.DataFrame:
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
            f"Generar con: python GeoMIP/data/generate_large_tpms.py --n {n}"
        )

    casos_set = set(casos) if casos else None
    casos_label = f"  solo={sorted(casos_set)}" if casos_set else ""
    print(
        f"\n{'='*60}\n"
        f"QNodes k=2 — n={n}  TPM={tpm_path.name}  casos={len(pares)}  "
        f"timeout={timeout}s  desde=#{desde}{casos_label}\n"
        f"{'='*60}",
        flush=True,
    )
    print(f"Cargando TPM...", flush=True)
    tpm = load_tpm(tpm_path, n_val)
    print(f"TPM: shape={tpm.shape}  dtype={tpm.dtype}", flush=True)

    rows: list[dict] = []
    if merge:
        prev = _latest_qnodes(n)
        if prev is not None:
            old = pd.read_excel(prev)
            rows = old.to_dict("records")
            print(f"  cargado checkpoint previo: {prev.name} ({len(rows)} filas)", flush=True)

    for idx, (purview, mec_str) in enumerate(pares, 1):
        if idx < desde:
            continue
        if casos_set is not None and idx not in casos_set:
            continue

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

        if merge:
            found = False
            for i, existing in enumerate(rows):
                if existing.get("#Prueba") == idx:
                    rows[i] = row
                    found = True
                    break
            if not found:
                rows.append(row)
        else:
            rows.append(row)

        status = "OK" if r["convergio"] else f"FAIL ({r['error']})"
        print(f"  {status}", flush=True)

        if idx % 5 == 0:
            ts = datetime.now().strftime("%Y-%m-%d_%Hh%M")
            ck = _carpeta_n(n) / f"qnodes_k2_checkpoint_{ts}.xlsx"
            pd.DataFrame(rows).sort_values("#Prueba").to_excel(ck, index=False)
            print(f"    checkpoint -> {ck.name}", flush=True)

    df = pd.DataFrame(rows).sort_values("#Prueba").reset_index(drop=True)
    if merge:
        df = merge_with_previous(n, df)
    return df


def main():
    parser = argparse.ArgumentParser(description="QNodes k=2 — DatosPruebas2026")
    parser.add_argument(
        "--n", nargs="+", type=int, default=[10, 15, 20, 22, 25],
        help="Tamaños de red (default: 10 15 20 22 25)",
    )
    parser.add_argument("--timeout", type=int, default=None,
                        help="Segundos máximos por caso (default: según n)")
    parser.add_argument("--desde", type=int, default=1,
                        help="Reanudar desde el número de prueba (1-based)")
    parser.add_argument("--merge", action="store_true",
                        help="Fusionar con el último qnodes_k2_*.xlsx del mismo n")
    parser.add_argument("--casos", nargs="+", type=int, default=None,
                        help="Solo ejecutar estos #Prueba (ej: --casos 19 20 21)")
    parser.add_argument("--no-patch", action="store_true",
                        help="No generar parche del benchmark completo")
    args = parser.parse_args()

    for n in args.n:
        timeout = args.timeout or TIMEOUT_POR_N.get(n, 86400)
        df = run_qnodes_k2(
            n, timeout, desde=args.desde, merge=args.merge, casos=args.casos
        )
        ts = datetime.now().strftime("%Y-%m-%d_%Hh%M")
        out = _carpeta_n(n) / f"qnodes_k2_n{n}_{ts}.xlsx"
        df.to_excel(out, index=False)
        ok = int(df["QN_k2_convergio"].fillna(False).sum())
        print(f"\nCompletado n={n}: {ok}/{len(df)} convergieron")
        print(f"Salida: {out}")
        if not args.no_patch:
            patch_completo(n, df)


if __name__ == "__main__":
    main()
