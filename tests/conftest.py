# tests/conftest.py
"""Configuración compartida de pytest para el proyecto K-QGMIP."""
import sys
from pathlib import Path

# Solo Method2 aquí — QNodes define otro árbol `src/` incompatible y debe evitarse en pytest.
ROOT = Path(__file__).resolve().parents[1]
METHOD2 = ROOT / "GeoMIP" / "src" / "Method2_Dynamic_Programming_Reformulation"

if str(METHOD2) not in sys.path:
    sys.path.insert(0, str(METHOD2))

SAMPLES = ROOT / "GeoMIP" / "data" / "samples"
