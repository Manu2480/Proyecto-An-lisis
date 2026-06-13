"""Rutas canónicas del proyecto GeoMIP (única fuente de verdad)."""
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parent
GEOMIP_ROOT = SRC_ROOT.parent
SAMPLES_DIR = GEOMIP_ROOT / "data" / "samples"
RESULTS_DIR = GEOMIP_ROOT / "data" / "results"
METHOD2_ROOT = SRC_ROOT / "Method2_Dynamic_Programming_Reformulation"
