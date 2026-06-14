#!/usr/bin/env bash
export PATH="$HOME/.local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$HOME/.venvs/kqgmip}"
cd "/mnt/c/Users/Manu/Documents/Semestre 2026 - 01/Analisis y diseño de algoritmos/proyecto/projecto-analisis-20261"
uv run python scripts/limpiar_results.py
