#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
R = Path(__file__).resolve().parents[1] / "GeoMIP/data/results"
for p in [
    R/"n20/n20_completo_2026-05-18_04h38.xlsx",
    R/"n20/qnodes_k2_n20_2026-06-13_20h19.xlsx",
]:
    df = pd.read_excel(p, nrows=1)
    print(p.name, [c for c in df.columns if "QN" in c or "Geo" in c])
