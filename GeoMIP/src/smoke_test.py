"""Prueba de humo: 1 caso n=10 con QNodes y Geometric."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

METHOD2 = Path(__file__).resolve().parent / "Method2_Dynamic_Programming_Reformulation"
sys.path.insert(0, str(METHOD2))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import benchmark as bm
from src.controllers.manager import Manager
from src.controllers.strategies.q_nodes import QNodes
from src.controllers.strategies.geometric import GeometricSIA
from src.controllers.strategies.kpartition import KPartitionSIA

SAMPLES = Path(__file__).resolve().parent.parent / "data" / "samples"

tpm_path = SAMPLES / "N10A.csv"
tpm = np.genfromtxt(tpm_path, delimiter=",")

n, estado, pares = bm.casos_n10()
print(f"n={n}  casos={len(pares)}  TPM={tpm.shape}")

pur, mec = pares[0]
alcance   = bm.letters_to_binary(pur, n)
mecanismo = bm.letters_to_binary(mec, n)
condicion = "1" * n
print(f"Caso 1: {pur} / {mec}")
print(f"  alcance  ={alcance}")
print(f"  mecanismo={mecanismo}")

# QNodes k=2
r = bm.run_strategy(QNodes, {"gestor": Manager(estado_inicial=estado)}, {},
                    condicion, alcance, mecanismo, tpm, 60)
print(f"  QNodes k=2: perdida={r['perdida']}  t={r['tiempo_ms']:.1f}ms  err={r['error']}")

# Geometric k=2
r = bm.run_strategy(GeometricSIA, {"gestor": Manager(estado_inicial=estado)}, {},
                    condicion, alcance, mecanismo, tpm, 60)
print(f"  Geo    k=2: perdida={r['perdida']}  t={r['tiempo_ms']:.1f}ms  err={r['error']}")

# KPartition k=3 greedy
r = bm.run_strategy(KPartitionSIA, {"gestor": Manager(estado_inicial=estado)},
                    {"k": 3, "forzar_heuristica": "greedy"},
                    condicion, alcance, mecanismo, tpm, 60)
print(f"  QNodes k=3: perdida={r['perdida']}  t={r['tiempo_ms']:.1f}ms  err={r['error']}")

# KPartition k=3 clustering
r = bm.run_strategy(KPartitionSIA, {"gestor": Manager(estado_inicial=estado)},
                    {"k": 3, "forzar_heuristica": "clustering"},
                    condicion, alcance, mecanismo, tpm, 60)
print(f"  Geo    k=3: perdida={r['perdida']}  t={r['tiempo_ms']:.1f}ms  err={r['error']}")

print("\nSmoke test OK")
