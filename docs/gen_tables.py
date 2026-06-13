"""
docs/gen_tables.py
==================
Genera tablas LaTeX a partir del archivo benchmark_*.xlsx más reciente
(o el especificado) y las guarda en docs/tables/.

Tablas generadas:
  - benchmark_n<N>.tex   — resultados para cada n (GeometricSIA vs QNodes vs KPart)
  - benchmark_summary.tex — resumen global media/min/max/std por n/k/estrategia

Uso:
  python gen_tables.py
  python gen_tables.py --input GeoMIP/data/results/benchmark_2026-05-16_18h00.xlsx
  python gen_tables.py --out docs/tables/
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────
DOCS_ROOT    = Path(__file__).resolve().parent
RESULTS_DIR  = DOCS_ROOT.parent / "GeoMIP" / "data" / "results"
TABLES_DIR   = DOCS_ROOT / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)


def find_latest_benchmark() -> Path | None:
    """Devuelve el benchmark_*.xlsx más reciente en RESULTS_DIR."""
    candidates = sorted(RESULTS_DIR.glob("benchmark_[0-9]*.xlsx"))
    return candidates[-1] if candidates else None


# ── Formateo LaTeX ────────────────────────────────────────────────────────────
def fmt_float(v, digits=4):
    if pd.isna(v):
        return "---"
    return f"{v:.{digits}f}"


def fmt_time(v):
    if pd.isna(v):
        return "---"
    if v < 1000:
        return f"{v:.1f}\\,ms"
    return f"{v/1000:.1f}\\,s"


def df_to_latex_table(df: pd.DataFrame, caption: str, label: str,
                      float_cols=("perdida_emd", "memoria_mb"),
                      time_cols=("tiempo_ms",)) -> str:
    """Convierte un DataFrame a una tabla LaTeX booktabs."""
    col_renames = {
        "estrategia":     "Estrategia",
        "k":              "$k$",
        "purview_texto":  "Purview",
        "mecanismo_texto":"Mecanismo",
        "perdida_emd":    r"$\phi$ (EMD)",
        "tiempo_ms":      "Tiempo",
        "memoria_mb":     "Memoria (MB)",
        "convergio":      "Conv.",
    }
    df = df.rename(columns=col_renames)

    # Formatear columnas numéricas
    for col in df.columns:
        orig = {v: k for k, v in col_renames.items()}.get(col, col)
        if orig in float_cols and col in df.columns:
            df[col] = df[col].apply(fmt_float)
        elif orig in time_cols and col in df.columns:
            df[col] = df[col].apply(fmt_time)
        elif col == "Conv.":
            df[col] = df[col].map({True: r"\checkmark", False: r"$\times$",
                                   None: "---", np.nan: "---"}).fillna("---")

    ncols = len(df.columns)
    col_spec = "l" + "r" * (ncols - 1)

    lines = [
        r"\begin{table}[H]",
        r"  \centering",
        rf"  \caption{{{caption}}}",
        rf"  \label{{{label}}}",
        r"  \small",
        rf"  \begin{{tabular}}{{{col_spec}}}",
        r"    \toprule",
        "    " + " & ".join(f"\\textbf{{{c}}}" for c in df.columns) + r" \\",
        r"    \midrule",
    ]
    for _, row in df.iterrows():
        lines.append("    " + " & ".join(str(v) for v in row.values) + r" \\")
    lines += [
        r"    \bottomrule",
        r"  \end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(lines)


# ── Generación por n ──────────────────────────────────────────────────────────
def generate_per_n(df: pd.DataFrame, out_dir: Path):
    """Genera una tabla LaTeX por cada valor de n."""
    generated = []
    for n, group in df.groupby("n"):
        cols_show = ["purview_texto", "mecanismo_texto", "estrategia", "k",
                     "perdida_emd", "tiempo_ms", "memoria_mb", "convergio"]
        cols_show = [c for c in cols_show if c in group.columns]
        sub = group[cols_show].sort_values(["purview_texto", "mecanismo_texto",
                                            "k", "estrategia"])
        tex = df_to_latex_table(
            sub.reset_index(drop=True),
            caption=f"Resultados benchmark $n={n}$.",
            label=f"tab:bench_n{n}",
        )
        out_path = out_dir / f"benchmark_n{n}.tex"
        out_path.write_text(tex, encoding="utf-8")
        generated.append(str(out_path))
        print(f"  [OK] {out_path}")
    return generated


# ── Tabla resumen global ──────────────────────────────────────────────────────
def generate_summary(df: pd.DataFrame, out_dir: Path) -> str:
    """Genera tabla resumen con estadísticas agregadas."""
    num_cols = ["perdida_emd", "tiempo_ms", "memoria_mb"]
    num_cols = [c for c in num_cols if c in df.columns]
    agg = (df.dropna(subset=["perdida_emd"])
             .groupby(["n", "estrategia", "k"])[num_cols]
             .agg(["mean", "min", "max"])
             .round(4)
             .reset_index())
    # Aplanar MultiIndex de columnas
    agg.columns = [" ".join(str(c) for c in col).strip()
                   if isinstance(col, tuple) else col
                   for col in agg.columns]

    lines = [
        r"\begin{table}[H]",
        r"  \centering",
        r"  \caption{Resumen estadístico del benchmark (media, mín, máx).}",
        r"  \label{tab:bench_summary}",
        r"  \small",
        r"  \begin{tabular}{llrrrrrrrr}",
        r"    \toprule",
        r"    $n$ & Estrategia & $k$ & "
        + r"$\bar\phi$ & $\phi_\min$ & $\phi_\max$ & "
        + r"$\bar t$ (ms) & $t_\min$ & $t_\max$ \\",
        r"    \midrule",
    ]

    phi_mean = "perdida_emd mean" if "perdida_emd mean" in agg.columns else None
    for _, row in agg.iterrows():
        n_val = int(row["n"]) if "n" in row else "?"
        strat = str(row.get("estrategia", ""))
        k_val = int(row.get("k", 2))

        def g(col, fmt=".4f"):
            v = row.get(col, None)
            return f"{v:{fmt}}" if pd.notna(v) else "---"

        lines.append(
            f"    {n_val} & \\texttt{{{strat[:20]}}} & {k_val} & "
            f"{g('perdida_emd mean')} & {g('perdida_emd min')} & {g('perdida_emd max')} & "
            f"{g('tiempo_ms mean', '.1f')} & {g('tiempo_ms min', '.1f')} & "
            f"{g('tiempo_ms max', '.1f')} \\\\"
        )
    lines += [
        r"    \bottomrule",
        r"  \end{tabular}",
        r"\end{table}",
    ]
    out_path = out_dir / "benchmark_summary.tex"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [OK] {out_path}")
    return str(out_path)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Genera tablas LaTeX desde benchmark xlsx")
    parser.add_argument("--input", default=None, help="Ruta al benchmark xlsx")
    parser.add_argument("--out",   default=str(TABLES_DIR), help="Directorio de salida")
    parser.add_argument("--sheet", default="Resultados", help="Hoja del xlsx")
    args = parser.parse_args()

    # Encontrar archivo de entrada
    if args.input:
        src = Path(args.input)
    else:
        src = find_latest_benchmark()
    if src is None or not src.exists():
        print(f"[ERROR] No se encontró archivo benchmark en {RESULTS_DIR}")
        print("  Ejecuta: uv run python GeoMIP/src/benchmark.py --n 10")
        sys.exit(1)

    print(f"Leyendo: {src}")
    df = pd.read_excel(src, sheet_name=args.sheet)
    print(f"  {len(df)} filas, columnas: {list(df.columns)}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    generate_per_n(df, out_dir)
    generate_summary(df, out_dir)

    print(f"\nTablas LaTeX guardadas en: {out_dir}")


if __name__ == "__main__":
    main()
