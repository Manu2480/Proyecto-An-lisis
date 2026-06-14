"""Audita el ultimo n{n}_rapido_*.xlsx de una red."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "GeoMIP/src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rapido_validate import validate_rapido_df  # noqa: E402

RAPIDO = ROOT / "GeoMIP/data/results/rapido"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, required=True)
    args = parser.parse_args()

    folder = RAPIDO / f"n{args.n}"
    files = sorted(folder.glob(f"n{args.n}_rapido_*.xlsx"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise SystemExit(f"Sin archivo rapido para n={args.n}")
    path = files[-1]
    df = pd.read_excel(path)

    print(f"Archivo: {path.relative_to(ROOT)}")
    print(f"Filas: {len(df)}")
    ok, errors = validate_rapido_df(df)
    if ok:
        print("RESULTADO: APROBADO")
        raise SystemExit(0)
    for err in errors:
        print(f"  ! {err}")
    print("RESULTADO: RECHAZADO")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
