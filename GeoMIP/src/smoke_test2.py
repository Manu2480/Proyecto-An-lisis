"""Smoke test de las 4 heurísticas (greedy, kl, clustering, spectral) en n=10."""
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
pur, mec = pares[0]
alcance   = bm.letters_to_binary(pur, 10)
mecanismo = bm.letters_to_binary(mec, 10)
condicion = "1" * 10

print(f"Caso: {pur} / {mec}")
print(f"{'Heurística':<14} {'k':>3}  {'Pérdida':>10}  {'Tiempo(ms)':>12}  Error")
print("-" * 55)

for heur, nombre in [("greedy","Greedy"), ("kl","KL"),
                     ("clustering","Clustering"), ("spectral","Spectral")]:
    for k in [3, 5]:
        r = bm.run_strategy(
            KPartitionSIA,
            {"gestor": Manager(estado_inicial=estado)},
            {"k": k, "forzar_heuristica": heur},
            condicion, alcance, mecanismo, tpm, 60
        )
        err  = r["error"] or ""
        perd = f"{r['perdida']:.6f}" if r["perdida"] is not None else "None"
        t_ms = f"{r['tiempo_ms']:.0f}" if r["tiempo_ms"] is not None else "None"
        print(f"{nombre:<14} {k:>3}  {perd:>10}  {t_ms:>12}  {err}")

print("\nSmoke test 2 completado.")
