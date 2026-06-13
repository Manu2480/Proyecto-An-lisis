"""
Genera tablas comparativas: benchmark exacto vs rapido (y opcional aprox).

Salida en GeoMIP/data/results/comparativa/:
  - n{n}_comparativa.xlsx   formato ancho (graficos en Excel)
  - comparativa_long.csv    formato largo (matplotlib/seaborn)
  - comparativa_resumen.xlsx medias por n, k, estrategia

Uso:
  cd GeoMIP/src/Method2_Dynamic_Programming_Reformulation
  uv run python ../gen_comparativa.py
  uv run python ../gen_comparativa.py --n 10 15 20
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

BENCHMARK_ROOT = Path(__file__).resolve().parent
from geomip_paths import RESULTS_DIR  # noqa: E402

COMPARATIVA_DIR = RESULTS_DIR / "comparativa"
COMPARATIVA_DIR.mkdir(parents=True, exist_ok=True)

KS = [2, 3, 4, 5]
KEYS = ["#Prueba", "Purview", "Mecanismo"]


def _latest(folder: Path, pattern: str) -> Path | None:
    if not folder.exists():
        return None
    files = sorted(folder.glob(pattern), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def _load_exacto(n: int) -> pd.DataFrame | None:
    p = _latest(RESULTS_DIR / f"n{n}", "n*_completo_*.xlsx")
    if p is None:
        p = _latest(RESULTS_DIR / f"n{n}", "*.xlsx")
    return pd.read_excel(p) if p else None


def _load_rapido(n: int) -> pd.DataFrame | None:
    p = _latest(RESULTS_DIR / "rapido" / f"n{n}", "n*_rapido_*.xlsx")
    return pd.read_excel(p) if p else None


def _load_aprox(n: int) -> pd.DataFrame | None:
    p = _latest(RESULTS_DIR / "aprox" / f"n{n}", "n*_aprox_*.xlsx")
    return pd.read_excel(p) if p else None


def _perdida_cols(df: pd.DataFrame, prefix: str) -> dict[int, str]:
    out = {}
    for k in KS:
        for col in df.columns:
            if re.fullmatch(rf"{re.escape(prefix)}_k{k}_perdida", str(col)):
                out[k] = col
                break
    return out


def build_wide(n: int, exacto: pd.DataFrame | None, rapido: pd.DataFrame | None, aprox: pd.DataFrame | None) -> pd.DataFrame:
    base = None
    for df in (exacto, rapido, aprox):
        if df is not None:
            base = df[KEYS].copy()
            break
    if base is None:
        return pd.DataFrame()

    if exacto is not None:
        base = base.merge(exacto, on=KEYS, how="left")
    if rapido is not None:
        rcols = KEYS + [c for c in rapido.columns if c.startswith("MCTS_")]
        base = base.merge(rapido[rcols], on=KEYS, how="left", suffixes=("", "_dup"))
        base = base[[c for c in base.columns if not c.endswith("_dup")]]
    if aprox is not None:
        acols = KEYS + [c for c in aprox.columns if c.startswith("KLmc_") or c.startswith("Geo_")]
        base = base.merge(aprox[acols], on=KEYS, how="left", suffixes=("", "_dup2"))
        base = base[[c for c in base.columns if not c.endswith("_dup2")]]

    base.insert(0, "n", n)

    # Deltas rapido vs exacto (Geo k=2, KL k=3..5)
    if exacto is not None and rapido is not None:
        geo_e = "Geo_k2_perdida"
        geo_r = "MCTS_k2_perdida"
        if geo_e in base.columns and geo_r in base.columns:
            base["delta_k2_rapido_vs_geo"] = base[geo_r] - base[geo_e]

        for k in [3, 4, 5]:
            kl = f"KL_k{k}_perdida"
            mc = f"MCTS_k{k}_perdida"
            if kl in base.columns and mc in base.columns:
                base[f"delta_k{k}_rapido_vs_kl"] = base[mc] - base[kl]

    return base


def build_long(wide_frames: list[pd.DataFrame]) -> pd.DataFrame:
    filas = []
    for df in wide_frames:
        if df.empty:
            continue
        n = int(df["n"].iloc[0])
        for _, row in df.iterrows():
            for modo, prefijos in [
                ("Exacto", {"k2": "Geo_k2", "k3": "QN_k3", "k4": "QN_k4", "k5": "QN_k5"}),
                ("Exacto_KL", {"k3": "KL_k3", "k4": "KL_k4", "k5": "KL_k5"}),
                ("Rapido_MCTS", {f"k{k}": f"MCTS_k{k}" for k in KS}),
                ("Aprox_KLmc", {f"k{k}": f"KLmc_k{k}" for k in [3, 4, 5]}),
            ]:
                for k_label, pref in prefijos.items():
                    pcol = f"{pref}_perdida"
                    tcol = f"{pref}_tiempo_ms"
                    if pcol not in df.columns:
                        continue
                    perd = row.get(pcol)
                    if pd.isna(perd):
                        continue
                    k_num = int(re.search(r"\d+", k_label).group()) if re.search(r"\d+", k_label) else 2
                    filas.append({
                        "n": n,
                        "#Prueba": row["#Prueba"],
                        "Purview": row["Purview"],
                        "Mecanismo": row["Mecanismo"],
                        "modo": modo,
                        "k": k_num,
                        "perdida": perd,
                        "tiempo_ms": row.get(tcol),
                    })
    return pd.DataFrame(filas)


def build_resumen(long_df: pd.DataFrame) -> pd.DataFrame:
    if long_df.empty:
        return pd.DataFrame()
    g = long_df.groupby(["n", "modo", "k"], dropna=False)
    return g.agg(
        casos=("perdida", "count"),
        perdida_media=("perdida", "mean"),
        perdida_min=("perdida", "min"),
        perdida_max=("perdida", "max"),
        tiempo_medio_ms=("tiempo_ms", "mean"),
    ).reset_index()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", nargs="+", type=int, default=[10, 15, 20, 22, 25])
    args = parser.parse_args()

    wide_frames = []
    for n in args.n:
        exacto = _load_exacto(n)
        rapido = _load_rapido(n)
        aprox = _load_aprox(n)
        if exacto is None and rapido is None and aprox is None:
            print(f"[SKIP] n={n}: sin datos")
            continue
        wide = build_wide(n, exacto, rapido, aprox)
        if wide.empty:
            continue
        out_n = COMPARATIVA_DIR / f"n{n}_comparativa.xlsx"
        wide.to_excel(out_n, index=False)
        print(f"  n={n} comparativa: {out_n}")
        wide_frames.append(wide)

    if not wide_frames:
        print("Sin datos para comparar.")
        return

    long_df = build_long(wide_frames)
    long_path = COMPARATIVA_DIR / "comparativa_long.csv"
    long_df.to_csv(long_path, index=False, encoding="utf-8")
    print(f"  formato largo: {long_path}")

    resumen = build_resumen(long_df)
    res_path = COMPARATIVA_DIR / "comparativa_resumen.xlsx"
    with pd.ExcelWriter(res_path, engine="openpyxl") as xw:
        resumen.to_excel(xw, sheet_name="resumen", index=False)
        for n in sorted(long_df["n"].unique()):
            sub = long_df[long_df["n"] == n]
            sub.to_excel(xw, sheet_name=f"long_n{int(n)}", index=False)
    print(f"  resumen: {res_path}")


if __name__ == "__main__":
    main()
