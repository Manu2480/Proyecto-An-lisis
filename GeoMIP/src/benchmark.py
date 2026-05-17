"""
GeoMIP/src/benchmark.py
========================
Benchmark completo del proyecto K-QGMIP.

Ejecuta GeometricSIA, KPartitionSIA (k=3,4,5) y QNodes sobre todos los
casos de prueba definidos en DatosPruebas2026_1.md para los sistemas
n ∈ {10, 15, 20, 22} disponibles en GeoMIP/data/samples/.

Métricas registradas por fila:
  tpm, n, estado_inicial, alcance, mecanismo, k, estrategia,
  particion, perdida_emd, tiempo_ms, memoria_mb, convergio

Salida:
  GeoMIP/results/benchmark_YYYY-MM-DD_HHhMM.xlsx   — resultados completos
  GeoMIP/results/benchmark_summary_YYYY-MM-DD.xlsx  — resumen por n/k/estrategia

Uso:
  cd GeoMIP/src/Method2_Dynamic_Programming_Reformulation
  uv run python ../../../src/benchmark.py
  uv run python ../../../src/benchmark.py --timeout 300 --n 10 15
"""
import sys
import os
import time
import signal
import argparse
import traceback
import tracemalloc
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# Aumentar límite de recursión para subsistemas grandes
sys.setrecursionlimit(10000)

# ── Paths ──────────────────────────────────────────────────────────────────
BENCHMARK_ROOT = Path(__file__).resolve().parent   # GeoMIP/src/
GEOMIP_ROOT    = BENCHMARK_ROOT.parent             # GeoMIP/
SAMPLES_DIR    = GEOMIP_ROOT / "data" / "samples"
RESULTS_DIR    = GEOMIP_ROOT / "results"
METHOD2_ROOT   = GEOMIP_ROOT / "src" / "Method2_Dynamic_Programming_Reformulation"

# Añadir Method2 al path
if str(METHOD2_ROOT) not in sys.path:
    sys.path.insert(0, str(METHOD2_ROOT))

from src.controllers.manager import Manager
from src.controllers.strategies.geometric  import GeometricSIA
from src.controllers.strategies.kpartition import KPartitionSIA
from src.controllers.strategies.q_nodes    import QNodes

# Desactivar el profiler global para no crashear con RecursionError
# al renderizar el HTML de pyinstrument en subsistemas grandes (n>8)
from src.middlewares.profile import profiler_manager
profiler_manager.enabled = False

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Constantes ──────────────────────────────────────────────────────────────
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_TIMEOUT = 600   # segundos por caso


# ── Conversión letras ↔ binario ─────────────────────────────────────────────
def letters_to_binary(text: str, n: int) -> str:
    """'ABCDFHIJ' con n=10 → '1101011100'"""
    positions = ALPHABET[:n]
    mask = ["0"] * n
    for ch in text.strip().upper():
        if ch in positions:
            mask[positions.index(ch)] = "1"
    return "".join(mask)


# ── Timeout context manager ─────────────────────────────────────────────────
class TimeoutError(Exception):
    pass


# ── Ejecutar una función con timeout real (Windows-compatible) ─────────────
def _run_with_timeout(func, timeout_seconds: int):
    """
    Ejecuta func() en un thread separado con join(timeout).
    Usa un stack de 256 MB para evitar crashes por RecursionError fatal
    (el algoritmo calcular_costo es recursivo en profundidad ~2^n).
    Devuelve (result, elapsed_s, timed_out, exc).
    """
    import threading
    result_holder = [None]
    exc_holder    = [None]

    def worker():
        try:
            result_holder[0] = func()
        except BaseException as exc:   # captura RecursionError y otros fatales
            exc_holder[0] = exc

    # stack_size de 256 MB da espacio para ~2^18 frames de recursión
    try:
        threading.stack_size(256 * 1024 * 1024)
    except (OSError, ValueError):
        pass   # algunos OS no permiten cambiar el stack size; continuar igual

    t = threading.Thread(target=worker, daemon=True)
    t0 = time.perf_counter()
    t.start()
    t.join(timeout=timeout_seconds)
    elapsed = time.perf_counter() - t0
    timed_out = t.is_alive()   # si sigue vivo → timeout
    exc = exc_holder[0]
    return result_holder[0], elapsed, timed_out, exc


# ── Definición de casos de prueba ────────────────────────────────────────────
def build_test_cases_n10():
    """49 subsistemas para N=10 según DatosPruebas2026_1.md (Sheet: 10A-Elementos)."""
    n = 10
    estado = "1000000000"
    purviews = [
        "ABCDEFGHIJ", "ABCDEFGHIJ", "ABCDEFGHIJ", "ABCDEFGHIJ",
        "ABCDEFGHIJ", "ABCDEFGHIJ", "ABCDEFGHIJ",
        "ABCDEFGHI",  "ABCDEFGHI",  "ABCDEFGHI",  "ABCDEFGHI",
        "ABCDEFGHI",  "ABCDEFGHI",  "ABCDEFGHI",
        "BCDEFGHIJ",  "BCDEFGHIJ",  "BCDEFGHIJ",  "BCDEFGHIJ",
        "BCDEFGHIJ",  "BCDEFGHIJ",  "BCDEFGHIJ",
        "BCDEFGHI",   "BCDEFGHI",   "BCDEFGHI",   "BCDEFGHI",
        "BCDEFGHI",   "BCDEFGHI",   "BCDEFGHI",
        "ABDEGHJ",    "ABDEGHJ",    "ABDEGHJ",    "ABDEGHJ",
        "ABDEGHJ",    "ABDEGHJ",    "ABDEGHJ",
        "ACEGI",      "ACEGI",      "ACEGI",      "ACEGI",
        "ACEGI",      "ACEGI",      "ACEGI",
        "BDFHJ",      "BDFHJ",      "BDFHJ",      "BDFHJ",
        "BDFHJ",      "BDFHJ",      "BDFHJ",
    ]
    mechanisms = [
        "ABCDEFGHIJ", "ABCDEFGHI", "BCDEFGHIJ", "BCDEFGHI",
        "ABDEGHJ",    "ACEGI",     "BDFHJ",
        "ABCDEFGHIJ", "ABCDEFGHI", "BCDEFGHIJ", "BCDEFGHI",
        "ABDEGHJ",    "ACEGI",     "BDFHJ",
        "ABCDEFGHIJ", "ABCDEFGHI", "BCDEFGHIJ", "BCDEFGHI",
        "ABDEGHJ",    "ACEGI",     "BDFHJ",
        "ABCDEFGHIJ", "ABCDEFGHI", "BCDEFGHIJ", "BCDEFGHI",
        "ABDEGHJ",    "ACEGI",     "BDFHJ",
        "ABCDEFGHIJ", "ABCDEFGHI", "BCDEFGHIJ", "BCDEFGHI",
        "ABDEGHJ",    "ACEGI",     "BDFHJ",
        "ABCDEFGHIJ", "ABCDEFGHI", "BCDEFGHIJ", "BCDEFGHI",
        "ABDEGHJ",    "ACEGI",     "BDFHJ",
        "ABCDEFGHIJ", "ABCDEFGHI", "BCDEFGHIJ", "BCDEFGHI",
        "ABDEGHJ",    "ACEGI",     "BDFHJ",
    ]
    return n, estado, list(zip(purviews, mechanisms))


def build_test_cases_n15():
    """49 subsistemas para N=15 (Sheet: 15B-Elementos, TPM: N15B.csv)."""
    n = 15
    estado = "100000000000000"
    purviews = [
        "ABCDEFGHIJKLMNO","ABCDEFGHIJKLMNO","ABCDEFGHIJKLMNO","ABCDEFGHIJKLMNO",
        "ABCDEFGHIJKLMNO","ABCDEFGHIJKLMNO","ABCDEFGHIJKLMNO",
        "ABCDEFGHIJKLMN","ABCDEFGHIJKLMN","ABCDEFGHIJKLMN","ABCDEFGHIJKLMN",
        "ABCDEFGHIJKLMN","ABCDEFGHIJKLMN","ABCDEFGHIJKLMN",
        "BCDEFGHIJKLMNO","BCDEFGHIJKLMNO","BCDEFGHIJKLMNO","BCDEFGHIJKLMNO",
        "BCDEFGHIJKLMNO","BCDEFGHIJKLMNO","BCDEFGHIJKLMNO",
        "BCDEFGHIJKLMN","BCDEFGHIJKLMN","BCDEFGHIJKLMN","BCDEFGHIJKLMN",
        "BCDEFGHIJKLMN","BCDEFGHIJKLMN","BCDEFGHIJKLMN",
        "ABDEGHJKMN","ABDEGHJKMN","ABDEGHJKMN","ABDEGHJKMN",
        "ABDEGHJKMN","ABDEGHJKMN","ABDEGHJKMN",
        "ACEGIKMO","ACEGIKMO","ACEGIKMO","ACEGIKMO",
        "ACEGIKMO","ACEGIKMO","ACEGIKMO",
        "BDFHJLN","BDFHJLN","BDFHJLN","BDFHJLN",
        "BDFHJLN","BDFHJLN","BDFHJLN",
    ]
    mechanisms = [
        "ABCDEFGHIJKLMNO","ABCDEFGHIJKLMN","BCDEFGHIJKLMNO","BCDEFGHIJKLMN",
        "ABDEGHJKMN","ACEGIKMO","BDFHJLN",
        "ABCDEFGHIJKLMNO","ABCDEFGHIJKLMN","BCDEFGHIJKLMNO","BCDEFGHIJKLMN",
        "ABDEGHJKMN","ACEGIKMO","BDFHJLN",
        "ABCDEFGHIJKLMNO","ABCDEFGHIJKLMN","BCDEFGHIJKLMNO","BCDEFGHIJKLMN",
        "ABDEGHJKMN","ACEGIKMO","BDFHJLN",
        "ABCDEFGHIJKLMNO","ABCDEFGHIJKLMN","BCDEFGHIJKLMNO","BCDEFGHIJKLMN",
        "ABDEGHJKMN","ACEGIKMO","BDFHJLN",
        "ABCDEFGHIJKLMNO","ABCDEFGHIJKLMN","BCDEFGHIJKLMNO","BCDEFGHIJKLMN",
        "ABDEGHJKMN","ACEGIKMO","BDFHJLN",
        "ABCDEFGHIJKLMNO","ABCDEFGHIJKLMN","BCDEFGHIJKLMNO","BCDEFGHIJKLMN",
        "ABDEGHJKMN","ACEGIKMO","BDFHJLN",
        "ABCDEFGHIJKLMNO","ABCDEFGHIJKLMN","BCDEFGHIJKLMNO","BCDEFGHIJKLMN",
        "ABDEGHJKMN","ACEGIKMO","BDFHJLN",
    ]
    return n, estado, list(zip(purviews, mechanisms))


def build_test_cases_n20():
    """7 casos representativos para N=20 (subsistemas grandes, sin BruteForce)."""
    n = 20
    estado = "10000000000000000000"
    full = ALPHABET[:n]
    pairs = [
        (full, full),
        (full, full[:-1]),
        (full[1:], full),
        (full[1:], full[1:]),
        ("".join(full[i] for i in range(0,n,2)), full),
        ("".join(full[i] for i in range(1,n,2)), full),
        (full, "".join(full[i] for i in range(0,n,2))),
    ]
    return n, estado, pairs


def build_test_cases_n22():
    """5 casos representativos para N=22."""
    n = 22
    estado = "1000000000000000000000"
    full = ALPHABET[:n]
    pairs = [
        (full, full),
        (full[:-1], full),
        (full, full[:-1]),
        ("".join(full[i] for i in range(0,n,2)), full),
        ("".join(full[i] for i in range(1,n,2)), full),
    ]
    return n, estado, pairs


# ── Correr una estrategia con timeout y medición de memoria ──────────────────
def run_strategy(strategy_cls, manager_kwargs, strategy_kwargs, cond, alcance, mec,
                 tpm=None, timeout=DEFAULT_TIMEOUT) -> dict:
    """
    Ejecuta una estrategia con timeout real (thread-based, Windows-compatible)
    y retorna un dict con métricas.
    """
    result = {
        "estrategia": strategy_cls.__name__,
        "particion": None,
        "perdida_emd": None,
        "tiempo_ms": None,
        "memoria_mb": None,
        "convergio": False,
        "error": None,
    }

    def task():
        tracemalloc.start()
        strat = strategy_cls(**manager_kwargs, **strategy_kwargs)
        if tpm is not None:
            sol = strat.aplicar_estrategia(cond, alcance, mec, tpm)
        else:
            sol = strat.aplicar_estrategia(cond, alcance, mec)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return sol, peak

    try:
        sol_peak, elapsed, timed_out, exc = _run_with_timeout(task, timeout)
        if timed_out:
            result["error"] = f"TIMEOUT > {timeout}s"
            result["convergio"] = False
        elif exc is not None:
            raise exc
        else:
            sol, peak = sol_peak
            result["particion"]   = str(sol.particion)
            result["perdida_emd"] = float(sol.perdida) if sol.perdida is not None else None
            result["tiempo_ms"]   = elapsed * 1000.0
            result["memoria_mb"]  = peak / 1_048_576
            result["convergio"]   = "Inviable" not in str(sol.particion)
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["convergio"] = False
    finally:
        if tracemalloc.is_tracing():
            tracemalloc.stop()
    return result


# ── Benchmark principal ───────────────────────────────────────────────────────
def run_benchmark(ns_to_run: list[int], timeout: int, skip_bruteforce: bool,
                  k_values: list[int]) -> pd.DataFrame:
    """Ejecuta el benchmark completo y retorna un DataFrame."""
    configs = {
        10: build_test_cases_n10,
        15: build_test_cases_n15,
        20: build_test_cases_n20,
        22: build_test_cases_n22,
    }
    records = []

    for n in ns_to_run:
        if n not in configs:
            print(f"[SKIP] n={n}: sin configuracion de casos")
            continue

        build_fn = configs[n]
        n_val, estado_inicial, subsystems = build_fn()

        # Buscar TPM disponible
        tpm_path = None
        for suffix in ["A", "B", "C"]:
            p = SAMPLES_DIR / f"N{n}{suffix}.csv"
            if p.exists():
                tpm_path = p
                break
        if tpm_path is None:
            print(f"[SKIP] n={n}: no hay TPM en {SAMPLES_DIR}")
            continue

        print(f"\n{'='*60}")
        print(f"n={n}  TPM={tpm_path.name}  casos={len(subsystems)}")
        print(f"{'='*60}")

        tpm = np.genfromtxt(tpm_path, delimiter=",")

        for idx, (purview_txt, mech_txt) in enumerate(subsystems, 1):
            alcance  = letters_to_binary(purview_txt,  n_val)
            mecanismo = letters_to_binary(mech_txt,     n_val)
            condicion = "1" * n_val   # sistema candidato completo

            print(f"  caso {idx:>3}/{len(subsystems):>3}  "
                  f"purview={purview_txt[:12]:<12} mech={mech_txt[:12]}", end="", flush=True)

            # Base info para todos los registros de este caso
            base = dict(
                tpm=tpm_path.name,
                n=n_val,
                estado_inicial=estado_inicial,
                purview_texto=purview_txt,
                mecanismo_texto=mech_txt,
                alcance=alcance,
                mecanismo=mecanismo,
            )

            # ── Geometric (k=2) ────────────────────────────────────────────
            r = run_strategy(GeometricSIA,
                             {"gestor": Manager(estado_inicial=estado_inicial)},
                             {}, condicion, alcance, mecanismo, tpm, timeout)
            records.append({**base, "k": 2, **r})
            sym = "." if r["convergio"] else "T" if "TIMEOUT" in str(r["error"]) else "E"
            print(f"  Geo={sym}", end="", flush=True)

            # ── QNodes (k=2) ───────────────────────────────────────────────
            r2 = run_strategy(QNodes,
                              {"gestor": Manager(estado_inicial=estado_inicial)},
                              {}, condicion, alcance, mecanismo, None, timeout)
            records.append({**base, "k": 2, **r2})
            sym2 = "." if r2["convergio"] else "T" if "TIMEOUT" in str(r2["error"]) else "E"
            print(f"  QN={sym2}", end="", flush=True)

            # ── KPartition (k=3,4,5) ──────────────────────────────────────
            for k in k_values:
                for cls_label in [("Geo_k", GeometricSIA), ("QN_k", QNodes)]:
                    lbl, BaseStrategy = cls_label
                    if lbl == "Geo_k":
                        rk = run_strategy(
                            KPartitionSIA,
                            {"gestor": Manager(estado_inicial=estado_inicial)},
                            {"k": k},
                            condicion, alcance, mecanismo, tpm, timeout
                        )
                        rk["estrategia"] = f"KPartitionSIA_k{k}"
                    else:
                        continue
                    records.append({**base, "k": k, **rk})
                    sk = "." if rk["convergio"] else "T" if "TIMEOUT" in str(rk["error"]) else "E"
                    print(f"  KP{k}={sk}", end="", flush=True)

            print()  # newline

            # Guardado incremental cada 10 casos
            if idx % 10 == 0 and records:
                _save_incremental(pd.DataFrame(records), n)

    return pd.DataFrame(records)


def _save_incremental(df: pd.DataFrame, n: int):
    """Guarda un checkpoint parcial del benchmark."""
    ts = datetime.now().strftime("%Y-%m-%d_%Hh%M")
    path = RESULTS_DIR / f"benchmark_checkpoint_n{n}_{ts}.xlsx"
    try:
        df.to_excel(path, index=False)
        print(f"  [checkpoint] {path.name}")
    except Exception:
        pass   # no abortar el benchmark por un fallo de guardado


# ── Guardar resultados ────────────────────────────────────────────────────────
def save_results(df: pd.DataFrame):
    now = datetime.now()
    ts  = now.strftime("%Y-%m-%d_%Hh%M")
    ds  = now.strftime("%Y-%m-%d")

    full_path    = RESULTS_DIR / f"benchmark_{ts}.xlsx"
    summary_path = RESULTS_DIR / f"benchmark_summary_{ds}.xlsx"

    # ── Hoja completa ────────────────────────────────────────────────────────
    with pd.ExcelWriter(full_path, engine="openpyxl") as xw:
        df.to_excel(xw, sheet_name="Resultados", index=False)
        # Hoja resumen por n/estrategia/k
        cols_num = ["perdida_emd", "tiempo_ms", "memoria_mb"]
        agg = (df.dropna(subset=["perdida_emd"])
                 .groupby(["n", "estrategia", "k"])[cols_num]
                 .agg(["mean", "min", "max", "std"])
                 .round(4))
        agg.to_excel(xw, sheet_name="Resumen")

    print(f"\nResultados guardados en:\n  {full_path}")

    # ── Hoja resumen standalone ───────────────────────────────────────────────
    with pd.ExcelWriter(summary_path, engine="openpyxl") as xw:
        cols_num = ["perdida_emd", "tiempo_ms", "memoria_mb"]
        agg = (df.dropna(subset=["perdida_emd"])
                 .groupby(["n", "estrategia", "k"])[cols_num]
                 .agg(["mean", "min", "max", "std"])
                 .round(4))
        agg.to_excel(xw, sheet_name="Resumen")
        df.to_excel(xw, sheet_name="Detalle", index=False)
    print(f"  {summary_path}")

    return full_path, summary_path


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Benchmark K-QGMIP")
    parser.add_argument("--n",       nargs="+", type=int,
                        default=[10, 15, 20, 22],
                        help="Valores de n a incluir (e.g. --n 10 15)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help="Timeout en segundos por caso (default=600)")
    parser.add_argument("--k",       nargs="+", type=int,
                        default=[3, 4, 5],
                        help="Valores de k para KPartitionSIA")
    parser.add_argument("--skip-bruteforce", action="store_true",
                        help="Omite BruteForce (muy lento para n>6)")
    args = parser.parse_args()

    print(f"Benchmark K-QGMIP — {datetime.now():%Y-%m-%d %H:%M}")
    print(f"  n={args.n}  timeout={args.timeout}s  k={args.k}")
    print(f"  samples: {SAMPLES_DIR}")
    print(f"  results: {RESULTS_DIR}")

    df = run_benchmark(
        ns_to_run=args.n,
        timeout=args.timeout,
        skip_bruteforce=args.skip_bruteforce,
        k_values=args.k,
    )

    if df.empty:
        print("[ERROR] No se generaron resultados.")
        sys.exit(1)

    full, summary = save_results(df)
    print(f"\nTotal de filas: {len(df)}")
    print(f"Convergencias: {df['convergio'].sum()}/{len(df)}")
    errores = df[df["error"].notna()]
    if not errores.empty:
        print(f"Errores/timeouts: {len(errores)}")
        for _, row in errores.head(5).iterrows():
            print(f"  n={row['n']} {row.get('purview_texto','')} / {row.get('mecanismo_texto','')} "
                  f"k={row['k']} {row['estrategia']}: {row['error']}")


if __name__ == "__main__":
    main()
