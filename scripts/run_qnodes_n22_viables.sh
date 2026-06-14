#!/usr/bin/env bash
# Casos n=22 viables en <15 min c/u (evita pesados #16-18, #22-25, #50).
# Ligero: mecanismo ABDEG/ACEGI/BDFHJ (#19-21, #26-28)
# Medio: purview 11-12 nodos (#29-49)
export PATH="$HOME/.local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$HOME/.venvs/kqgmip}"
cd "/mnt/c/Users/Manu/Documents/Semestre 2026 - 01/Analisis y diseño de algoritmos/proyecto/projecto-analisis-20261/GeoMIP/src/Method2_Dynamic_Programming_Reformulation"

CASOS_VIABLES="19 20 21 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49"

echo "========== QNodes n=22 — casos viables (${#CASOS_VIABLES[@]} nums) =========="
echo "Omitidos (pesados): 16 17 18 22 23 24 25 50"
echo "Merge con checkpoint existente (15 casos previos)"
echo "Inicio: $(date -Iseconds)"
echo ""

uv run python -u ../run_qnodes_k2.py --n 22 --merge --casos $CASOS_VIABLES

echo ""
echo "Fin: $(date -Iseconds)"
