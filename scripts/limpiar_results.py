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
APROX = RESULTS / "aprox"
COMPARATIVA = RESULTS / "comparativa"

# Finales canonicos a conservar en sitio
KEEP = {
    RAPIDO / "n10" / "n10_rapido_2026-06-13_21h33.xlsx",
    RAPIDO / "n15" / "n15_rapido_2026-06-13_21h39.xlsx",
    RAPIDO / "n20" / "n20_rapido_2026-06-13_22h13.xlsx",
    RAPIDO / "n22" / "n22_rapido_2026-06-14_00h32.xlsx",
    RAPIDO / "n25" / "n25_rapido_2026-06-13_23h14.xlsx",
    RAPIDO / "benchmark_rapido_2026-06-14_00h32.xlsx",
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
    COMPARATIVA / "comparativa_long.csv",
    COMPARATIVA / "comparativa_resumen.xlsx",
    COMPARATIVA / "n10_comparativa.xlsx",
    COMPARATIVA / "n15_comparativa.xlsx",
    COMPARATIVA / "n20_comparativa.xlsx",
    COMPARATIVA / "n22_comparativa.xlsx",
    COMPARATIVA / "n25_comparativa.xlsx",
    APROX / "benchmark_aprox_2026-06-12_22h35.xlsx",
    APROX / "n10" / "n10_aprox_2026-06-12_22h35.xlsx",
    APROX / "n15" / "n15_aprox_2026-06-12_22h35.xlsx",
    RESULTS / "finales" / "benchmark_completo_2026-05-17_16h56.xlsx",
}

# Logs recientes a conservar (corridas jun 2026)
KEEP_LOGS = {
    "benchmark_n25_2026-06-13_22h15m16.stdout.log",
    "benchmark_n25_2026-06-13_22h15m16.stderr.log",
    "benchmark_n22_2026-06-13_23h14m48.stdout.log",
    "benchmark_n22_2026-06-13_23h14m48.stderr.log",
    "benchmark_n20_2026-06-13_21h45m04.stdout.log",
    "benchmark_n20_2026-06-13_21h45m04.stderr.log",
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


def _keep_latest_checkpoint(folder: Path, pattern: str) -> Path | None:
    files = sorted(folder.glob(pattern), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def clean_n_folders():
    rules = {
        "n10": {
            "archive_glob": ["checkpoint_*.xlsx", "qnodes_k2_checkpoint_*.xlsx"],
        },
        "n15": {
            "archive_glob": [
                "checkpoint_*.xlsx",
                "qnodes_k2_checkpoint_*.xlsx",
                "qnodes_k2_n15_2026-06-13_10h54.xlsx",
                "*_qn_k2_qn_k2.xlsx",
            ],
        },
        "n20": {
            "archive_glob": ["qnodes_k2_checkpoint_*.xlsx"],
        },
        "n22": {
            "archive_glob": ["checkpoint_*.xlsx", "qnodes_k2_checkpoint_*.xlsx"],
            "keep_latest_qnodes": True,
        },
        "n25": {
            "archive_glob": ["*.log"],
        },
    }
    for n, cfg in rules.items():
        folder = RESULTS / n
        if not folder.exists():
            continue
        print(f"\n[{n}]")
        dest = ARCHIVE / n
        latest_qn = None
        if cfg.get("keep_latest_qnodes"):
            latest_qn = _keep_latest_checkpoint(folder, "qnodes_k2_checkpoint_*.xlsx")
            if latest_qn:
                print(f"  conserva checkpoint activo: {latest_qn.name}")
        for pattern in cfg["archive_glob"]:
            for f in sorted(folder.glob(pattern)):
                if latest_qn and f.resolve() == latest_qn.resolve():
                    continue
                move_to(dest, f)


def clean_aprox():
    print("\n[aprox]")
    if not APROX.exists():
        return
    dest = ARCHIVE / "aprox"
    for sub in ["", "n10", "n15", "n20", "n22", "n25"]:
        folder = APROX / sub if sub else APROX
        if not folder.exists():
            continue
        for f in sorted(folder.glob("checkpoint_*.xlsx")):
            move_to(dest / (sub or "root"), f)
        for f in sorted(folder.glob("*.xlsx")):
            if f.name.startswith("~$"):
                continue
            if f.resolve() in {k.resolve() for k in KEEP if k.exists()}:
                continue
            move_to(dest / (sub or "root"), f)


def clean_root():
    print("\n[results root]")
    dest = ARCHIVE / "root"
    for f in sorted(RESULTS.glob("benchmark_completo_*.xlsx")):
        move_to(dest, f)


def clean_logs():
    print("\n[logs]")
    dest = ARCHIVE / "logs"
    logs_dir = RESULTS / "logs" / "n20_plus"
    if not logs_dir.exists():
        return
    for f in sorted(logs_dir.glob("*.log")):
        if f.name in KEEP_LOGS:
            continue
        move_to(dest, f)


def remove_temp_files():
    print("\n[temp]")
    for pattern in ["**/~$*.xlsx", "**/~$*.xls"]:
        for f in RESULTS.glob(pattern):
            try:
                f.unlink()
                print(f"  eliminado: {f.relative_to(RESULTS)}")
            except OSError as e:
                print(f"  omitido: {f.relative_to(RESULTS)} ({e})")
    untitled = ROOT / "Untitled"
    if untitled.exists():
        untitled.unlink()
        print("  eliminado: Untitled (raiz repo)")


def main():
    print("Limpieza results -> _archive/limpieza_2026-06-14")
    clean_rapido()
    clean_n_folders()
    clean_aprox()
    clean_root()
    clean_logs()
    remove_temp_files()
    print("\nFinales conservados:")
    for k in sorted(KEEP):
        if k.exists():
            print(f"  OK {k.relative_to(RESULTS)}")
        else:
            print(f"  -- {k.relative_to(RESULTS)} (no existe)")


if __name__ == "__main__":
    main()
