#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
R = Path(__file__).resolve().parents[1] / "GeoMIP/data/results"
qn = pd.read_excel(R / "n10/qnodes_k2_n10_2026-06-13_10h24.xlsx")
c = pd.read_excel(R / "n10/n10_completo_2026-05-17_16h56.xlsx")
m = qn.merge(c[["#Prueba","Geo_k2_perdida"]], on="#Prueba")
eq = (abs(m["QN_k2_perdida"]-m["Geo_k2_perdida"])<=1e-6).sum()
qn_better = (m["QN_k2_perdida"] < m["Geo_k2_perdida"]-1e-6).sum()
geo_better = (m["QN_k2_perdida"] > m["Geo_k2_perdida"]+1e-6).sum()
print(f"n10: igual={eq} QN mejor={qn_better} Geo mejor={geo_better} (de {len(m)})")
# caso 50 en casos_n10
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"GeoMIP/src"))
from benchmark import casos_n10
_,_,pares = casos_n10()
print(f"caso 50 purview/mec: {pares[49]}")
