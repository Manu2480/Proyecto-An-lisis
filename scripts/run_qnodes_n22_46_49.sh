#!/usr/bin/env bash
export PATH="$HOME/.local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$HOME/.venvs/kqgmip}"
ROOT="/mnt/c/Users/Manu/Documents/Semestre 2026 - 01/Analisis y diseño de algoritmos/proyecto/projecto-analisis-20261"
cd "$ROOT/GeoMIP/src/Method2_Dynamic_Programming_Reformulation"
echo "========== QNodes n=22 — casos 46-49 (fix merge) =========="
echo "Inicio: $(date -Iseconds)"
uv run python -u ../run_qnodes_k2.py --n 22 --merge --casos 46 47 48 49
echo "Fin: $(date -Iseconds)"
