import re
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "GeoMIP/data/results/rapido/n25/n25_rapido_2026-06-13_09h37.xlsx"
df = pd.read_excel(p)
print("SHAPE:", df.shape)
print("COLUMNAS:", list(df.columns))

part_cols = [c for c in df.columns if "particion" in c.lower()]
print("\nColumnas particion:", part_cols)

def count_groups(s):
    """Cuenta grupos en formato QNodes: linea1 = purviews, linea2 = mecanismos."""
    if pd.isna(s):
        return None
    text = str(s).strip()
    if not text or text.lower().startswith("inviable"):
        return 0
    lines = text.splitlines()
    top = lines[0] if lines else text
    # cada grupo es |contenido| concatenado: |A,B||C,D|
    return len(re.findall(r"\|[^|]*\|", top))

for col in part_cols:
    m = re.search(r"k(\d+)", col, re.I)
    expected_k = int(m.group(1)) if m else None
    counts = df[col].map(count_groups)
    print(f"\n=== {col} (esperado k={expected_k}) ===")
    print("  no nulos:", df[col].notna().sum())
    if expected_k:
        bad = df[counts != expected_k][["#Prueba", "Purview", "Mecanismo", col]].copy()
        bad["grupos"] = counts[counts != expected_k]
        print(f"  filas con grupos != {expected_k}: {len(bad)}")
        if len(bad):
            print(bad.head(15).to_string(index=False))
            if len(bad) > 15:
                print(f"  ... y {len(bad)-15} mas")
    print("  distribucion grupos:", counts.value_counts().sort_index().to_dict())

# muestra ejemplos normales
for col in part_cols[:2]:
    print(f"\nEjemplo {col}:")
    for v in df[col].dropna().head(5):
        print(" ", repr(v)[:200])
