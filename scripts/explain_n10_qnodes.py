#!/usr/bin/env python3
"""Detalle n10: QN vs Geo caso a caso."""
from pathlib import Path
import pandas as pd

R = Path(__file__).resolve().parents[1] / "GeoMIP/data/results"
qn = pd.read_excel(R / "n10/qnodes_k2_n10_2026-06-13_10h24.xlsx")
c = pd.read_excel(R / "n10/n10_completo_2026-05-17_16h56.xlsx")
m = qn.merge(c, on=["#Prueba", "Purview", "Mecanismo"], suffixes=("_qn", "_may"))
m["diff"] = m["QN_k2_perdida_qn"] - m["Geo_k2_perdida"]
print("n10 casos:", len(qn))
print("\n--- Geo mejor que QN (diff > 1e-6) ---")
geo_better = m[m["diff"] > 1e-6].sort_values("diff", ascending=False)
for _, r in geo_better.iterrows():
    print(
        f"  #{int(r['#Prueba']):2d}  QN={r['QN_k2_perdida_qn']:.8f}  "
        f"Geo={r['Geo_k2_perdida']:.8f}  diff={r['diff']:.8f}  "
        f"{r['Purview'][:10]}/{r['Mecanismo'][:10]}"
    )
print(f"\nTotal Geo mejor: {len(geo_better)}")
print("\n--- Iguales (29) ---")
eq = m[abs(m["diff"]) <= 1e-6]
print(f"  perdida media QN={eq['QN_k2_perdida_qn'].mean():.6f}  Geo={eq['Geo_k2_perdida'].mean():.6f}")
