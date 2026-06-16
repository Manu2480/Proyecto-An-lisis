#!/usr/bin/env python3
"""
Una gráfica por matriz n (desde n{n}_comparativa.xlsx):

  outputs/plots/proyecto/n{n}/matriz_n{n}.png

  Panel izquierdo — Para k=2,3,4,5: el punto (tiempo, pérdida) de la mejor
                    estrategia disponible en ese k (menor pérdida; si empata, menor tiempo).

  Panel derecho  — QNodes k=2 de esa matriz: su (tiempo, pérdida) medio.

Ambos paneles comparten los mismos ejes para comparar visualmente.
"""
from __future__ import annotations

import argparse
import re
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
COMPARATIVA_DIR = ROOT / "GeoMIP" / "data" / "results" / "comparativa"
DIR_BASE = ROOT / "outputs" / "plots" / "proyecto"

NS_DEFAULT = [10, 15, 20, 22, 25]
KS = [2, 3, 4, 5]

# Candidatos por k (QNodes va solo en el panel derecho)
CANDIDATOS_K = {
    2: [("Rapido_MCTS", "MCTS"), ("Aprox_Geo", "Geo"), ("Exacto", "Geo")],
    3: [("Rapido_MCTS", "MCTS"), ("Aprox_KLmc", "KL+MC")],
    4: [("Rapido_MCTS", "MCTS"), ("Aprox_KLmc", "KL+MC")],
    5: [("Rapido_MCTS", "MCTS"), ("Aprox_KLmc", "KL+MC")],
}

COLOR_K = {2: "#e74c3c", 3: "#f39c12", 4: "#2ecc71", 5: "#3498db"}


def _latest(folder: Path, pattern: str) -> Path | None:
    files = sorted(folder.glob(pattern), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def wide_a_largo(wide: pd.DataFrame) -> pd.DataFrame:
    if wide.empty:
        return pd.DataFrame()

    modos: list[tuple[str, dict[str, str]]] = [
        ("QNodes", {"k2": "QN_k2"}),
        ("Rapido_MCTS", {f"k{k}": f"MCTS_k{k}" for k in KS}),
        ("Aprox_Geo", {"k2": "Geo_k2"}),
        ("Aprox_KLmc", {f"k{k}": f"KLmc_k{k}" for k in [3, 4, 5]}),
    ]
    if "KL_k3_perdida" in wide.columns:
        modos = [
            ("Exacto", {"k2": "Geo_k2", "k3": "QN_k3", "k4": "QN_k4", "k5": "QN_k5"}),
            ("Exacto_KL", {"k3": "KL_k3", "k4": "KL_k4", "k5": "KL_k5"}),
        ] + modos

    filas = []
    n = int(wide["n"].iloc[0])
    for _, row in wide.iterrows():
        for modo, prefijos in modos:
            for k_label, pref in prefijos.items():
                pcol, tcol = f"{pref}_perdida", f"{pref}_tiempo_ms"
                if pcol not in wide.columns:
                    continue
                perd, tiempo = row.get(pcol), row.get(tcol)
                if pd.isna(perd) or pd.isna(tiempo) or tiempo <= 0:
                    continue
                k_num = int(re.search(r"\d+", k_label).group()) if re.search(r"\d+", k_label) else 2
                filas.append({
                    "n": n, "#Prueba": row["#Prueba"], "modo": modo, "k": k_num,
                    "perdida": perd, "tiempo_ms": tiempo,
                })
    return pd.DataFrame(filas)


def cargar_n(n: int) -> tuple[pd.DataFrame, Path | None]:
    p = _latest(COMPARATIVA_DIR, f"n{n}_comparativa.xlsx")
    if p is None:
        return pd.DataFrame(), None
    return wide_a_largo(pd.read_excel(p)), p


def _media_estrategia(df: pd.DataFrame, modo: str, k: int) -> dict | None:
    sub = df[(df["modo"] == modo) & (df["k"] == k)]
    if sub.empty:
        return None
    return {
        "perdida": sub["perdida"].mean(),
        "tiempo_s": sub["tiempo_ms"].mean() / 1000.0,
        "casos": len(sub),
    }


def mejor_por_k(df: pd.DataFrame, k: int) -> dict | None:
    """Estrategia con menor pérdida media en k; empate → menor tiempo."""
    opciones = []
    for modo, nombre in CANDIDATOS_K[k]:
        m = _media_estrategia(df, modo, k)
        if m is None:
            continue
        opciones.append({"k": k, "estrategia": nombre, "modo": modo, **m})
    if not opciones:
        return None
    opciones.sort(key=lambda o: (o["perdida"], o["tiempo_s"]))
    return opciones[0]


def qnodes_k2(df: pd.DataFrame) -> dict | None:
    sub = df[(df["modo"] == "QNodes") & (df["k"] == 2)]
    if sub.empty:
        return None
    return {
        "k": 2,
        "estrategia": "QNodes",
        "perdida": sub["perdida"].mean(),
        "tiempo_s": sub["tiempo_ms"].mean() / 1000.0,
        "casos": len(sub),
    }


def _rango_tiempo(puntos: list[dict], factor_log: float = 2.0) -> tuple[float, float, bool]:
    xs = [p["tiempo_s"] for p in puntos if p["tiempo_s"] > 0]
    if not xs:
        return 1.0, 10.0, False
    use_log = max(xs) / min(xs) > 8
    if use_log:
        return min(xs) / factor_log, max(xs) * factor_log, True
    pad = (max(xs) - min(xs)) * 0.25 or max(xs) * 0.15 or 1.0
    return max(0.0, min(xs) - pad), max(xs) + pad, False


def _rango_perdida(puntos: list[dict]) -> tuple[float, float]:
    ys = [p["perdida"] for p in puntos]
    if not ys:
        return 0.0, 1.0
    ymin, ymax = min(ys), max(ys)
    if ymax - ymin < 1e-6:
        return max(0.0, ymin - 0.05), ymax + 0.15
    pad = (ymax - ymin) * 0.2 or 0.05
    return max(0.0, ymin - pad), ymax + pad


def _config_ejes(ax, puntos: list[dict], titulo_x: str, titulo_y: str) -> None:
    xlo, xhi, log_x = _rango_tiempo(puntos)
    ylo, yhi = _rango_perdida(puntos)
    if log_x:
        ax.set_xscale("log")
        ax.set_xlim(xlo, xhi)
        ax.set_xlabel(f"{titulo_x} (escala log)")
    else:
        ax.set_xlim(xlo, xhi)
        ax.set_xlabel(titulo_x)
    ax.set_ylim(ylo, yhi)
    ax.set_ylabel(titulo_y)
    ax.grid(True, alpha=0.35, which="both")


def _leyenda_puntos(ax, puntos: list[dict], loc: str = "best") -> None:
    handles = []
    for p in puntos:
        h = ax.scatter(
            [], [], s=100, c=COLOR_K.get(p["k"], "#333"),
            edgecolors="black", linewidths=0.6,
        )
        handles.append(h)
    labels = [
        f"k={p['k']} {p['estrategia']}: {p['perdida']:.4f} EMD, {p['tiempo_s']:.1f} s"
        for p in puntos
    ]
    ax.legend(handles, labels, loc=loc, fontsize=8, framealpha=0.95)


def _tabla_comparacion(ax, mejores: list[dict], qn: dict | None) -> None:
    ax.axis("off")
    if qn is None:
        ax.text(0.5, 0.5, "Sin QNodes k=2 para comparar", ha="center", va="center")
        return

    filas = [
        ["k", "Mejor estrat.", "Pérdida", "Tiempo (s)", "Δ pérdida vs QN", "QNodes más lento ×"],
    ]
    for m in mejores:
        delta = m["perdida"] - qn["perdida"]
        ratio = qn["tiempo_s"] / m["tiempo_s"] if m["tiempo_s"] > 0 else float("nan")
        filas.append([
            str(m["k"]),
            m["estrategia"],
            f"{m['perdida']:.4f}",
            f"{m['tiempo_s']:.1f}",
            f"{delta:+.4f}",
            f"×{ratio:.0f}" if ratio == ratio else "—",
        ])
    filas.append([
        "QN",
        "QNodes k=2",
        f"{qn['perdida']:.4f}",
        f"{qn['tiempo_s']:.1f}",
        "0 (ref.)",
        "×1",
    ])

    tabla = ax.table(
        cellText=filas[1:],
        colLabels=filas[0],
        loc="center",
        cellLoc="center",
    )
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(8)
    tabla.scale(1.05, 1.35)


def grafica_matriz(n: int, df: pd.DataFrame, fuente: Path) -> bool:
    mejores = [m for k in KS if (m := mejor_por_k(df, k))]
    qn = qnodes_k2(df)

    if not mejores and qn is None:
        print(f"  [SKIP] n={n}: sin datos")
        return False

    fig = plt.figure(figsize=(13, 7.5))
    gs = fig.add_gridspec(2, 2, height_ratios=[3.2, 1.2], hspace=0.45, wspace=0.28)
    ax_izq = fig.add_subplot(gs[0, 0])
    ax_der = fig.add_subplot(gs[0, 1])
    ax_tab = fig.add_subplot(gs[1, :])

    titulo_x = "Tiempo medio (s) — más rápido a la izquierda"
    titulo_y = "Pérdida media (EMD) — mejor abajo"

    # --- Izquierda: mejores por k (solo heurísticas, sin QNodes) ---
    ax_izq.set_title(
        "Mejor estrategia por k\n(menor pérdida; si empata, menor tiempo)",
        fontweight="bold",
    )
    for m in mejores:
        ax_izq.scatter(
            m["tiempo_s"], m["perdida"],
            s=160, c=COLOR_K.get(m["k"], "#333"),
            edgecolors="black", linewidths=0.8, zorder=5,
        )
        ax_izq.text(
            m["tiempo_s"], m["perdida"], f"  k={m['k']}",
            fontsize=9, fontweight="bold", va="center",
        )
    if len(mejores) > 1:
        orden = sorted(mejores, key=lambda x: x["k"])
        ax_izq.plot(
            [p["tiempo_s"] for p in orden],
            [p["perdida"] for p in orden],
            linestyle="--", color="gray", alpha=0.45, zorder=1,
        )
    _config_ejes(ax_izq, mejores, titulo_x, titulo_y)
    _leyenda_puntos(ax_izq, mejores, loc="upper right")

    # --- Derecha: solo QNodes k=2 (ejes propios, centrados en ese punto) ---
    ax_der.set_title("QNodes k=2 (baseline)", fontweight="bold")
    if qn is None:
        ax_der.text(0.5, 0.5, "Sin datos QNodes k=2", ha="center", va="center", transform=ax_der.transAxes)
    else:
        ax_der.scatter(
            qn["tiempo_s"], qn["perdida"],
            s=320, c=COLOR_K[2], marker="*",
            edgecolors="black", linewidths=0.8, zorder=5,
        )
        ax_der.annotate(
            f"QNodes k=2\n{qn['perdida']:.4f} EMD\n{qn['tiempo_s']:.1f} s\n({qn['casos']} casos)",
            (qn["tiempo_s"], qn["perdida"]),
            textcoords="offset points", xytext=(-90, 12),
            fontsize=9,
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white", alpha=0.9),
            arrowprops=dict(arrowstyle="->", color="gray"),
        )
        _config_ejes(ax_der, [qn], titulo_x, titulo_y)

    # --- Tabla resumen (comparación numérica clara) ---
    _tabla_comparacion(ax_tab, mejores, qn)

    fig.suptitle(f"Matriz n={n} — relación tiempo / pérdida", fontweight="bold", y=0.98)
    fig.text(
        0.5, 0.01,
        f"Fuente: {fuente.name} · Paneles con ejes independientes (izq. heurísticas k=2…5, der. QNodes k=2)",
        ha="center", fontsize=8, color="gray",
    )

    out_dir = DIR_BASE / f"n{n}"
    out_dir.mkdir(parents=True, exist_ok=True)
    ruta = out_dir / f"matriz_n{n}.png"
    fig.savefig(ruta, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {ruta.relative_to(ROOT)}")
    return True


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Gráfica tiempo/pérdida por matriz n")
    p.add_argument("--n", type=int, nargs="+", default=None, help="Redes (default: 10 15 20 22 25)")
    return p.parse_args()


def main():
    args = parse_args()
    ns = args.n if args.n else NS_DEFAULT

    print("=" * 60)
    print(f"Gráficas por matriz — n={','.join(map(str, ns))}")
    print("=" * 60)

    ok = 0
    for n in ns:
        df, path = cargar_n(n)
        if path is None:
            print(f"\n--- n={n} --- [SKIP: sin comparativa]")
            continue
        print(f"\n--- n={n} ({path.name}) ---")
        if grafica_matriz(n, df, path):
            ok += 1

    print(f"\nListo: {ok} gráfica(s) en {DIR_BASE.relative_to(ROOT)}/n{{n}}/matriz_n{{n}}.png")


if __name__ == "__main__":
    main()
