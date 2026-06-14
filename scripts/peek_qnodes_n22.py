import pandas as pd
from pathlib import Path

ROOT = Path("/mnt/c/Users/Manu/Documents/Semestre 2026 - 01/Analisis y diseño de algoritmos/proyecto/projecto-analisis-20261")
folder = ROOT / "GeoMIP/data/results/n22"
files = sorted(folder.glob("qnodes_k2_checkpoint_*.xlsx"), key=lambda p: p.stat().st_mtime)
if not files:
    print("sin checkpoints")
    raise SystemExit(0)
p = files[-1]
df = pd.read_excel(p)
print("archivo:", p.name)
print("filas:", len(df))
print("ultimo #Prueba:", int(df["#Prueba"].max()))
last = df.iloc[-1]
print("ultimo OK:", last["Purview"][:22], "/", str(last["Mecanismo"])[:22])
print("siguiente seria caso:", int(df["#Prueba"].max()) + 1)
