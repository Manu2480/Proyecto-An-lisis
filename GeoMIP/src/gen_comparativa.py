"""
Genera tablas comparativas entre resultados del proyecto.

Fuentes (ultimo archivo por fecha de modificacion):
  - QNodes k=2:  results/n{n}/qnodes_k2_n{n}_*.xlsx     (run_qnodes_k2.py)
  - Rapido:      results/rapido/n{n}/n*_rapido_*.xlsx  (benchmark_rapido.py, MCTS)
  - Aprox:       results/aprox/n{n}/n*_aprox_*.xlsx    (benchmark_aprox.py, KL+MC)
  - Exacto:      results/n{n}/n*_completo_*.xlsx       (benchmark.py, opcional)

Salida en GeoMIP/data/results/comparativa/:
  - n{n}_comparativa.xlsx    formato ancho
  - comparativa_long.csv     formato largo (graficas)
  - comparativa_resumen.xlsx medias por n, modo, k

Uso:
  cd GeoMIP/src/Method2_Dynamic_Programming_Reformulation
  uv run python ../gen_comparativa.py --n 15
  uv run python ../gen_comparativa.py --n 15 --sin-aprox
  uv run python ../gen_comparativa.py --n 10 15 20 --con-exacto
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

from geomip_paths import RESULTS_DIR  # noqa: E402

COMPARATIVA_DIR = RESULTS_DIR / "comparativa"
COMPARATIVA_DIR.mkdir(parents=True, exist_ok=True)

KS = [2, 3, 4, 5]
KEYS = ["#Prueba", "Purview", "Mecanismo"]

QN_COLS = [
    "QN_k2_particion",
    "QN_k2_perdida",
    "QN_k2_tiempo_ms",
    "QN_k2_convergio",
    "QN_k2_error",
]


def _latest(folder: Path, pattern: str) -> Path | None:
    if not folder.exists():
        return None
    files = sorted(folder.glob(pattern), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def _load_qnodes(n: int) -> tuple[pd.DataFrame | None, Path | None]:
    """Salida canonica de run_qnodes_k2.py (k=2 exacto)."""
    folder = RESULTS_DIR / f"n{n}"
    p = _latest(folder, f"qnodes_k2_n{n}_*.xlsx")
    if p is None:
        p = _latest(folder, "qnodes_k2_checkpoint_*.xlsx")
    if p is None:
        return None, None
    df = pd.read_excel(p)
    keep = KEYS + [c for c in QN_COLS if c in df.columns]
    return df[keep].copy(), p


def _load_rapido(n: int) -> tuple[pd.DataFrame | None, Path | None]:
    p = _latest(RESULTS_DIR / "rapido" / f"n{n}", "n*_rapido_*.xlsx")
    if p is None:
        return None, None
    return pd.read_excel(p), p


def _load_aprox(n: int) -> tuple[pd.DataFrame | None, Path | None]:
    p = _latest(RESULTS_DIR / "aprox" / f"n{n}", "n*_aprox_*.xlsx")
    if p is None:
        return None, None
    return pd.read_excel(p), p


def _load_exacto(n: int) -> tuple[pd.DataFrame | None, Path | None]:
    """Benchmark completo (benchmark.py); solo si --con-exacto."""
    folder = RESULTS_DIR / f"n{n}"
    p = _latest(folder, "n*_completo_*.xlsx")
    if p is None:
        return None, None
    return pd.read_excel(p), p


def _merge_source(
    base: pd.DataFrame,
    df: pd.DataFrame,
    cols: list[str],
    suffix: str,
) -> pd.DataFrame:
    present = [c for c in cols if c in df.columns]
    if not present:
        return base
    merged = base.merge(df[present], on=KEYS, how="left", suffixes=("", suffix))
    return merged[[c for c in merged.columns if not c.endswith(suffix)]]


def _add_deltas(base: pd.DataFrame) -> pd.DataFrame:
    """Deltas de perdida: positivo = la columna derecha es peor (mayor phi)."""

    def _diff(left: str, right: str, out: str) -> None:
        if left in base.columns and right in base.columns:
            base[out] = base[right] - base[left]

    # QNodes (referencia exacta k=2) vs heuristicas
    _diff("QN_k2_perdida", "MCTS_k2_perdida", "delta_k2_rapido_vs_qnodes")
    _diff("QN_k2_perdida", "Geo_k2_perdida", "delta_k2_geo_vs_qnodes")

    for k in [3, 4, 5]:
        _diff(f"KLmc_k{k}_perdida", f"MCTS_k{k}_perdida", f"delta_k{k}_rapido_vs_klmc")
        _diff(f"KL_k{k}_perdida", f"MCTS_k{k}_perdida", f"delta_k{k}_rapido_vs_kl_exacto")
        _diff(f"KL_k{k}_perdida", f"KLmc_k{k}_perdida", f"delta_k{k}_klmc_vs_kl_exacto")

    # Legacy: rapido vs benchmark exacto (Geo + KL del completo)
    _diff("Geo_k2_perdida", "MCTS_k2_perdida", "delta_k2_rapido_vs_geo_completo")

    return base


def build_wide(
    n: int,
    qnodes: pd.DataFrame | None,
    rapido: pd.DataFrame | None,
    aprox: pd.DataFrame | None,
    exacto: pd.DataFrame | None,
) -> pd.DataFrame:
    base = None
    for df in (qnodes, rapido, aprox, exacto):
        if df is not None:
            base = df[KEYS].drop_duplicates().copy()
            break
    if base is None:
        return pd.DataFrame()

    if qnodes is not None:
        base = _merge_source(base, qnodes, KEYS + QN_COLS, "_qn")

    if rapido is not None:
        rcols = KEYS + [c for c in rapido.columns if c.startswith("MCTS_")]
        base = _merge_source(base, rapido, rcols, "_rap")

    if aprox is not None:
        acols = KEYS + [
            c for c in aprox.columns
            if c.startswith("KLmc_") or c.startswith("Geo_")
        ]
        base = _merge_source(base, aprox, acols, "_apx")

    if exacto is not None:
        # No pisar QN_k2 del archivo dedicado si ya viene de qnodes
        excols = KEYS + [c for c in exacto.columns if c not in KEYS]
        if qnodes is not None:
            excols = [c for c in excols if not c.startswith("QN_k2_")]
        base = _merge_source(base, exacto, excols, "_exc")

    base.insert(0, "n", n)
    return _add_deltas(base)


def build_long(wide_frames: list[pd.DataFrame], incluir_exacto: bool) -> pd.DataFrame:
    modos: list[tuple[str, dict[str, str]]] = [
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
    for df in wide_frames:
        if df.empty:
            continue
        n = int(df["n"].iloc[0])
        for _, row in df.iterrows():
            for modo, prefijos in modos:
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


def _print_fuente(etiqueta: str, path: Path | None) -> None:
    if path is None:
        print(f"    {etiqueta}: (no encontrado)")
    else:
        print(f"    {etiqueta}: {path.name}")


def main():
    parser = argparse.ArgumentParser(
        description="Comparativa QNodes (run_qnodes_k2) vs rapido y/o aprox"
    )
    parser.add_argument("--n", nargs="+", type=int, default=[10, 15, 20, 22, 25])
    parser.add_argument(
        "--sin-rapido",
        action="store_true",
        help="No incluir benchmark_rapido.py (MCTS)",
    )
    parser.add_argument(
        "--sin-aprox",
        action="store_true",
        help="No incluir benchmark_aprox.py (Geo k=2 + KLmc)",
    )
    parser.add_argument(
        "--sin-qnodes",
        action="store_true",
        help="No incluir run_qnodes_k2.py (QN_k2)",
    )
    parser.add_argument(
        "--con-exacto",
        action="store_true",
        help="Incluir ademas n*_completo_*.xlsx de benchmark.py (Geo/Greedy/KL)",
    )
    args = parser.parse_args()

    wide_frames = []
    for n in args.n:
        qnodes, pq = (None, None) if args.sin_qnodes else _load_qnodes(n)
        rapido, pr = (None, None) if args.sin_rapido else _load_rapido(n)
        aprox, pa = (None, None) if args.sin_aprox else _load_aprox(n)
        exacto, pe = _load_exacto(n) if args.con_exacto else (None, None)

        if qnodes is None and rapido is None and aprox is None and exacto is None:
            print(f"[SKIP] n={n}: sin datos")
            continue

        print(f"  n={n}:")
        _print_fuente("QNodes", pq)
        _print_fuente("Rapido", pr)
        _print_fuente("Aprox", pa)
        if args.con_exacto:
            _print_fuente("Exacto", pe)

        wide = build_wide(n, qnodes, rapido, aprox, exacto)
        if wide.empty:
            continue
        out_n = COMPARATIVA_DIR / f"n{n}_comparativa.xlsx"
        wide.to_excel(out_n, index=False)
        print(f"    -> {out_n.name} ({len(wide)} filas)")
        wide_frames.append(wide)

    if not wide_frames:
        print("Sin datos para comparar.")
        return

    long_df = build_long(wide_frames, incluir_exacto=args.con_exacto)
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
