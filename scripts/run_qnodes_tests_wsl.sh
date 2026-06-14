#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$HOME/.venvs/kqgmip}"
ROOT="/mnt/c/Users/Manu/Documents/Semestre 2026 - 01/Analisis y diseño de algoritmos/proyecto/projecto-analisis-20261"
cd "$ROOT/GeoMIP/src/Method2_Dynamic_Programming_Reformulation"
uv sync
uv run python -m pytest "$ROOT/tests/test_qnodes_memo.py" -v --tb=short
