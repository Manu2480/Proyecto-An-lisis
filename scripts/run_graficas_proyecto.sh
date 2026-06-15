#!/usr/bin/env bash
export PATH="$HOME/.local/bin:$PATH"
VENV="${UV_PROJECT_ENVIRONMENT:-$HOME/.venvs/kqgmip}"
ROOT="/mnt/c/Users/Manu/Documents/Semestre 2026 - 01/Analisis y diseño de algoritmos/proyecto/projecto-analisis-20261"
PY="$VENV/bin/python3"
uv pip install --python "$PY" matplotlib seaborn
"$PY" "$ROOT/scripts/generar_graficas_proyecto.py"
