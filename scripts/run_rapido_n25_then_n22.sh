#!/usr/bin/env bash
# n=25 primero, luego n=22 (con validacion en cada checkpoint).
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$HOME/.venvs/kqgmip}"
export PYTHONUNBUFFERED=1

ROOT="/mnt/c/Users/Manu/Documents/Semestre 2026 - 01/Analisis y diseño de algoritmos/proyecto/projecto-analisis-20261"
SCRIPT="$ROOT/scripts/run_rapido_y_auditar.sh"

echo "========== COLA: n=25 -> n=22 =========="
echo "Inicio: $(date -Iseconds)"

bash "$SCRIPT" 25
echo ""
echo "n=25 terminado OK. Iniciando n=22..."
echo ""

bash "$SCRIPT" 22
echo ""
echo "Cola completada: $(date -Iseconds)"
