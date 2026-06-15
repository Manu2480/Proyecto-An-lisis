#!/usr/bin/env python3
"""Auditoría rápida de coherencia datos vs gráficas proyecto."""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "GeoMIP" / "data" / "results"
cl = pd.read_csv(R / "comparativa" / "comparativa_long.csv")
cl = cl[cl["n"].isin([10, 15, 20])]

print("=== comparativa_long n=10,15,20 ===")
print(cl.groupby(["n", "modo"]).size().unstack(fill_value=0))

for n in [10, 15, 20]:
    qn = sorted((R / f"n{n}").glob(f"qnodes_k2_n{n}_*.xlsx"))[-1]
    qdf = pd.read_excel(qn)
    geo = cl[(cl.n == n) & (cl.modo == "Exacto") & (cl.k == 2)]
    mcts = cl[(cl.n == n) & (cl.modo == "Rapido_MCTS") & (cl.k == 2)]
    m = geo.merge(
        qdf[["#Prueba", "QN_k2_perdida"]],
        on="#Prueba", how="inner",
    )
    tol = 1e-6
    d = m["perdida"] - m["QN_k2_perdida"]
    print(f"\n--- n={n} QNodes vs Geo k=2 ---")
    print(f"  qnodes filas: {len(qdf)}, geo filas: {len(geo)}, merge: {len(m)}")
    print(f"  iguales: {(d.abs() <= tol).sum()}")
    print(f"  geo mejor: {(d < -tol).sum()}")
    print(f"  qn mejor:  {(d > tol).sum()}")
    if (d.abs() > tol).any():
        worst = m.loc[d.abs().idxmax()]
        print(f"  max diff caso #{int(worst['#Prueba'])}: Geo={worst['perdida']}, QN={worst['QN_k2_perdida']}")

    print(f"  Geo k2 perdida media: {geo['perdida'].mean():.4f}, max: {geo['perdida'].max():.4f}")
    print(f"  MCTS k2 perdida media: {mcts['perdida'].mean():.4f}, max: {mcts['perdida'].max():.4f}")
    print(f"  QN k2 perdida media: {qdf['QN_k2_perdida'].mean():.4f}, max: {qdf['QN_k2_perdida'].max():.4f}")

    # tiempo g1 sanity
    ex = cl[(cl.n == n) & (cl.modo == "Exacto")]
    for k in [2, 3, 4, 5]:
        sk = ex[ex.k == k]
        if len(sk):
            print(f"  tiempo medio Exacto k={k}: {sk['tiempo_ms'].mean():.0f} ms (max {sk['tiempo_ms'].max():.0f})")

print("\n=== g2 eje X: agrupa por tamano |Purview|, no por subsistema unico ===")
for n in [10, 15, 20]:
    geo = cl[(cl.n == n) & (cl.modo == "Exacto") & (cl.k == 2)].copy()
    geo["tam"] = geo["Purview"].str.len()
    print(f"n={n}: tamanos unicos {sorted(geo['tam'].unique())}, casos por tamano:")
    print(geo.groupby("tam").size().to_dict())
