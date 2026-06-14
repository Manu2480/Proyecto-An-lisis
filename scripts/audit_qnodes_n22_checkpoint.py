#!/usr/bin/env python3
"""Revisa checkpoint QNodes n=22 (15 casos guardados)."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "GeoMIP/data/results"
N22 = RESULTS / "n22"

sys.path.insert(0, str(ROOT / "GeoMIP/src"))
from benchmark import casos_n22  # noqa: E402

TOL = 1e-6


def main():
    ck = sorted(N22.glob("qnodes_k2_checkpoint_*.xlsx"), key=lambda p: p.stat().st_mtime)[-1]
    df = pd.read_excel(ck)
    _, _, pares = casos_n22()

    print("=== QNodes n=22 — checkpoint ===")
    print(f"archivo: {ck.name}")
    print(f"filas: {len(df)}")
    print()

    issues = []

    # 1) #Prueba consecutivos 1..15
    pruebas = sorted(int(x) for x in df["#Prueba"])
    esperado = list(range(1, len(df) + 1))
    if pruebas != esperado:
        issues.append(f"#Prueba no consecutivos: {pruebas}")

    # 2) Purview/Mecanismo vs enunciado
    bad_pares = []
    for _, row in df.iterrows():
        idx = int(row["#Prueba"]) - 1
        exp_p, exp_m = pares[idx]
        got_p = str(row["Purview"]).strip()
        got_m = str(row["Mecanismo"]).strip()
        if got_p != exp_p or got_m != exp_m:
            bad_pares.append(int(row["#Prueba"]))
    if bad_pares:
        issues.append(f"purview/mecanismo distinto al enunciado en casos {bad_pares}")

    # 3) Convergencia y pérdidas
    conv = int(df["QN_k2_convergio"].fillna(False).astype(bool).sum())
    fails = df[~df["QN_k2_convergio"].fillna(False).astype(bool)]
    if len(fails):
        issues.append(f"sin converger: #{list(fails['#Prueba'])}")

    nan_loss = df[df["QN_k2_convergio"].fillna(False).astype(bool) & df["QN_k2_perdida"].isna()]
    if len(nan_loss):
        issues.append(f"perdida NaN en convergidos: #{list(nan_loss['#Prueba'])}")

    neg = df[df["QN_k2_perdida"].notna() & (df["QN_k2_perdida"] < -TOL)]
    if len(neg):
        issues.append(f"perdida negativa: #{list(neg['#Prueba'])}")

    # 4) vs Geo_k2 del benchmark completo mayo
    comp_path = N22 / "n22_completo_2026-05-20_02h29.xlsx"
    geo_cmp = None
    if comp_path.exists():
        comp = pd.read_excel(comp_path)
        if "Geo_k2_perdida" in comp.columns:
            m = df.merge(comp[["#Prueba", "Geo_k2_perdida"]], on="#Prueba", how="left")
            eq = (abs(m["QN_k2_perdida"] - m["Geo_k2_perdida"]) <= TOL).sum()
            qn_worse = (m["QN_k2_perdida"] > m["Geo_k2_perdida"] + TOL).sum()
            qn_better = (m["QN_k2_perdida"] < m["Geo_k2_perdida"] - TOL).sum()
            geo_cmp = (eq, qn_worse, qn_better)

    # Tabla resumen
    print("Caso | Purview (res) | Mecanismo (res) | perdida QN | tiempo_ms | conv")
    print("-" * 85)
    for _, row in df.iterrows():
        p = str(row["Purview"])
        m = str(row["Mecanismo"])
        loss = row["QN_k2_perdida"]
        t = row.get("QN_k2_tiempo_ms", "")
        c = "OK" if row.get("QN_k2_convergio") else "FAIL"
        loss_s = f"{loss:.6g}" if pd.notna(loss) else "NaN"
        t_s = f"{int(t):,}" if pd.notna(t) else "-"
        print(
            f" {int(row['#Prueba']):2d}  | {p[:18]:<18} | {m[:18]:<18} | "
            f"{loss_s:>10} | {t_s:>12} | {c}"
        )

    print()
    print("--- Estadísticas ---")
    print(f"  convergieron: {conv}/{len(df)}")
    if df["QN_k2_perdida"].notna().any():
        print(f"  perdida min/max/media: {df['QN_k2_perdida'].min():.6g} / "
              f"{df['QN_k2_perdida'].max():.6g} / {df['QN_k2_perdida'].mean():.6g}")
    if "QN_k2_tiempo_ms" in df.columns and df["QN_k2_tiempo_ms"].notna().any():
        t = df["QN_k2_tiempo_ms"]
        print(f"  tiempo_ms min/max/media: {int(t.min()):,} / {int(t.max()):,} / {int(t.mean()):,}")
        print(f"  tiempo total acumulado: {int(t.sum()):,} ms (~{t.sum()/3_600_000:.1f} h)")

    if geo_cmp:
        eq, worse, better = geo_cmp
        print(f"  vs Geo_k2 (mayo): iguales={eq}  QN>Geo={worse}  QN<Geo={better}")

    # Casos pesados (perdida 0 = trivial?)
    zeros = df[df["QN_k2_perdida"].fillna(-1) == 0]
    print(f"  casos con perdida=0: {len(zeros)} (#{list(zeros['#Prueba'].astype(int))})")

    print()
    if issues:
        print("PROBLEMAS:")
        for i in issues:
            print(f"  ! {i}")
        print("\nRESULTADO: REVISAR")
        sys.exit(1)
    print("RESULTADO: 15 casos OK (datos coherentes con enunciado)")
    print(f"Siguiente caso al reanudar: --desde {len(df)+1} --merge")


if __name__ == "__main__":
    main()
