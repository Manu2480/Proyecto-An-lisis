#!/usr/bin/env bash
# Corrida rapida de una red + auditoria de particiones (grupos vs k).
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$HOME/.venvs/kqgmip}"
export PYTHONUNBUFFERED=1

N="${1:?Uso: run_rapido_y_auditar.sh <n>}"
ROOT="/mnt/c/Users/Manu/Documents/Semestre 2026 - 01/Analisis y diseño de algoritmos/proyecto/projecto-analisis-20261"
cd "$ROOT/GeoMIP/src/Method2_Dynamic_Programming_Reformulation"

echo "========== BENCHMARK RAPIDO n=$N =========="
uv run python -u ../benchmark_rapido.py --n "$N" --no-merge

echo ""
echo "========== AUDITORIA n=$N =========="
uv run python -u ../../../scripts/audit_rapido_una.py --n "$N"
