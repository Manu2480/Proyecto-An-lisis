"""Audita archivos rapido: grupos en particion vs k esperado."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAPIDO = ROOT / "GeoMIP/data/results/rapido"


def count_groups(s) -> int | None:
    if pd.isna(s):
        return None
    text = str(s).strip()
    if not text or text.lower().startswith("inviable"):
        return 0
    top = text.splitlines()[0]
    return len(re.findall(r"\|[^|]*\|", top))


def audit_file(path: Path) -> dict:
    df = pd.read_excel(path)
    part_cols = [c for c in df.columns if "particion" in c.lower()]
    out = {"archivo": str(path.relative_to(ROOT)), "filas": len(df), "columnas_k": {}}
    for col in part_cols:
        m = re.search(r"k(\d+)", col, re.I)
        if not m:
            continue
        k = int(m.group(1))
        counts = df[col].map(count_groups)
        mas = int((counts > k).sum())
        menos = int((counts < k).sum())
        ok = int((counts == k).sum())
        out["columnas_k"][col] = {
            "k": k,
            "ok": ok,
            "mas_de_k": mas,
            "menos_de_k": menos,
            "bad": mas + menos,
            "pct_mas": round(100 * mas / len(df), 1) if len(df) else 0,
            "pct_menos": round(100 * menos / len(df), 1) if len(df) else 0,
            "mas_pruebas": sorted(df.loc[counts > k, "#Prueba"].tolist()) if mas else [],
            "menos_pruebas": sorted(df.loc[counts < k, "#Prueba"].tolist()) if menos else [],
        }
    return out


def main():
    # Finales canonicos: ultimo n*_rapido por carpeta n*
    targets: list[Path] = []
    for n in (10, 15, 20, 22, 25):
        folder = RAPIDO / f"n{n}"
        if not folder.exists():
            continue
        finals = sorted(folder.glob(f"n{n}_rapido_*.xlsx"), key=lambda p: p.stat().st_mtime)
        if finals:
            targets.append(finals[-1])

    # Consolidados en raiz rapido
    targets.extend(sorted(RAPIDO.glob("benchmark_rapido_*.xlsx"), key=lambda p: p.stat().st_mtime))

    print("AUDITORIA PARTICIONES RAPIDO")
    print("=" * 70)
    for p in targets:
        r = audit_file(p)
        print(f"\n{r['archivo']}  ({r['filas']} filas)")
        for col, info in r["columnas_k"].items():
            flag = ""
            if info["mas_de_k"]:
                flag = " *** BUG _refinar_kl"
            elif info["menos_de_k"]:
                flag = " (menos de k: partes vacias MCTS)"
            else:
                flag = " OK"
            print(
                f"  {col}: {info['ok']}/{r['filas']} ok | "
                f"+{info['mas_de_k']} grupos de mas ({info['pct_mas']}%) | "
                f"-{info['menos_de_k']} grupos de menos ({info['pct_menos']}%){flag}"
            )
            if info["mas_pruebas"]:
                pr = info["mas_pruebas"]
                print(f"    mas: {pr[:10]}{'...' if len(pr)>10 else ''}")
            if info["menos_pruebas"] and info["mas_de_k"] == 0:
                pr = info["menos_pruebas"]
                print(f"    menos: {pr[:10]}{'...' if len(pr)>10 else ''}")

    print("\n" + "=" * 70)
    print(f"Archivos auditados: {len(targets)}")


if __name__ == "__main__":
    main()
