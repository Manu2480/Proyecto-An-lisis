#!/usr/bin/env python3
"""Auditoría rápida de coherencia datos vs gráficas proyecto."""
from pathlib import Path
import re
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "GeoMIP" / "data" / "results"
COMP = R / "comparativa"
KS = [2, 3, 4, 5]


def _latest(folder: Path, pattern: str) -> Path | None:
    files = sorted(folder.glob(pattern), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def wide_a_largo(wide: pd.DataFrame) -> pd.DataFrame:
    incluir_exacto = "KL_k3_perdida" in wide.columns
    modos = [
        ("QNodes", {"k2": "QN_k2"}),
        ("Rapido_MCTS", {f"k{k}": f"MCTS_k{k}" for k in KS}),
        ("Aprox_Geo", {"k2": "Geo_k2"}),
        ("Aprox_KLmc", {f"k{k}": f"KLmc_k{k}" for k in [3, 4, 5]}),
    ]
    if incluir_exacto:
        modos = [
            ("Exacto", {"k2": "Geo_k2", "k3": "QN_k3", "k4": "QN_k4", "k5": "QN_k5"}),
            ("Exacto_KL", {"k3": "KL_k3", "k4": "KL_k4", "k5": "KL_k5"}),
        ] + modos
    filas = []
    n = int(wide["n"].iloc[0])
    for _, row in wide.iterrows():
        for modo, prefijos in modos:
            for k_label, pref in prefijos.items():
                pcol = f"{pref}_perdida"
                tcol = f"{pref}_tiempo_ms"
                if pcol not in wide.columns:
                    continue
                perd = row.get(pcol)
                if pd.isna(perd):
                    continue
                k_num = int(re.search(r"\d+", k_label).group()) if re.search(r"\d+", k_label) else 2
                filas.append({
                    "n": n, "#Prueba": row["#Prueba"], "Purview": row["Purview"],
                    "modo": modo, "k": k_num, "perdida": perd, "tiempo_ms": row.get(tcol),
                })
    return pd.DataFrame(filas)


partes = []
for n in [10, 15, 20, 22, 25]:
    p = _latest(COMP, f"n{n}_comparativa.xlsx")
    if p is None:
        print(f"[WARN] sin n{n}_comparativa.xlsx")
        continue
    print(f"n={n}: {p.name}")
    partes.append(wide_a_largo(pd.read_excel(p)))

cl = pd.concat(partes, ignore_index=True)

print("\n=== comparativa n{n} (desde Excel ancho) ===")
print(cl.groupby(["n", "modo"]).size().unstack(fill_value=0))

for n in [10, 15, 20, 22, 25]:
    qn = cl[(cl.n == n) & (cl.modo == "QNodes") & (cl.k == 2)]
    geo_ex = cl[(cl.n == n) & (cl.modo == "Exacto") & (cl.k == 2)]
    geo_ap = cl[(cl.n == n) & (cl.modo == "Aprox_Geo") & (cl.k == 2)]
    geo = geo_ex if not geo_ex.empty else geo_ap
    mcts = cl[(cl.n == n) & (cl.modo == "Rapido_MCTS") & (cl.k == 2)]
    m = geo.merge(qn[["#Prueba", "perdida"]].rename(columns={"perdida": "QN_k2_perdida"}), on="#Prueba", how="inner")
    tol = 1e-6
    d = m["perdida"] - m["QN_k2_perdida"]
    print(f"\n--- n={n} QNodes vs Geo k=2 ---")
    print(f"  qn filas: {len(qn)}, geo filas: {len(geo)}, merge: {len(m)}")
    print(f"  iguales: {(d.abs() <= tol).sum()}")
    print(f"  geo mejor: {(d < -tol).sum()}")
    print(f"  qn mejor:  {(d > tol).sum()}")
    if len(geo):
        print(f"  Geo k2 perdida media: {geo['perdida'].mean():.4f}, max: {geo['perdida'].max():.4f}")
    if len(mcts):
        print(f"  MCTS k2 perdida media: {mcts['perdida'].mean():.4f}, max: {mcts['perdida'].max():.4f}")
    if len(qn):
        print(f"  QN k2 perdida media: {qn['perdida'].mean():.4f}, max: {qn['perdida'].max():.4f}")

print("\n=== resumen para figuras (k=2 y escalado k) ===")
for n in [10, 15, 20, 22, 25]:
    sub = cl[cl.n == n]
    if sub.empty:
        continue
    qn = sub[(sub.modo == "QNodes") & (sub.k == 2)]
    mcts = sub[sub.modo == "Rapido_MCTS"]
    klmc = sub[sub.modo == "Aprox_KLmc"]
    print(f"n={n}: QNodes k=2={len(qn)}, MCTS filas={len(mcts)}, KL+MC filas={len(klmc)}")
    if len(mcts):
        print(f"  MCTS perdida media por k: {mcts.groupby('k')['perdida'].mean().round(4).to_dict()}")
    if len(klmc):
        print(f"  KL+MC perdida media por k: {klmc.groupby('k')['perdida'].mean().round(4).to_dict()}")
