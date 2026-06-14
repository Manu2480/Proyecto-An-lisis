#!/usr/bin/env python3
"""Detalle auditoría QNodes."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "GeoMIP/data/results"

for n in (10, 15, 20):
    qn = pd.read_excel(R / f"n{n}/qnodes_k2_n{n}_2026-06-13_{'10h24' if n==10 else '10h57' if n==15 else '20h19'}.xlsx")
    comp = pd.read_excel(R / f"n{n}/n{n}_completo_{'2026-05-17_16h56' if n<20 else '2026-05-18_04h38'}.xlsx")
    m = qn.merge(comp, on="#Prueba", suffixes=("_jun", "_may"))
    print(f"\n=== n={n} ===")
    print(f"QN jun: {len(qn)} filas, conv={qn['QN_k2_convergio'].sum()}")
    if "QN_k2_perdida" in comp.columns:
        may_ok = comp["QN_k2_perdida"].notna().sum()
        print(f"QN may completo: {may_ok} con perdida")
    if n == 10:
        missing = set(range(1, 51)) - set(qn["#Prueba"])
        print(f"Casos faltantes en jun: {sorted(missing)}")
    if "Geo_k2_perdida" in comp.columns:
        bad = m[(m["QN_k2_perdida_jun"] > m["Geo_k2_perdida"] + 1e-6) & m["Geo_k2_perdida"].notna()]
        print(f"QN_jun > Geo_k2: {len(bad)} casos")
        if len(bad) and len(bad) <= 5:
            for _, r in bad.iterrows():
                print(f"  #{int(r['#Prueba'])} QN={r['QN_k2_perdida_jun']} Geo={r['Geo_k2_perdida']}")
        elif len(bad):
            print(f"  ej #{int(bad.iloc[0]['#Prueba'])} QN={bad.iloc[0]['QN_k2_perdida_jun']} Geo={bad.iloc[0]['Geo_k2_perdida']}")
    if "QN_k2_perdida" in comp.columns:
        both = m[m["QN_k2_perdida_may"].notna() & m["QN_k2_perdida_jun"].notna()]
        diff = both[abs(both["QN_k2_perdida_jun"] - both["QN_k2_perdida_may"]) > 1e-6]
        print(f"QN jun vs may: {len(diff)} difieren de {len(both)} comparables")
        if len(diff):
            r = diff.iloc[0]
            print(f"  ej #{int(r['#Prueba'])} jun={r['QN_k2_perdida_jun']} may={r['QN_k2_perdida_may']}")
