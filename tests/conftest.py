# tests/conftest.py
"""Configuración compartida de pytest para el proyecto K-QGMIP."""
import sys
from pathlib import Path

# Añadir las raíces de los módulos al PYTHONPATH para que pytest encuentre los paquetes.
ROOT = Path(__file__).resolve().parents[1]
METHOD2 = ROOT / "GeoMIP" / "src" / "Method2_Dynamic_Programming_Reformulation"
QNODES  = ROOT / "QNodes"

for p in (QNODES, METHOD2):   # Method2 al final → queda en posición 0 (máxima prioridad)
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

SAMPLES = ROOT / "GeoMIP" / "data" / "samples"
