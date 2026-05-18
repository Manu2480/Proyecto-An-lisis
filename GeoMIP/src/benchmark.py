"""
GeoMIP/src/benchmark.py
========================
Benchmark completo del proyecto K-QGMIP.

Ejecuta para n in {10, 15, 20, 22, 25} los subconjuntos EXACTOS de
DatosPruebas2026_1.md con las estrategias:
  k=2: QNodes, GeometricSIA
  k=3,4,5: KPartitionSIA greedy (prefijo tablas QN_*) + KPartitionSIA KL
  k=4: idem
  k=5: idem

Formato de salida: una fila por caso de prueba, columnas por estrategia/k
(igual al Excel DatosPruebas2026).

Uso:
  cd GeoMIP/src/Method2_Dynamic_Programming_Reformulation
  uv run python ../benchmark.py
  uv run python ../benchmark.py --n 10 15
  uv run python ../benchmark.py --n 20 22 25
  uv run python ../benchmark.py --timeout 21600

Cuando la petición incluye algún n≥20, además de imprimir en consola se escriben
  GeoMIP/results/logs/n20_plus/benchmark_n<...>_<fecha>_<hora>.stdout.log
  GeoMIP/results/logs/n20_plus/benchmark_n<...>_<fecha>_<hora>.stderr.log
(UTF-8). Desactivar con --no-run-log.
"""
import sys
import os
import time
import threading
import tracemalloc
import argparse
from datetime import datetime
from pathlib import Path

# Forzar UTF-8 en stdout/stderr para evitar UnicodeEncodeError en Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd

sys.setrecursionlimit(10000)

# ── Paths ───────────────────────────────────────────────────────────────────
BENCHMARK_ROOT = Path(__file__).resolve().parent        # GeoMIP/src/
GEOMIP_ROOT    = BENCHMARK_ROOT.parent                  # GeoMIP/
SAMPLES_DIR    = GEOMIP_ROOT / "data" / "samples"
RESULTS_DIR    = GEOMIP_ROOT / "results"
METHOD2_ROOT   = GEOMIP_ROOT / "src" / "Method2_Dynamic_Programming_Reformulation"

if str(METHOD2_ROOT) not in sys.path:
    sys.path.insert(0, str(METHOD2_ROOT))

from src.controllers.manager import Manager
from src.controllers.strategies.geometric  import GeometricSIA, limpiar_cache_find_mip
from src.controllers.strategies.kpartition import KPartitionSIA
from src.controllers.strategies.q_nodes    import QNodes
from src.models.base.sia import limpiar_cache_subsistemas

# Desactivar profiler para evitar crash de encoding con caracteres Unicode
from src.middlewares.profile import profiler_manager
profiler_manager.enabled = False

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Cota por estrategia por defecto (~6 h). Casos n=20 pueden tardar horas por find_mip.
# Se puede subir con CLI:  uv run python ../benchmark.py --timeout 72000
DEFAULT_TIMEOUT = 21600


# ── Logging Tee (n≥20): consola + archivo con fecha en nombre ─────────────────


class _TeeTextStream:
    """Replica cada write/flush a varios streams (p. ej. consola + archivo)."""

    __slots__ = ("_streams",)

    def __init__(self, *streams):
        self._streams = streams

    def write(self, data: str) -> int:
        for s in self._streams:
            s.write(data)
        return len(data)

    def flush(self) -> None:
        for s in self._streams:
            s.flush()


def _large_n_log_paths(ns: list[int]) -> tuple[Path, Path] | None:
    """Rutas stdout/stderr bajo results/logs/n20_plus/; None si no aplica."""
    large = sorted({n for n in ns if n >= 20})
    if not large:
        return None
    stamp = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%S")
    tag = "-".join(str(n) for n in large)
    log_dir = RESULTS_DIR / "logs" / "n20_plus"
    log_dir.mkdir(parents=True, exist_ok=True)
    base = log_dir / f"benchmark_n{tag}_{stamp}"
    return (base.with_name(base.name + ".stdout.log"), base.with_name(base.name + ".stderr.log"))


def _install_large_n_logging(ns: list[int]):
    """
    Si hay n≥20, abre .stdout.log / .stderr.log y envuelve sys.stdout/sys.stderr.
    Retorna (out_file, err_file, prev_stdout, prev_stderr) para restaurar en finally;
    si no aplica, retorna (None, None, None, None).
    """
    paths = _large_n_log_paths(ns)
    if paths is None:
        return None, None, None, None
    out_path, err_path = paths
    out_f = open(out_path, "w", encoding="utf-8", errors="replace", buffering=1)
    err_f = open(err_path, "w", encoding="utf-8", errors="replace", buffering=1)
    prev_out, prev_err = sys.stdout, sys.stderr
    sys.stdout = _TeeTextStream(prev_out, out_f)
    sys.stderr = _TeeTextStream(prev_err, err_f)
    print(f"[run-log] stdout → {out_path}", flush=True)
    print(f"[run-log] stderr → {err_path}", flush=True)
    return out_f, err_f, prev_out, prev_err


def _uninstall_large_n_logging(out_f, err_f, prev_out, prev_err):
    if prev_out is None:
        return
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception:
        pass
    sys.stdout = prev_out
    sys.stderr = prev_err
    try:
        if out_f:
            out_f.close()
        if err_f:
            err_f.close()
    except Exception:
        pass


# ── Subconjuntos exactos de DatosPruebas2026_1.md ───────────────────────────

def casos_n10():
    """49 subconjuntos exactos — Sheet 10A-Elementos."""
    estado = "1000000000"
    pares = [
        ("ABCDEFGHIJ","ABCDEFGHIJ"),("ABCDEFGHIJ","ABCDEFGHI"),("ABCDEFGHIJ","BCDEFGHIJ"),
        ("ABCDEFGHIJ","BCDEFGHI"),("ABCDEFGHIJ","ABDEGHJ"),("ABCDEFGHIJ","ACEGI"),
        ("ABCDEFGHIJ","BDFHJ"),
        ("ABCDEFGHI","ABCDEFGHIJ"),("ABCDEFGHI","ABCDEFGHI"),("ABCDEFGHI","BCDEFGHIJ"),
        ("ABCDEFGHI","BCDEFGHI"),("ABCDEFGHI","ABDEGHJ"),("ABCDEFGHI","ACEGI"),
        ("ABCDEFGHI","BDFHJ"),
        ("BCDEFGHIJ","ABCDEFGHIJ"),("BCDEFGHIJ","ABCDEFGHI"),("BCDEFGHIJ","BCDEFGHIJ"),
        ("BCDEFGHIJ","BCDEFGHI"),("BCDEFGHIJ","ABDEGHJ"),("BCDEFGHIJ","ACEGI"),
        ("BCDEFGHIJ","BDFHJ"),
        ("BCDEFGHI","ABCDEFGHIJ"),("BCDEFGHI","ABCDEFGHI"),("BCDEFGHI","BCDEFGHIJ"),
        ("BCDEFGHI","BCDEFGHI"),("BCDEFGHI","ABDEGHJ"),("BCDEFGHI","ACEGI"),
        ("BCDEFGHI","BDFHJ"),
        ("ABDEGHJ","ABCDEFGHIJ"),("ABDEGHJ","ABCDEFGHI"),("ABDEGHJ","BCDEFGHIJ"),
        ("ABDEGHJ","BCDEFGHI"),("ABDEGHJ","ABDEGHJ"),("ABDEGHJ","ACEGI"),
        ("ABDEGHJ","BDFHJ"),
        ("ACEGI","ABCDEFGHIJ"),("ACEGI","ABCDEFGHI"),("ACEGI","BCDEFGHIJ"),
        ("ACEGI","BCDEFGHI"),("ACEGI","ABDEGHJ"),("ACEGI","ACEGI"),
        ("ACEGI","BDFHJ"),
        ("BDFHJ","ABCDEFGHIJ"),("BDFHJ","ABCDEFGHI"),("BDFHJ","BCDEFGHIJ"),
        ("BDFHJ","BCDEFGHI"),("BDFHJ","ABDEGHJ"),("BDFHJ","ACEGI"),
        ("BDFHJ","BDFHJ"),
    ]
    return 10, estado, pares


def casos_n15():
    """50 subconjuntos exactos — Sheet 15B-Elementos."""
    estado = "100000000000000"
    pares = [
        ("ABCDEFGHIJKLMNO","ABCDEFGHIJKLMNO"),("ABCDEFGHIJKLMNO","ABCDEFGHIJKLMN"),
        ("ABCDEFGHIJKLMNO","BCDEFGHIJKLMNO"),("ABCDEFGHIJKLMNO","BCDEFGHIJKLMN"),
        ("ABCDEFGHIJKLMNO","ABDEGHJKMN"),("ABCDEFGHIJKLMNO","ACEGIKMO"),
        ("ABCDEFGHIJKLMNO","BDFHJLN"),
        ("ABCDEFGHIJKLMN","ABCDEFGHIJKLMNO"),("ABCDEFGHIJKLMN","ABCDEFGHIJKLMN"),
        ("ABCDEFGHIJKLMN","BCDEFGHIJKLMNO"),("ABCDEFGHIJKLMN","BCDEFGHIJKLMN"),
        ("ABCDEFGHIJKLMN","ABDEGHJKMN"),("ABCDEFGHIJKLMN","ACEGIKMO"),
        ("ABCDEFGHIJKLMN","BDFHJLN"),
        ("BCDEFGHIJKLMNO","ABCDEFGHIJKLMNO"),("BCDEFGHIJKLMNO","ABCDEFGHIJKLMN"),
        ("BCDEFGHIJKLMNO","BCDEFGHIJKLMNO"),("BCDEFGHIJKLMNO","BCDEFGHIJKLMN"),
        ("BCDEFGHIJKLMNO","ABDEGHJKMN"),("BCDEFGHIJKLMNO","ACEGIKMO"),
        ("BCDEFGHIJKLMNO","BDFHJLN"),
        ("BCDEFGHIJKLMN","ABCDEFGHIJKLMNO"),("BCDEFGHIJKLMN","ABCDEFGHIJKLMN"),
        ("BCDEFGHIJKLMN","BCDEFGHIJKLMNO"),("BCDEFGHIJKLMN","BCDEFGHIJKLMN"),
        ("BCDEFGHIJKLMN","ABDEGHJKMN"),("BCDEFGHIJKLMN","ACEGIKMO"),
        ("BCDEFGHIJKLMN","BDFHJLN"),
        ("ABDEGHJKMN","ABCDEFGHIJKLMNO"),("ABDEGHJKMN","ABCDEFGHIJKLMN"),
        ("ABDEGHJKMN","BCDEFGHIJKLMNO"),("ABDEGHJKMN","BCDEFGHIJKLMN"),
        ("ABDEGHJKMN","ABDEGHJKMN"),("ABDEGHJKMN","ACEGIKMO"),
        ("ABDEGHJKMN","BDFHJLN"),
        ("ACEGIKMO","ABCDEFGHIJKLMNO"),("ACEGIKMO","ABCDEFGHIJKLMN"),
        ("ACEGIKMO","BCDEFGHIJKLMNO"),("ACEGIKMO","BCDEFGHIJKLMN"),
        ("ACEGIKMO","ABDEGHJKMN"),("ACEGIKMO","ACEGIKMO"),
        ("ACEGIKMO","BDFHJLN"),
        ("BDFHJLN","ABCDEFGHIJKLMNO"),("BDFHJLN","ABCDEFGHIJKLMN"),
        ("BDFHJLN","BCDEFGHIJKLMNO"),("BDFHJLN","BCDEFGHIJKLMN"),
        ("BDFHJLN","ABDEGHJKMN"),("BDFHJLN","ACEGIKMO"),
        ("BDFHJLN","BDFHJLN"),
        ("BCDEFGJKLMNO","BCDEFGHIJKLMNO"),   # caso 50
    ]
    return 15, estado, pares


def casos_n20():
    """50 subconjuntos exactos — Sheet 20A-Elementos."""
    estado = "10000000000000000000"
    pares = [
        ("ABCDEFGHIJKLMNOPQRST","ABCDEFGHIJKLMNOPQRST"),
        ("ABCDEFGHIJKLMNOPQRST","ABCDEFGHIJKLMNOPQRS"),
        ("ABCDEFGHIJKLMNOPQRST","BCDEFGHIJKLMNOPQRST"),
        ("ABCDEFGHIJKLMNOPQRST","BCDEFGHIJKLMNOPQRS"),
        ("ABCDEFGHIJKLMNOPQRST","ABDEGHJKMNPQST"),
        ("ABCDEFGHIJKLMNOPQRST","ACEGIKMOQS"),
        ("ABCDEFGHIJKLMNOPQRST","BDFHJLNPRT"),
        ("ABCDEFGHIJKLMNOPQRS","ABCDEFGHIJKLMNOPQRST"),
        ("ABCDEFGHIJKLMNOPQRS","ABCDEFGHIJKLMNOPQRS"),
        ("ABCDEFGHIJKLMNOPQRS","BCDEFGHIJKLMNOPQRST"),
        ("ABCDEFGHIJKLMNOPQRS","BCDEFGHIJKLMNOPQRS"),
        ("ABCDEFGHIJKLMNOPQRS","ABDEGHJKMNPQST"),
        ("ABCDEFGHIJKLMNOPQRS","ACEGIKMOQS"),
        ("ABCDEFGHIJKLMNOPQRS","BDFHJLNPRT"),
        ("BCDEFGHIJKLMNOPQRST","ABCDEFGHIJKLMNOPQRST"),
        ("BCDEFGHIJKLMNOPQRST","ABCDEFGHIJKLMNOPQRS"),
        ("BCDEFGHIJKLMNOPQRST","BCDEFGHIJKLMNOPQRST"),
        ("BCDEFGHIJKLMNOPQRST","BCDEFGHIJKLMNOPQRS"),
        ("BCDEFGHIJKLMNOPQRST","ABDEGHJKMNPQST"),
        ("BCDEFGHIJKLMNOPQRST","ACEGIKMOQS"),
        ("BCDEFGHIJKLMNOPQRST","BDFHJLNPRT"),
        ("BCDEFGHIJKLMNOPQRS","ABCDEFGHIJKLMNOPQRST"),
        ("BCDEFGHIJKLMNOPQRS","ABCDEFGHIJKLMNOPQRS"),
        ("BCDEFGHIJKLMNOPQRS","BCDEFGHIJKLMNOPQRST"),
        ("BCDEFGHIJKLMNOPQRS","BCDEFGHIJKLMNOPQRS"),
        ("BCDEFGHIJKLMNOPQRS","ABDEGHJKMNPQST"),
        ("BCDEFGHIJKLMNOPQRS","ACEGIKMOQS"),
        ("BCDEFGHIJKLMNOPQRS","BDFHJLNPRT"),
        ("ABDEGHJKMNPQST","ABCDEFGHIJKLMNOPQRST"),
        ("ABDEGHJKMNPQST","ABCDEFGHIJKLMNOPQRS"),
        ("ABDEGHJKMNPQST","BCDEFGHIJKLMNOPQRST"),
        ("ABDEGHJKMNPQST","BCDEFGHIJKLMNOPQRS"),
        ("ABDEGHJKMNPQST","ABDEGHJKMNPQST"),
        ("ABDEGHJKMNPQST","ACEGIKMOQS"),
        ("ABDEGHJKMNPQST","BDFHJLNPRT"),
        ("ACEGIKMOQS","ABCDEFGHIJKLMNOPQRST"),
        ("ACEGIKMOQS","ABCDEFGHIJKLMNOPQRS"),
        ("ACEGIKMOQS","BCDEFGHIJKLMNOPQRST"),
        ("ACEGIKMOQS","BCDEFGHIJKLMNOPQRS"),
        ("ACEGIKMOQS","ABDEGHJKMNPQST"),
        ("ACEGIKMOQS","ACEGIKMOQS"),
        ("ACEGIKMOQS","BDFHJLNPRT"),
        ("BDFHJLNPRT","ABCDEFGHIJKLMNOPQRST"),
        ("BDFHJLNPRT","ABCDEFGHIJKLMNOPQRS"),
        ("BDFHJLNPRT","BCDEFGHIJKLMNOPQRST"),
        ("BDFHJLNPRT","BCDEFGHIJKLMNOPQRS"),
        ("BDFHJLNPRT","ABDEGHJKMNPQST"),
        ("BDFHJLNPRT","ACEGIKMOQS"),
        ("BDFHJLNPRT","BDFHJLNPRT"),
        ("BCDEFGJKLMNO","BCDEFGHIJKLMNO"),    # caso 50
    ]
    return 20, estado, pares


def casos_n22():
    """50 subconjuntos exactos — Sheet 22A-Elementos."""
    estado = "1000000000000000000000"
    pares = [
        ("ABCDEFGHIJKLMNOPQRSTUV","ABCDEFGHIJKLMNOPQRSTUV"),
        ("ABCDEFGHIJKLMNOPQRSTUV","ABCDEFGHIJKLMNOPQRSTU"),
        ("ABCDEFGHIJKLMNOPQRSTUV","BCDEFGHIJKLMNOPQRSTUV"),
        ("ABCDEFGHIJKLMNOPQRSTUV","BCDEFGHIJKLMNOPQRSTU"),
        ("ABCDEFGHIJKLMNOPQRSTUV","ABDEGHJKMNPQSTV"),
        ("ABCDEFGHIJKLMNOPQRSTUV","ACEGIKMOQSU"),
        ("ABCDEFGHIJKLMNOPQRSTUV","BDFHJLNPRTV"),
        ("ABCDEFGHIJKLMNOPQRSTU","ABCDEFGHIJKLMNOPQRSTUV"),
        ("ABCDEFGHIJKLMNOPQRSTU","ABCDEFGHIJKLMNOPQRSTU"),
        ("ABCDEFGHIJKLMNOPQRSTU","BCDEFGHIJKLMNOPQRSTUV"),
        ("ABCDEFGHIJKLMNOPQRSTU","BCDEFGHIJKLMNOPQRSTU"),
        ("ABCDEFGHIJKLMNOPQRSTU","ABDEGHJKMNPQSTV"),
        ("ABCDEFGHIJKLMNOPQRSTU","ACEGIKMOQSU"),
        ("ABCDEFGHIJKLMNOPQRSTU","BDFHJLNPRTV"),
        ("BCDEFGHIJKLMNOPQRSTUV","ABCDEFGHIJKLMNOPQRSTUV"),
        ("BCDEFGHIJKLMNOPQRSTUV","ABCDEFGHIJKLMNOPQRSTU"),
        ("BCDEFGHIJKLMNOPQRSTUV","BCDEFGHIJKLMNOPQRSTUV"),
        ("BCDEFGHIJKLMNOPQRSTUV","BCDEFGHIJKLMNOPQRSTU"),
        ("BCDEFGHIJKLMNOPQRSTUV","ABDEGHJKMNPQSTV"),
        ("BCDEFGHIJKLMNOPQRSTUV","ACEGIKMOQSU"),
        ("BCDEFGHIJKLMNOPQRSTUV","BDFHJLNPRTV"),
        ("BCDEFGHIJKLMNOPQRSTU","ABCDEFGHIJKLMNOPQRSTUV"),
        ("BCDEFGHIJKLMNOPQRSTU","ABCDEFGHIJKLMNOPQRSTU"),
        ("BCDEFGHIJKLMNOPQRSTU","BCDEFGHIJKLMNOPQRSTUV"),
        ("BCDEFGHIJKLMNOPQRSTU","BCDEFGHIJKLMNOPQRSTU"),
        ("BCDEFGHIJKLMNOPQRSTU","ABDEGHJKMNPQSTV"),
        ("BCDEFGHIJKLMNOPQRSTU","ACEGIKMOQSU"),
        ("BCDEFGHIJKLMNOPQRSTU","BDFHJLNPRTV"),
        ("ABDEGHJKMNPQSTV","ABCDEFGHIJKLMNOPQRSTUV"),
        ("ABDEGHJKMNPQSTV","ABCDEFGHIJKLMNOPQRSTU"),
        ("ABDEGHJKMNPQSTV","BCDEFGHIJKLMNOPQRSTUV"),
        ("ABDEGHJKMNPQSTV","BCDEFGHIJKLMNOPQRSTU"),
        ("ABDEGHJKMNPQSTV","ABDEGHJKMNPQSTV"),
        ("ABDEGHJKMNPQSTV","ACEGIKMOQSU"),
        ("ABDEGHJKMNPQSTV","BDFHJLNPRTV"),
        ("ACEGIKMOQSU","ABCDEFGHIJKLMNOPQRSTUV"),
        ("ACEGIKMOQSU","ABCDEFGHIJKLMNOPQRSTU"),
        ("ACEGIKMOQSU","BCDEFGHIJKLMNOPQRSTUV"),
        ("ACEGIKMOQSU","BCDEFGHIJKLMNOPQRSTU"),
        ("ACEGIKMOQSU","ABDEGHJKMNPQSTV"),
        ("ACEGIKMOQSU","ACEGIKMOQSU"),
        ("ACEGIKMOQSU","BDFHJLNPRTV"),
        ("BDFHJLNPRTV","ABCDEFGHIJKLMNOPQRSTUV"),
        ("BDFHJLNPRTV","ABCDEFGHIJKLMNOPQRSTU"),
        ("BDFHJLNPRTV","BCDEFGHIJKLMNOPQRSTUV"),
        ("BDFHJLNPRTV","BCDEFGHIJKLMNOPQRSTU"),
        ("BDFHJLNPRTV","ABDEGHJKMNPQSTV"),
        ("BDFHJLNPRTV","ACEGIKMOQSU"),
        ("BDFHJLNPRTV","BDFHJLNPRTV"),
        ("ACDEFGHIJKLMNOPQRST","ACDEFGHIJKLMNOPQRST"),   # caso 50
    ]
    return 22, estado, pares


def casos_n25():
    """50 subconjuntos exactos — Sheet 25A-Elementos."""
    estado = "1000000000000000000000000"
    pares = [
        ("ABCDEFGHIJKLMNOPQRSTUVWXY","ABCDEFGHIJKLMNOPQRSTUVWXY"),
        ("ABCDEFGHIJKLMNOPQRSTUVWXY","ABCDEFGHIJKLMNOPQRSTUVWX"),
        ("ABCDEFGHIJKLMNOPQRSTUVWXY","BCDEFGHIJKLMNOPQRSTUVWXY"),
        ("ABCDEFGHIJKLMNOPQRSTUVWXY","BCDEFGHIJKLMNOPQRSTUVWX"),
        ("ABCDEFGHIJKLMNOPQRSTUVWXY","ABDEGHJKMNPQSTVWY"),
        ("ABCDEFGHIJKLMNOPQRSTUVWXY","ACEGIKMOQSUWY"),
        ("ABCDEFGHIJKLMNOPQRSTUVWXY","BDFHJLNPRTVX"),
        ("ABCDEFGHIJKLMNOPQRSTUVWX","ABCDEFGHIJKLMNOPQRSTUVWXY"),
        ("ABCDEFGHIJKLMNOPQRSTUVWX","ABCDEFGHIJKLMNOPQRSTUVWX"),
        ("ABCDEFGHIJKLMNOPQRSTUVWX","BCDEFGHIJKLMNOPQRSTUVWXY"),
        ("ABCDEFGHIJKLMNOPQRSTUVWX","BCDEFGHIJKLMNOPQRSTUVWX"),
        ("ABCDEFGHIJKLMNOPQRSTUVWX","ABDEGHJKMNPQSTVWY"),
        ("ABCDEFGHIJKLMNOPQRSTUVWX","ACEGIKMOQSUWY"),
        ("ABCDEFGHIJKLMNOPQRSTUVWX","BDFHJLNPRTVX"),
        ("BCDEFGHIJKLMNOPQRSTUVWXY","ABCDEFGHIJKLMNOPQRSTUVWXY"),
        ("BCDEFGHIJKLMNOPQRSTUVWXY","ABCDEFGHIJKLMNOPQRSTUVWX"),
        ("BCDEFGHIJKLMNOPQRSTUVWXY","BCDEFGHIJKLMNOPQRSTUVWXY"),
        ("BCDEFGHIJKLMNOPQRSTUVWXY","BCDEFGHIJKLMNOPQRSTUVWX"),
        ("BCDEFGHIJKLMNOPQRSTUVWXY","ABDEGHJKMNPQSTVWY"),
        ("BCDEFGHIJKLMNOPQRSTUVWXY","ACEGIKMOQSUWY"),
        ("BCDEFGHIJKLMNOPQRSTUVWXY","BDFHJLNPRTVX"),
        ("BCDEFGHIJKLMNOPQRSTUVWX","ABCDEFGHIJKLMNOPQRSTUVWXY"),
        ("BCDEFGHIJKLMNOPQRSTUVWX","ABCDEFGHIJKLMNOPQRSTUVWX"),
        ("BCDEFGHIJKLMNOPQRSTUVWX","BCDEFGHIJKLMNOPQRSTUVWXY"),
        ("BCDEFGHIJKLMNOPQRSTUVWX","BCDEFGHIJKLMNOPQRSTUVWX"),
        ("BCDEFGHIJKLMNOPQRSTUVWX","ABDEGHJKMNPQSTVWY"),
        ("BCDEFGHIJKLMNOPQRSTUVWX","ACEGIKMOQSUWY"),
        ("BCDEFGHIJKLMNOPQRSTUVWX","BDFHJLNPRTVX"),
        ("ABDEGHJKMNPQSTVWY","ABCDEFGHIJKLMNOPQRSTUVWXY"),
        ("ABDEGHJKMNPQSTVWY","ABCDEFGHIJKLMNOPQRSTUVWX"),
        ("ABDEGHJKMNPQSTVWY","BCDEFGHIJKLMNOPQRSTUVWXY"),
        ("ABDEGHJKMNPQSTVWY","BCDEFGHIJKLMNOPQRSTUVWX"),
        ("ABDEGHJKMNPQSTVWY","ABDEGHJKMNPQSTVWY"),
        ("ABDEGHJKMNPQSTVWY","ACEGIKMOQSUWY"),
        ("ABDEGHJKMNPQSTVWY","BDFHJLNPRTVX"),
        ("ACEGIKMOQSUWY","ABCDEFGHIJKLMNOPQRSTUVWXY"),
        ("ACEGIKMOQSUWY","ABCDEFGHIJKLMNOPQRSTUVWX"),
        ("ACEGIKMOQSUWY","BCDEFGHIJKLMNOPQRSTUVWXY"),
        ("ACEGIKMOQSUWY","BCDEFGHIJKLMNOPQRSTUVWX"),
        ("ACEGIKMOQSUWY","ABDEGHJKMNPQSTVWY"),
        ("ACEGIKMOQSUWY","ACEGIKMOQSUWY"),
        ("ACEGIKMOQSUWY","BDFHJLNPRTVX"),
        ("BDFHJLNPRTVX","ABCDEFGHIJKLMNOPQRSTUVWXY"),
        ("BDFHJLNPRTVX","ABCDEFGHIJKLMNOPQRSTUVWX"),
        ("BDFHJLNPRTVX","BCDEFGHIJKLMNOPQRSTUVWXY"),
        ("BDFHJLNPRTVX","BCDEFGHIJKLMNOPQRSTUVWX"),
        ("BDFHJLNPRTVX","ABDEGHJKMNPQSTVWY"),
        ("BDFHJLNPRTVX","ACEGIKMOQSUWY"),
        ("BDFHJLNPRTVX","BDFHJLNPRTVX"),
        ("ACDEFGHIJKLMNOPQRSTVX","ACDEFGHIJKLMNOPQRSTVX"),  # caso 50
    ]
    return 25, estado, pares


CASOS = {10: casos_n10, 15: casos_n15, 20: casos_n20, 22: casos_n22, 25: casos_n25}


# ── Conversión letras → binario ──────────────────────────────────────────────
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def letters_to_binary(text: str, n: int) -> str:
    positions = ALPHABET[:n]
    mask = ["0"] * n
    for ch in text.strip().upper():
        if ch in positions:
            mask[positions.index(ch)] = "1"
    return "".join(mask)


# ── Timeout thread-based (Windows) ───────────────────────────────────────────
def _run_with_timeout(func, timeout_seconds):
    result_holder = [None]
    exc_holder    = [None]

    def worker():
        try:
            result_holder[0] = func()
        except BaseException as e:
            exc_holder[0] = e

    import threading
    threading.stack_size(64 * 1024 * 1024)
    t  = threading.Thread(target=worker, daemon=True)
    t0 = time.perf_counter()
    t.start()
    t.join(timeout=timeout_seconds)
    elapsed   = time.perf_counter() - t0
    timed_out = t.is_alive()
    return result_holder[0], elapsed, timed_out, exc_holder[0]


# ── Ejecutar una estrategia ───────────────────────────────────────────────────
def run_strategy(strategy_cls, init_kwargs, call_kwargs,
                 cond, alcance, mec, tpm=None, timeout=DEFAULT_TIMEOUT):
    result = {"particion": None, "perdida": None, "tiempo_ms": None,
              "convergio": False, "error": None}

    def task():
        tracemalloc.start()
        strat = strategy_cls(**init_kwargs, **call_kwargs)
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
            result["error"] = f"TIMEOUT>{timeout}s"
            result["tiempo_ms"] = elapsed * 1000
        elif exc:
            result["error"] = str(exc)[:120]
            result["tiempo_ms"] = elapsed * 1000
        else:
            sol, _ = sol_peak
            result["particion"]  = str(sol.particion) if sol else None
            result["perdida"]    = float(sol.perdida) if sol and sol.perdida is not None else None
            result["tiempo_ms"]  = elapsed * 1000
            result["convergio"]  = True
    except Exception as e:
        result["error"] = str(e)[:120]
    return result


# ── Heurística: recomendar k óptimo ──────────────────────────────────────────
def heuristica_k_optimo(fila: dict) -> dict:
    """
    Dado un dict con las pérdidas y tiempos de k=2,3,4,5,
    recomienda el k que maximiza la relación mejora_perdida / aumento_tiempo.

    Funciona con columnas QN/KL (benchmark estándar) o MCTS_* si algún ejecutable
      antiguo lo generó explícitamente.
    Retorna: {k_recomendado, estrategia_recomendada, razon, detalle}
    """
    base_perdida = {}
    base_tiempo  = {}

    # Columnas greedies (nombre histórico "QN_*" = mismo prefijo para n grandes)
    tiene_mcts = "MCTS_k2_perdida" in fila

    if tiene_mcts:
        estrategias = [("MCTS", "MCTS")]
        for prefijo, _ in estrategias:
            base_perdida[prefijo] = fila.get(f"{prefijo}_k2_perdida")
            base_tiempo[prefijo] = fila.get(f"{prefijo}_k2_tiempo_ms") or 1
    else:
        estrategias = [
            ("QN", "QNodes-Greedy"),
            ("KL", "KL"),
        ]
        for prefijo, _ in estrategias:
            base_perdida[prefijo] = fila.get(f"{prefijo}_k2_perdida")
            base_tiempo[prefijo] = fila.get(f"{prefijo}_k2_tiempo_ms") or 1

    # Fallback: usar Geo k=2 como base si ningún prefijo existe
    base_geo2 = fila.get("Geo_k2_perdida")
    t_geo2    = fila.get("Geo_k2_tiempo_ms") or 1

    best_k, best_strat, best_score = 2, "Geometric k=2", -1.0

    for k in [3, 4, 5]:
        for prefijo, nombre in estrategias:
            p = fila.get(f"{prefijo}_k{k}_perdida")
            t = fila.get(f"{prefijo}_k{k}_tiempo_ms") or 1
            base_p = base_perdida.get(prefijo) or base_geo2
            base_t = base_tiempo.get(prefijo)  or t_geo2
            if base_p is not None and p is not None:
                mejora = max(0, base_p - p)
                razon  = mejora / (t / base_t) if t > 0 else 0
                if razon > best_score:
                    best_score, best_k, best_strat = razon, k, nombre

    return {
        "heuristica_k": best_k,
        "heuristica_estrategia": best_strat,
        "heuristica_score": round(best_score, 6),
    }


# ── Benchmark principal ───────────────────────────────────────────────────────
def run_benchmark(ns: list[int], timeout: int) -> dict[int, pd.DataFrame]:
    """Retorna un dict {n: DataFrame} con formato ancho (1 fila por caso)."""
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
            print(f"[SKIP] n={n}: sin TPM en {SAMPLES_DIR}")
            continue

        # Todas las estrategias del caso comparten el mismo límite (segundos por hebra).
        # El CLI --timeout marca el tope máximo por estrategia (no usar min con 1800,
        # eso impedía lanzar cortas de 5–6 h aun pasando --timeout alto).
        if n <= 10:
            case_to = timeout
        elif n <= 15:
            case_to = timeout
        else:
            case_to = min(timeout, 86400)

        print(f"\n{'='*65}")
        print(f"n={n}  TPM={tpm_path.name}  casos={len(pares)}  timeout={case_to}s/estrategia")
        print(f"{'='*65}")

        tpm = np.asarray(np.genfromtxt(tpm_path, delimiter=","), dtype=np.float64)
        rows = []

        usar_qnodes = n <= 15

        for idx, (purview, mec_str) in enumerate(pares, 1):
            alcance   = letters_to_binary(purview,  n_val)
            mecanismo = letters_to_binary(mec_str,  n_val)
            condicion = "1" * n_val

            print(f"  #{idx:>3}/{len(pares)}  {purview[:14]:<14} / {mec_str[:14]}", end="", flush=True)

            # Limpiar caché entre casos: cada caso tiene distintos (alcance,mecanismo),
            # por lo que el caché del caso anterior no es reutilizable y ocupa memoria.
            limpiar_cache_subsistemas()
            limpiar_cache_find_mip()

            row = {"#Prueba": idx, "Purview": purview, "Mecanismo": mec_str}
            gestor = lambda: Manager(estado_inicial=estado)

            # ── k=2  QNodes (solo n<=15) ─────────────────────────────────────
            if usar_qnodes:
                r = run_strategy(QNodes, {"gestor": gestor()}, {},
                                 condicion, alcance, mecanismo, tpm, case_to)
                row["QN_k2_particion"] = r["particion"]
                row["QN_k2_perdida"]   = r["perdida"]
                row["QN_k2_tiempo_ms"] = r["tiempo_ms"]
                print(f"  QN2={'.' if r['convergio'] else 'X'}", end="", flush=True)
            else:
                row["QN_k2_particion"] = "N/A (n>=20)"
                row["QN_k2_perdida"]   = None
                row["QN_k2_tiempo_ms"] = None

            # ── k=2  GeometricSIA ────────────────────────────────────────────
            r = run_strategy(GeometricSIA, {"gestor": gestor()}, {},
                             condicion, alcance, mecanismo, tpm, case_to)
            row["Geo_k2_particion"] = r["particion"]
            row["Geo_k2_perdida"]   = r["perdida"]
            row["Geo_k2_tiempo_ms"] = r["tiempo_ms"]
            print(f"  Geo2={'.' if r['convergio'] else 'X'}", end="", flush=True)

            # ── k=3,4,5 Greedy + KL (mismo esquema n pequeños y grandes; find_mip
            # está memoizado dentro del caso tras la corrida Geo k=2)
            for k in [3, 4, 5]:
                heuristicas = [
                    ("greedy", "QN"),
                    ("kl", "KL"),
                ]
                simbolos = []
                for heur, prefijo in heuristicas:
                    r = run_strategy(
                        KPartitionSIA,
                        {"gestor": gestor()},
                        {"k": k, "forzar_heuristica": heur},
                        condicion,
                        alcance,
                        mecanismo,
                        tpm,
                        case_to,
                    )
                    row[f"{prefijo}_k{k}_particion"] = r["particion"]
                    row[f"{prefijo}_k{k}_perdida"] = r["perdida"]
                    row[f"{prefijo}_k{k}_tiempo_ms"] = r["tiempo_ms"]
                    simbolos.append("." if r["convergio"] else "X")

                print(f"  k{k}(QN{simbolos[0]}/KL{simbolos[1]})", end="", flush=True)

            # ── Heurística ───────────────────────────────────────────────────
            row.update(heuristica_k_optimo(row))
            print()
            rows.append(row)

            # Checkpoint cada 5 casos
            if idx % 5 == 0:
                _checkpoint(pd.DataFrame(rows), n)

        df = pd.DataFrame(rows)
        _checkpoint(df, n)   # checkpoint final de cada n
        resultados[n] = df
        print(f"  n={n} completado: {len(df)} filas")

    return resultados


def _carpeta_n(n: int) -> Path:
    """Devuelve (y crea si no existe) la carpeta GeoMIP/results/n{n}/."""
    p = RESULTS_DIR / f"n{n}"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _checkpoint(df: pd.DataFrame, n: int):
    ts   = datetime.now().strftime("%Y-%m-%d_%Hh%M")
    path = _carpeta_n(n) / f"checkpoint_{ts}.xlsx"
    try:
        df.to_excel(path, index=False)
    except Exception:
        pass


# ── Guardar resultado final ───────────────────────────────────────────────────
def save_results(resultados: dict[int, pd.DataFrame]):
    ts = datetime.now().strftime("%Y-%m-%d_%Hh%M")

    # Un Excel por red en su carpeta individual
    for n, df in sorted(resultados.items()):
        out_n = _carpeta_n(n) / f"n{n}_completo_{ts}.xlsx"
        df.to_excel(out_n, index=False)
        print(f"  n={n} guardado en: {out_n}")

    # Excel consolidado en la raíz de results/
    out = RESULTS_DIR / f"benchmark_completo_{ts}.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as xw:
        for n, df in sorted(resultados.items()):
            df.to_excel(xw, sheet_name=f"n{n}", index=False)

        filas_h = []
        for n, df in sorted(resultados.items()):
            if "heuristica_k" in df.columns:
                dist = df["heuristica_k"].value_counts().to_dict()
                filas_h.append({"n": n, **{f"k={k}": dist.get(k, 0) for k in [2,3,4,5]}})
        if filas_h:
            pd.DataFrame(filas_h).to_excel(xw, sheet_name="Heuristica_resumen", index=False)

    print(f"\nConsolidado: {out}")
    return out


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Benchmark K-QGMIP — DatosPruebas2026")
    parser.add_argument("--n", nargs="+", type=int, default=[10, 15, 20, 22, 25])
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help="Segundos por estrategia y caso (default=%(default)s; use p.ej. 21600 para n>=20)")
    parser.add_argument("--no-run-log", action="store_true",
                        help="No escribir logs con fecha en logs/n20_plus/ cuando n≥20")
    args = parser.parse_args()

    out_f = err_f = prev_out = prev_err = None
    if not args.no_run_log:
        out_f, err_f, prev_out, prev_err = _install_large_n_logging(args.n)

    try:
        print(f"Benchmark K-QGMIP - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"  n={args.n}  timeout_max={args.timeout}s")
        print(f"  samples: {SAMPLES_DIR}")

        resultados = run_benchmark(args.n, args.timeout)

        if resultados:
            out = save_results(resultados)
            total = sum(len(df) for df in resultados.values())
            print(f"Total filas: {total}")
        else:
            print("Sin resultados.")
    finally:
        if not args.no_run_log:
            _uninstall_large_n_logging(out_f, err_f, prev_out, prev_err)


if __name__ == "__main__":
    main()
