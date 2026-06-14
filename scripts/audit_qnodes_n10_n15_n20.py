#!/usr/bin/env python3
"""Valida resultados QNodes k=2 vs benchmark completo (referencia)."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "GeoMIP/data/results"

QN_COLS = ["QN_k2_particion", "QN_k2_perdida", "QN_k2_tiempo_ms", "QN_k2_convergio", "QN_k2_error"]

CANONICAL = {
    10: RESULTS / "n10/qnodes_k2_n10_2026-06-13_10h24.xlsx",
    15: RESULTS / "n15/qnodes_k2_n15_2026-06-13_10h57.xlsx",
    20: RESULTS / "n20/qnodes_k2_n20_2026-06-13_20h19.xlsx",
}

COMPLETO = {
    10: RESULTS / "n10/n10_completo_2026-05-17_16h56.xlsx",
    15: RESULTS / "n15/n15_completo_2026-05-17_16h56.xlsx",
    20: RESULTS / "n20/n20_completo_2026-05-18_04h38.xlsx",
}

PARCHE = {
    10: RESULTS / "n10/n10_completo_2026-05-17_16h56_qn_k2.xlsx",
    15: RESULTS / "n15/n15_completo_2026-05-17_16h56_qn_k2.xlsx",
    20: RESULTS / "n20/n20_completo_2026-05-18_04h38_qn_k2.xlsx",
}

TOL = 1e-6


def _latest(folder: Path, pattern: str) -> Path | None:
    files = sorted(folder.glob(pattern), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def load_qn(n: int) -> pd.DataFrame:
    p = CANONICAL[n]
    if not p.exists():
        p = _latest(RESULTS / f"n{n}", "qnodes_k2_n*.xlsx")
    if p is None or not p.exists():
        raise FileNotFoundError(f"sin qnodes n={n}")
    return pd.read_excel(p)


def compare_perdida(a: float, b: float) -> bool:
    if pd.isna(a) and pd.isna(b):
        return True
    if pd.isna(a) or pd.isna(b):
        return False
    return math.isclose(float(a), float(b), rel_tol=0, abs_tol=TOL)


def audit_n(n: int) -> dict:
    qn = load_qn(n)
    out = {"n": n, "archivo": str(CANONICAL[n]), "issues": [], "ok": True}

    # 1) Completitud
    filas = len(qn)
    conv = int(qn["QN_k2_convergio"].fillna(False).astype(bool).sum())
    out["filas"] = filas
    out["convergieron"] = conv
    if filas < 50:
        out["issues"].append(f"solo {filas}/50 filas")
        out["ok"] = False
    fails = qn[~qn["QN_k2_convergio"].fillna(False).astype(bool)]
    if len(fails):
        out["issues"].append(f"{len(fails)} casos sin converger: #{list(fails['#Prueba'])}")
        out["ok"] = False

    # 2) n10/n15: vs benchmark mayo (misma corrida benchmark.py con QNodes)
    completo = COMPLETO[n]
    if completo.exists() and "QN_k2_perdida" in pd.read_excel(completo, nrows=0).columns:
        ref = pd.read_excel(completo)
        merged = qn.merge(ref, on="#Prueba", suffixes=("_qn", "_ref"), how="outer")
        diffs = []
        for _, row in merged.iterrows():
            if not compare_perdida(row.get("QN_k2_perdida_qn"), row.get("QN_k2_perdida_ref")):
                diffs.append(int(row["#Prueba"]))
        out["vs_completo_mayo"] = len(diffs)
        if diffs:
            out["issues"].append(f"perdida distinta vs completo mayo en casos {diffs[:10]}{'...' if len(diffs)>10 else ''}")
            out["ok"] = False
    else:
        out["vs_completo_mayo"] = None

    # 3) Todos: QN_k2 <= Geo_k2 (óptimo bipartición no peor que Geometric)
    if completo.exists():
        ref = pd.read_excel(completo)
        if "Geo_k2_perdida" in ref.columns:
            merged = qn.merge(ref[["#Prueba", "Geo_k2_perdida"]], on="#Prueba", how="inner")
            peor = merged[
                merged["QN_k2_perdida"].notna()
                & merged["Geo_k2_perdida"].notna()
                & (merged["QN_k2_perdida"] > merged["Geo_k2_perdida"] + TOL)
            ]
            out["vs_geo_peor"] = len(peor)
            if len(peor):
                casos = list(peor["#Prueba"].astype(int))
                out["issues"].append(
                    f"QN perdida > Geo_k2 en {len(peor)} casos: {casos[:8]}{'...' if len(casos)>8 else ''}"
                )
                out["ok"] = False
            # casos donde QN mucho mejor (informativo)
            mejor = merged[
                merged["QN_k2_perdida"].notna()
                & merged["Geo_k2_perdida"].notna()
                & (merged["Geo_k2_perdida"] - merged["QN_k2_perdida"] > 0.01)
            ]
            out["qn_mejor_que_geo"] = len(mejor)

    # 4) Parche qn_k2 coherente con standalone
    parche = PARCHE[n]
    if parche.exists():
        p = pd.read_excel(parche)
        merged = qn.merge(p, on="#Prueba", suffixes=("_qn", "_parche"))
        diffs = []
        for _, row in merged.iterrows():
            if not compare_perdida(row.get("QN_k2_perdida_qn"), row.get("QN_k2_perdida_parche")):
                diffs.append(int(row["#Prueba"]))
        out["parche_diff"] = len(diffs)
        if diffs:
            out["issues"].append(f"parche qn_k2 difiere en casos {diffs}")
            out["ok"] = False
    else:
        out["parche_diff"] = None

    # 5) Pérdidas válidas (no negativas, no NaN en convergidos)
    bad_loss = qn[
        qn["QN_k2_convergio"].fillna(False).astype(bool)
        & (qn["QN_k2_perdida"].isna() | (qn["QN_k2_perdida"] < -TOL))
    ]
    if len(bad_loss):
        out["issues"].append(f"perdida invalida en #{list(bad_loss['#Prueba'])}")
        out["ok"] = False

    return out


def main():
    print("=== AUDITORIA QNodes k=2 (n10, n15, n20) ===\n")
    all_ok = True
    for n in (10, 15, 20):
        try:
            r = audit_n(n)
        except FileNotFoundError as e:
            print(f"n={n}: ERROR {e}")
            all_ok = False
            continue
        status = "APROBADO" if r["ok"] else "FALLA"
        print(f"n={n}  {status}")
        print(f"  archivo: {Path(r['archivo']).name}")
        print(f"  filas: {r['filas']}  convergieron: {r['convergieron']}/50")
        if r.get("vs_completo_mayo") is not None:
            print(f"  dif vs completo mayo (QN_k2): {r['vs_completo_mayo']}")
        if "vs_geo_peor" in r:
            print(f"  QN > Geo_k2: {r['vs_geo_peor']}  (QN mejor que Geo: {r.get('qn_mejor_que_geo', 0)})")
        if r.get("parche_diff") is not None:
            print(f"  dif vs parche qn_k2: {r['parche_diff']}")
        if r["issues"]:
            for issue in r["issues"]:
                print(f"  ! {issue}")
        print()
        all_ok = all_ok and r["ok"]

    print("RESULTADO GLOBAL:", "APROBADO" if all_ok else "REVISAR")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
