#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

R = Path(__file__).resolve().parents[1] / "GeoMIP/data/results"
for n in (10, 15):
    c = pd.read_excel(R / f"n{n}/n{n}_completo_2026-05-17_16h56.xlsx")
    qn = c["QN_k2_perdida"]
    geo = c["Geo_k2_perdida"]
    both = c[qn.notna() & geo.notna()]
    peor = both[both["QN_k2_perdida"] > both["Geo_k2_perdida"] + 1e-6]
    print(f"n={n} mayo: QN filas={qn.notna().sum()}/50  QN>Geo={len(peor)}/{len(both)}")
    if n == 10:
        print("  caso 50 QN:", c.loc[c["#Prueba"]==50, "QN_k2_perdida"].values)
        print("  caso 50 conv:", c.loc[c["#Prueba"]==50, "QN_k2_particion"].values if "QN_k2_particion" in c.columns else "N/A")

# n20: QN vs Geo summary
c20 = pd.read_excel(R / "n20/n20_completo_2026-05-18_04h38.xlsx")
qn20 = pd.read_excel(R / "n20/qnodes_k2_n20_2026-06-13_20h19.xlsx")
c20 = pd.read_excel(R / "n20/n20_completo_2026-05-18_04h38.xlsx")
m = qn20.merge(c20[["#Prueba", "Geo_k2_perdida"]], on="#Prueba")
qn = m["QN_k2_perdida"]
geo = m["Geo_k2_perdida"]
eq = (abs(qn - geo) <= 1e-6).sum()
better = (qn < geo - 1e-6).sum()
worse = (qn > geo + 1e-6).sum()
print(f"\nn=20: QN==Geo {eq}/50  QN<Geo {better}  QN>Geo {worse}")
print("  perdida min/max QN:", qn.min(), qn.max())
