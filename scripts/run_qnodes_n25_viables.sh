#!/usr/bin/env bash
# QNodes k=2 n=25 — casos viables (misma logica estructural que n=22).
# Omitidos pesados: sistema completo (#1-4, #8-11, #15), bloque BCDEF denso
# (#16-18, #22-25) y caso especial #50.
export PATH="$HOME/.local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$HOME/.venvs/kqgmip}"
cd "/mnt/c/Users/Manu/Documents/Semestre 2026 - 01/Analisis y diseño de algoritmos/proyecto/projecto-analisis-20261/GeoMIP/src/Method2_Dynamic_Programming_Reformulation"

CASOS_VIABLES="5 6 7 12 13 14 19 20 21 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49"
N_CASOS=33

echo "========== QNodes n=25 — casos viables ($N_CASOS casos) =========="
echo "Omitidos (pesados): 1 2 3 4 8 9 10 11 15 16 17 18 22 23 24 25 50"
echo "TPM: N25A.csv (~3.4 GB, carga ~5-10 min)"
echo "Inicio: $(date -Iseconds)"
echo ""

uv run python -u ../run_qnodes_k2.py --n 25 --merge --casos $CASOS_VIABLES

echo ""
echo "Fin: $(date -Iseconds)"
