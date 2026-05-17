"""Compara las 4 heurísticas en varios casos de n=10 para ver patrones."""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent / "Method2_Dynamic_Programming_Reformulation"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import benchmark as bm
from src.controllers.manager import Manager
from src.controllers.strategies.kpartition import KPartitionSIA

tpm = np.genfromtxt(
    Path(__file__).resolve().parent.parent / "data" / "samples" / "N10A.csv",
    delimiter=","
)
n, estado, pares = bm.casos_n10()

# Probar casos representativos: sistema completo, subsistema grande, subsistema mediano, subsistema pequeño
indices_test = [0, 7, 22, 40]  # casos 1, 8, 23, 41 del Excel

print(f"{'Caso':<30} {'Heur':<12} k  {'Pérdida':>10}")
print("-" * 60)

for idx in indices_test:
    pur, mec = pares[idx]
    alcance   = bm.letters_to_binary(pur, 10)
    mecanismo = bm.letters_to_binary(mec, 10)
    condicion = "1" * 10
    etiqueta  = f"#{idx+1} {pur[:8]}/{mec[:8]}"

    for heur, nombre in [("greedy","Greedy"), ("kl","KL"), ("spectral","Spectral")]:
        for k in [3]:
            r = bm.run_strategy(
                KPartitionSIA,
                {"gestor": Manager(estado_inicial=estado)},
                {"k": k, "forzar_heuristica": heur},
                condicion, alcance, mecanismo, tpm, 30
            )
            perd = f"{r['perdida']:.6f}" if r["perdida"] is not None else "None"
            print(f"{etiqueta:<30} {nombre:<12} {k}  {perd:>10}")
    print()
