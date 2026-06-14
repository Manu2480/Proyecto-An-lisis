"""
Limpia GeoMIP/data/results: conserva finales canonicos, archiva checkpoints y duplicados.
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "GeoMIP/data/results"
ARCHIVE = RESULTS / "_archive" / "limpieza_2026-06-14"
RAPIDO = RESULTS / "rapido"
RAPIDO_ARCHIVE = RAPIDO / "_archive" / "2026-06-14"

# Finales canonicos a conservar en sitio
KEEP = {
    RAPIDO / "n10" / "n10_rapido_2026-06-12_23h00.xlsx",
    RAPIDO / "n15" / "n15_rapido_2026-06-13_00h58.xlsx",
    RAPIDO / "n20" / "n20_rapido_2026-06-13_00h58.xlsx",
    RAPIDO / "n22" / "n22_rapido_2026-06-13_08h02.xlsx",
    RAPIDO / "n25" / "n25_rapido_2026-06-13_09h37.xlsx",
    RAPIDO / "benchmark_rapido_2026-06-13_09h37.xlsx",
    RESULTS / "n10" / "qnodes_k2_n10_2026-06-13_10h24.xlsx",
    RESULTS / "n10" / "n10_completo_2026-05-17_16h56.xlsx",
    RESULTS / "n10" / "n10_completo_2026-05-17_16h56_qn_k2.xlsx",
    RESULTS / "n15" / "qnodes_k2_n15_2026-06-13_10h57.xlsx",
    RESULTS / "n15" / "n15_completo_2026-05-17_16h56.xlsx",
    RESULTS / "n15" / "n15_completo_2026-05-17_16h56_qn_k2.xlsx",
    RESULTS / "n20" / "qnodes_k2_n20_2026-06-13_20h19.xlsx",
    RESULTS / "n20" / "n20_completo_2026-05-18_04h38.xlsx",
    RESULTS / "n20" / "n20_completo_2026-05-18_04h38_qn_k2.xlsx",
    RESULTS / "n22" / "n22_completo_2026-05-20_02h29.xlsx",
    RESULTS / "comparativa" / "comparativa_long.csv",
}


def move_to(dest_dir: Path, src: Path) -> None:
    if not src.exists() or src.name.startswith("~$"):
        return
    if src.resolve() in {k.resolve() for k in KEEP if k.exists()}:
        return
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / src.name
    if target.exists():
        target = dest_dir / f"{src.stem}__dup{src.suffix}"
    try:
        shutil.move(str(src), str(target))
    except (PermissionError, OSError) as e:
        print(f"  omitido (bloqueado): {src.relative_to(RESULTS)} ({e})")
        return
    print(f"  archivado: {src.relative_to(RESULTS)} -> {target.relative_to(RESULTS)}")


def clean_rapido():
    print("\n[rapido]")
    RAPIDO_ARCHIVE.mkdir(parents=True, exist_ok=True)
    for sub in ["", "n10", "n15", "n20", "n22", "n25"]:
        folder = RAPIDO / sub if sub else RAPIDO
        if not folder.exists():
            continue
        for f in sorted(folder.glob("*.xlsx")):
            if f.name.startswith("~$"):
                continue
            if f.resolve() in {k.resolve() for k in KEEP if k.exists()}:
                continue
            dest = RAPIDO_ARCHIVE / (sub or "root")
            move_to(dest, f)
    for sub in ["n10", "n15", "n20", "n22", "n25"]:
        folder = RAPIDO / sub
        if not folder.exists():
            continue
        for f in sorted(folder.glob("checkpoint_*.xlsx")):
            move_to(RAPIDO_ARCHIVE / sub / "checkpoints", f)


def clean_n_folders():
    rules = {
        "n10": {
            "keep_glob": ["qnodes_k2_n10_*.xlsx", "n10_completo_*.xlsx"],
            "archive_glob": ["checkpoint_*.xlsx", "qnodes_k2_checkpoint_*.xlsx"],
        },
        "n15": {
            "keep_glob": ["qnodes_k2_n15_2026-06-13_10h57.xlsx", "n15_completo_*.xlsx"],
            "archive_glob": ["checkpoint_*.xlsx", "qnodes_k2_checkpoint_*.xlsx", "qnodes_k2_n15_2026-06-13_10h54.xlsx", "*_qn_k2_qn_k2.xlsx"],
        },
        "n20": {
            "keep_glob": ["qnodes_k2_n20_*.xlsx", "n20_completo_*.xlsx"],
            "archive_glob": ["qnodes_k2_checkpoint_*.xlsx"],
        },
        "n22": {
            "keep_glob": ["n22_completo_*.xlsx"],
            "archive_glob": ["checkpoint_*.xlsx"],
        },
        "n25": {
            "keep_glob": [],
            "archive_glob": ["*.log"],
        },
    }
    for n, cfg in rules.items():
        folder = RESULTS / n
        if not folder.exists():
            continue
        print(f"\n[{n}]")
        dest = ARCHIVE / n
        for pattern in cfg["archive_glob"]:
            for f in sorted(folder.glob(pattern)):
                move_to(dest, f)


def main():
    print("Limpieza results -> _archive/limpieza_2026-06-14")
    clean_rapido()
    clean_n_folders()
    print("\nFinales conservados:")
    for k in sorted(KEEP):
        if k.exists():
            print(f"  OK {k.relative_to(RESULTS)}")
        else:
            print(f"  -- {k.relative_to(RESULTS)} (no existe)")


if __name__ == "__main__":
    main()
