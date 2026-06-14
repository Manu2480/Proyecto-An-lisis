#!/usr/bin/env bash
# Smoke timing QNodes memo en un caso n=20 (#2).
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$HOME/.venvs/kqgmip}"
ROOT="/mnt/c/Users/Manu/Documents/Semestre 2026 - 01/Analisis y diseño de algoritmos/proyecto/projecto-analisis-20261"
cd "$ROOT/GeoMIP/src/Method2_Dynamic_Programming_Reformulation"
uv run python -u - <<'PY'
import sys
import time
from pathlib import Path

BENCH = Path("..").resolve()
sys.path.insert(0, str(BENCH))
sys.path.insert(0, str(Path.cwd()))

from benchmark import CASOS, letters_to_binary, run_strategy
from geomip_paths import SAMPLES_DIR
from tpm_io import load_tpm
from src.controllers.manager import Manager
from src.controllers.strategies.q_nodes import QNodes
from src.models.base.sia import limpiar_cache_subsistemas
from src.middlewares.profile import profiler_manager

profiler_manager.enabled = False

n = 20
_, estado, pares = CASOS[n]()
purview, mec_str = pares[1]
n_val = len(estado)
condicion = "1" * n_val
alcance = letters_to_binary(purview, n_val)
mecanismo = letters_to_binary(mec_str, n_val)
tpm = load_tpm(SAMPLES_DIR / f"N{n}A.csv", n_val)

limpiar_cache_subsistemas()
t0 = time.perf_counter()
r = run_strategy(
    QNodes,
    {"gestor": Manager(estado_inicial=estado)},
    {},
    condicion,
    alcance,
    mecanismo,
    tpm,
    21600,
)
dt = time.perf_counter() - t0
print(
    f"n={n} caso=2 perdida={r['perdida']} "
    f"tiempo_ms={r['tiempo_ms']} wall_s={dt:.1f} convergio={r['convergio']}"
)
PY
