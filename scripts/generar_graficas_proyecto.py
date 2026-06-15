#!/usr/bin/env python3
"""
Gráficas del informe a partir de resultados reales del proyecto (n=10,15,20).

No modifica outputs/plots/ (plantilla DatosPruebas2026_1_filled.xlsx).
Salida: outputs/plots/proyecto/

Fuentes:
  - GeoMIP/data/results/comparativa/comparativa_long.csv
  - GeoMIP/data/results/n{n}/qnodes_k2_n{n}_*.xlsx (k=2 QNodes canónico)
  - GeoMIP/data/results/n{n}/n{n}_completo_*.xlsx (referencia en bitácora)
"""
from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid", font_scale=0.95)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "GeoMIP" / "data" / "results"
COMPARATIVA = RESULTS / "comparativa" / "comparativa_long.csv"
DIR_SALIDA = ROOT / "outputs" / "plots" / "proyecto"
DIR_SALIDA.mkdir(parents=True, exist_ok=True)

NS = [10, 15, 20]
K_VALS = [2, 3, 4, 5]

# Archivos canónicos (bitácora 39)
FUENTES = {
    10: {
        "completo": "n10_completo_2026-05-17_16h56.xlsx",
        "qnodes": "qnodes_k2_n10_2026-06-13_10h24.xlsx",
        "rapido": "rapido/n10/n10_rapido_2026-06-13_21h33.xlsx",
    },
    15: {
        "completo": "n15_completo_2026-05-17_16h56.xlsx",
        "qnodes": "qnodes_k2_n15_2026-06-13_10h57.xlsx",
        "rapido": "rapido/n15/n15_rapido_2026-06-13_21h39.xlsx",
    },
    20: {
        "completo": "n20_completo_2026-05-18_04h38.xlsx",
        "qnodes": "qnodes_k2_n20_2026-06-13_20h19.xlsx",
        "rapido": "rapido/n20/n20_rapido_2026-06-13_22h13.xlsx",
    },
}


def _latest(folder: Path, pattern: str) -> Path | None:
    files = sorted(folder.glob(pattern), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def cargar_qnodes(n: int) -> pd.DataFrame:
    folder = RESULTS / f"n{n}"
    p = _latest(folder, f"qnodes_k2_n{n}_*.xlsx")
    if p is None:
        return pd.DataFrame()
    df = pd.read_excel(p)
    return df.rename(columns={
        "QN_k2_perdida": "perdida",
        "QN_k2_tiempo_ms": "tiempo_ms",
    }).assign(
        n=n,
        estrategia="QNodes",
        k=2,
        tamano=lambda d: d["Purview"].astype(str).str.len(),
    )


def cargar_base() -> pd.DataFrame:
    if not COMPARATIVA.exists():
        raise SystemExit(f"[ERROR] Falta {COMPARATIVA}")
    df = pd.read_csv(COMPARATIVA)
    df = df[df["n"].isin(NS)].copy()
    df["tamano"] = df["Purview"].astype(str).str.len()
    return df


def etiqueta_modo(modo: str) -> str:
    return {
        "Exacto": "Geo/QN exacto",
        "Exacto_KL": "KL exacto",
        "Rapido_MCTS": "MCTS rápido",
        "Aprox_KLmc": "KL+MC aprox",
    }.get(modo, modo)


def _label_purview(tam: int | float) -> str:
    return f"|P|={int(tam)}"


def _nota_cobertura(df: pd.DataFrame, n: int) -> str:
    geo = df[(df["n"] == n) & (df["modo"] == "Exacto") & (df["k"] == 2)]
    mcts = df[(df["n"] == n) & (df["modo"] == "Rapido_MCTS") & (df["k"] == 2)]
    partes = []
    if len(geo) < 50:
        partes.append(f"Geo exacto k=2: {len(geo)}/50 casos en comparativa")
    if len(mcts) == 50:
        partes.append("MCTS rápido: 50/50")
    return " · ".join(partes)


def g1_tiempo_kparticiones(df: pd.DataFrame, n: int):
    """Tiempo vs tamaño del subsistema — benchmark exacto (k=2 Geo, k=3..5 QN)."""
    sub = df[(df["n"] == n) & (df["modo"] == "Exacto")].copy()
    if sub.empty:
        print(f"  [SKIP] n={n} g1: sin Exacto")
        return
    agg = sub.groupby(["tamano", "k"], as_index=False).agg(
        tiempo_ms=("tiempo_ms", "mean"),
        n_casos=("tiempo_ms", "count"),
    )
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    axes = axes.flatten()
    for idx, k in enumerate(K_VALS):
        ax = axes[idx]
        sk = agg[agg["k"] == k].sort_values("tamano")
        if sk.empty:
            ax.set_visible(False)
            continue
        label = "Geo k=2" if k == 2 else f"QN k={k}"
        ax.plot(sk["tamano"], sk["tiempo_ms"], marker="o", color="steelblue", linewidth=1.5)
        for _, row in sk.iterrows():
            if row["n_casos"] == 1:
                ax.annotate(
                    "1 caso", (row["tamano"], row["tiempo_ms"]),
                    textcoords="offset points", xytext=(4, 4), fontsize=7, color="gray",
                )
        ax.set_title(f"{label}", fontweight="bold")
        ax.set_xlabel("Tamaño del subsistema (|Purview|)")
        ax.set_ylabel("Tiempo medio (ms)")
        ax.yaxis.set_major_formatter(mticker.ScalarFormatter(useMathText=True))
        ax.ticklabel_format(style="sci", axis="y", scilimits=(0, 0))
        ax.grid(True, alpha=0.3)
    fig.suptitle(
        f"n={n} — Rendimiento temporal (benchmark exacto, DatosPruebas2026)",
        fontweight="bold", y=1.02,
    )
    plt.tight_layout()
    ruta = DIR_SALIDA / f"n{n}_g1_tiempo_exacto_k.png"
    fig.savefig(ruta, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {ruta.name}")


def g2_perdida_k2_estrategias(df: pd.DataFrame, qn: pd.DataFrame, n: int):
    """Boxplot pérdida k=2: QNodes vs Geo exacto vs MCTS rápido."""
    filas = []
    geo = df[(df["n"] == n) & (df["modo"] == "Exacto") & (df["k"] == 2)]
    mcts = df[(df["n"] == n) & (df["modo"] == "Rapido_MCTS") & (df["k"] == 2)]
    for _, r in geo.iterrows():
        filas.append({
            "tamano": r["tamano"],
            "estrategia": "Geometric (exacto)",
            "perdida": r["perdida"],
        })
    for _, r in mcts.iterrows():
        filas.append({
            "tamano": r["tamano"],
            "estrategia": "MCTS (rápido)",
            "perdida": r["perdida"],
        })
    for _, r in qn.iterrows():
        filas.append({
            "tamano": r["tamano"],
            "estrategia": "QNodes",
            "perdida": r["perdida"],
        })
    plot_df = pd.DataFrame(filas)
    if plot_df.empty:
        print(f"  [SKIP] n={n} g2: sin datos k=2")
        return
    plot_df["subsistema_label"] = plot_df["tamano"].map(_label_purview)
    orden = sorted(plot_df["tamano"].unique())
    orden_labels = [_label_purview(t) for t in orden]
    plt.figure(figsize=(max(8, len(orden) * 0.8), 5))
    ax = sns.boxplot(
        data=plot_df,
        x="subsistema_label", y="perdida",
        hue="estrategia",
        order=orden_labels,
        palette={"QNodes": "#3498db", "Geometric (exacto)": "#e67e22", "MCTS (rápido)": "#2ecc71"},
        linewidth=0.8, fliersize=2,
    )
    ax.set_xlabel("Tamaño del subsistema (|Purview|)")
    ax.set_ylabel("Pérdida (EMD)")
    ax.set_title(f"n={n} — Pérdida k=2 por estrategia (datos del proyecto)", fontweight="bold")
    nota = _nota_cobertura(df, n)
    if nota:
        ax.text(0.5, -0.22, nota, transform=ax.transAxes, ha="center", fontsize=8, color="gray")
    ax.legend(title="Estrategia", fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout(rect=(0, 0.06, 1, 1))
    ruta = DIR_SALIDA / f"n{n}_g2_perdida_k2_estrategias.png"
    plt.savefig(ruta, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"  -> {ruta.name}")


def g3_delta_qnodes_k2(df: pd.DataFrame, qn: pd.DataFrame, n: int):
    """Δ pérdida respecto a QNodes k=2 (baseline del enunciado)."""
    if qn.empty:
        print(f"  [SKIP] n={n} g3: sin QNodes")
        return
    base = qn[["#Prueba", "perdida", "tamano"]].rename(columns={"perdida": "perdida_qn"})
    merged = []
    for modo, nombre in [("Exacto", "Geometric"), ("Rapido_MCTS", "MCTS")]:
        sub = df[(df["n"] == n) & (df["modo"] == modo) & (df["k"] == 2)]
        if sub.empty:
            continue
        m = sub.merge(base, on="#Prueba", how="inner", suffixes=("", "_qn"))
        tam_col = "tamano" if "tamano" in m.columns else "tamano_qn"
        m["delta"] = m["perdida"] - m["perdida_qn"]
        m["estrategia"] = nombre
        m["tamano"] = m[tam_col]
        merged.append(m)
    if not merged:
        print(f"  [SKIP] n={n} g3: sin pares")
        return
    mdf = pd.concat(merged, ignore_index=True)
    agg = mdf.groupby(["tamano", "estrategia"], as_index=False)["delta"].mean()
    agg["subsistema_label"] = agg["tamano"].map(_label_purview)
    orden = sorted(agg["tamano"].unique())
    orden_labels = [_label_purview(t) for t in orden]
    plt.figure(figsize=(max(8, len(orden) * 0.7), 5))
    ax = sns.barplot(
        data=agg, x="subsistema_label", y="delta", hue="estrategia",
        order=orden_labels,
        palette={"Geometric": "#e67e22", "MCTS": "#2ecc71"},
    )
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Tamaño del subsistema (|Purview|)")
    ax.set_ylabel("Δ Pérdida (estrategia − QNodes)")
    ax.set_title(f"n={n} — Variación de pérdida k=2 vs QNodes (baseline)", fontweight="bold")
    ax.legend(title="Estrategia")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    ruta = DIR_SALIDA / f"n{n}_g3_delta_qnodes_k2.png"
    plt.savefig(ruta, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"  -> {ruta.name}")


def g4_kparticiones_exacto_vs_rapido(df: pd.DataFrame, n: int):
    """Pérdida media por k: paneles separados exacto vs MCTS (escalas distintas)."""
    sub = df[df["n"] == n].copy()
    sub["estrategia"] = sub["modo"].map(etiqueta_modo)
    agg = sub.groupby(["k", "estrategia"], as_index=False)["perdida"].mean()
    exacto_modos = ["Geo/QN exacto", "KL exacto", "KL+MC aprox"]
    agg_ex = agg[agg["estrategia"].isin(exacto_modos)]
    agg_mc = agg[agg["estrategia"] == "MCTS rápido"]

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    if not agg_ex.empty:
        sns.barplot(data=agg_ex, x="k", y="perdida", hue="estrategia", palette="Set2", ax=axes[0])
        axes[0].set_title("Modos exactos / aprox", fontweight="bold")
        axes[0].set_ylabel("Pérdida media (EMD)")
        axes[0].legend(title="Modo", fontsize=7)
    else:
        axes[0].set_visible(False)
    if not agg_mc.empty:
        sns.barplot(data=agg_mc, x="k", y="perdida", color="#e67e22", ax=axes[1])
        axes[1].set_title("MCTS rápido", fontweight="bold")
        axes[1].set_ylabel("Pérdida media (EMD)")
    else:
        axes[1].set_visible(False)
    for ax in axes:
        ax.set_xlabel("k")
        ax.grid(True, alpha=0.3)
    fig.suptitle(f"n={n} — Pérdida media por k y modo de ejecución", fontweight="bold", y=1.02)
    plt.tight_layout()
    ruta = DIR_SALIDA / f"n{n}_g4_perdida_modo_k.png"
    fig.savefig(ruta, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {ruta.name}")


def g5_escalado_tiempo_geo_k2(df: pd.DataFrame):
    """Tiempo medio Geo k=2 vs n (10, 15, 20)."""
    sub = df[(df["modo"] == "Exacto") & (df["k"] == 2)]
    agg = sub.groupby("n", as_index=False).agg(
        tiempo_medio_ms=("tiempo_ms", "mean"),
        tiempo_max_ms=("tiempo_ms", "max"),
        casos=("tiempo_ms", "count"),
    )
    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = np.arange(len(agg))
    labels = [f"n={int(v)}" for v in agg["n"]]
    ax.bar(x, agg["tiempo_medio_ms"], color="steelblue", alpha=0.85, label="Media")
    upper = (agg["tiempo_max_ms"] - agg["tiempo_medio_ms"]).values
    ax.errorbar(
        x, agg["tiempo_medio_ms"],
        yerr=[np.zeros(len(agg)), upper],
        fmt="none", color="black", capsize=4, label="Hasta máx. por red",
    )
    for idx, (_, row) in enumerate(agg.iterrows()):
        ax.annotate(
            f"max {row['tiempo_max_ms']/1000:.0f}s",
            (idx, row["tiempo_max_ms"]),
            textcoords="offset points", xytext=(0, 6), ha="center", fontsize=7,
        )
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Tamaño de red n")
    ax.set_ylim(bottom=0)
    ax.set_ylabel("Tiempo Geo k=2 (ms)")
    ax.text(
        0.5, -0.18,
        "n=15: media Geo k=2 sobre 19 casos con dato en comparativa (no 50).",
        transform=ax.transAxes, ha="center", fontsize=8, color="gray",
    )
    ax.yaxis.set_major_formatter(mticker.ScalarFormatter(useMathText=True))
    ax.ticklabel_format(style="sci", axis="y", scilimits=(0, 0))
    ax.set_title("Escalado temporal — Geometric exacto k=2 (n=10,15,20)", fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    ruta = DIR_SALIDA / "global_g5_escalado_tiempo_geo_k2.png"
    fig.savefig(ruta, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {ruta.name}")


def g6_qnodes_vs_geo_k2(df: pd.DataFrame, qnodes: dict[int, pd.DataFrame]):
    """Coincidencia QNodes vs Geo k=2 por red."""
    filas = []
    for n in NS:
        geo = df[(df["n"] == n) & (df["modo"] == "Exacto") & (df["k"] == 2)]
        qn = qnodes.get(n, pd.DataFrame())
        if geo.empty or qn.empty:
            continue
        m = geo.merge(
            qn[["#Prueba", "perdida"]].rename(columns={"perdida": "perdida_qn"}),
            on="#Prueba", how="inner",
        )
        tol = 1e-6
        iguales = (m["perdida"] - m["perdida_qn"]).abs() <= tol
        filas.append({
            "n": n,
            "casos": len(m),
            "iguales": int(iguales.sum()),
            "qn_mejor": int((m["perdida_qn"] < m["perdida"] - tol).sum()),
            "geo_mejor": int((m["perdida"] < m["perdida_qn"] - tol).sum()),
        })
    if not filas:
        return
    res = pd.DataFrame(filas)
    res["pct_igual"] = 100 * res["iguales"] / res["casos"]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = np.arange(len(res))
    w = 0.25
    ax.bar(x - w, res["iguales"], w, label="Iguales", color="#3498db")
    ax.bar(x, res["qn_mejor"], w, label="QNodes menor", color="#2ecc71")
    ax.bar(x + w, res["geo_mejor"], w, label="Geo menor", color="#e67e22")
    ax.set_xticks(x)
    ax.set_xticklabels([f"n={int(v)}" for v in res["n"]])
    ax.set_ylabel("Casos (#Prueba)")
    ax.set_title("QNodes k=2 vs Geometric exacto k=2 — concordancia", fontweight="bold")
    for idx, row in res.iterrows():
        ax.text(
            idx, row["casos"] + 1,
            f"{int(row['casos'])} casos",
            ha="center", fontsize=7, color="gray",
        )
    ax.text(
        0.5, -0.15,
        "n=15: solo 19 casos con Geo k=2 en comparativa (benchmark exacto parcial).",
        transform=ax.transAxes, ha="center", fontsize=8, color="gray",
    )
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    ruta = DIR_SALIDA / "global_g6_qnodes_vs_geo_k2.png"
    fig.savefig(ruta, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {ruta.name}")


def main():
    print("=" * 60)
    print("Gráficas proyecto K-QGMIP (n=10,15,20)")
    print(f"Salida: {DIR_SALIDA}")
    print("=" * 60)
    print("\nFuentes de datos:")
    print(f"  comparativa: {COMPARATIVA.relative_to(ROOT)}")
    for n, arch in FUENTES.items():
        print(f"  n={n}:")
        print(f"    completo: GeoMIP/data/results/n{n}/{arch['completo']}")
        print(f"    qnodes:   GeoMIP/data/results/n{n}/{arch['qnodes']}")
        print(f"    rapido:   GeoMIP/data/results/{arch['rapido']}")
    print()

    df = cargar_base()
    qnodes = {n: cargar_qnodes(n) for n in NS}

    for n in NS:
        print(f"\n--- n={n} ---")
        g1_tiempo_kparticiones(df, n)
        g2_perdida_k2_estrategias(df, qnodes[n], n)
        g3_delta_qnodes_k2(df, qnodes[n], n)
        g4_kparticiones_exacto_vs_rapido(df, n)

    print("\n--- globales ---")
    g5_escalado_tiempo_geo_k2(df)
    g6_qnodes_vs_geo_k2(df, qnodes)

    print(f"\nListo: {len(list(DIR_SALIDA.glob('*.png')))} PNG en outputs/plots/proyecto/")


if __name__ == "__main__":
    main()
