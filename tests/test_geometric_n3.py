# tests/test_geometric_n3.py
"""
Reproduce exactamente el Cuadro 4.2 del documento 2_GeoMIP.md para el
sistema N3C con estado inicial 000 y subsistema completo (ABC|ABC).

Tabla 4.2 — Costos de transición desde 000:
  Transición  | A      | B      | C
  000         | 0      | 0      | 0
  100         | 0      | 0      | 0.5
  010         | 0      | 0.5    | 0
  110         | 0      | 0.375  | 0.375
  001         | 0.5    | 0      | 0
  101         | 0.375  | 0      | 0.375
  011         | 0.375  | 0.375  | 0
  111         | 0.219  | 0.219  | 0.219  (= 14/64)
"""
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT    = Path(__file__).resolve().parents[1]
METHOD2 = ROOT / "GeoMIP" / "src" / "Method2_Dynamic_Programming_Reformulation"
SAMPLES = ROOT / "GeoMIP" / "data" / "samples"

if str(METHOD2) not in sys.path:
    sys.path.insert(0, str(METHOD2))

from src.controllers.manager import Manager
from src.controllers.strategies.geometric import GeometricSIA
from src.constants.base import ACTUAL, EFECTO


# Cuadro 4.2: transición → (tA, tB, tC)
TABLE_4_2 = {
    "000": (0.0,          0.0,          0.0),
    "100": (0.0,          0.0,          0.5),
    "010": (0.0,          0.5,          0.0),
    "110": (0.0,          0.375,        0.375),
    "001": (0.5,          0.0,          0.0),
    "101": (0.375,        0.0,          0.375),
    "011": (0.375,        0.375,        0.0),
    "111": (14/64,        14/64,        14/64),   # ≈ 0.21875
}


@pytest.fixture(scope="module")
def geo_n3c():
    """Prepara GeometricSIA sobre N3C con estado 000, subsistema completo."""
    tpm_path = SAMPLES / "N3C.csv"
    if not tpm_path.exists():
        pytest.skip(f"N3C.csv no encontrado en {SAMPLES}")
    tpm = np.genfromtxt(tpm_path, delimiter=",")
    estado, cond = "000", "111"
    geo = GeometricSIA(Manager(estado_inicial=estado))
    geo.sia_preparar_subsistema(cond, cond, cond, tpm)
    # Construir tabla manualmente igual que find_mip()
    geo._flat_data = [nc.data.ravel() for nc in geo.sia_subsistema.ncubos]
    geo.vertices = set(
        tuple((EFECTO, e) for e in geo.sia_subsistema.indices_ncubos)
        + tuple((ACTUAL, a) for a in geo.sia_subsistema.dims_ncubos)
    )
    dims = geo.sia_subsistema.dims_ncubos
    geo.estado_inicial = geo.sia_subsistema.estado_inicial[dims]
    geo.estado_final   = 1 - geo.estado_inicial
    geo.idx_ncubos     = list(range(len(geo.sia_subsistema.indices_ncubos)))
    ei = tuple(geo.estado_inicial.tolist())
    ef = tuple(geo.estado_final.tolist())
    geo.caminos = {0: [list(ei)]}
    geo.tabla_transiciones = {}
    geo.tabla_transiciones[(ei, ei)] = [0.0] * 3
    for nivel in range(1, 4):
        geo.calcular_costos_nivel(geo.estado_final, nivel)
    return geo, ei


class TestTable42:
    """Verifica cada celda del Cuadro 4.2."""

    @pytest.mark.parametrize("state_str,expected", TABLE_4_2.items())
    def test_costo(self, geo_n3c, state_str, expected):
        geo, ei = geo_n3c
        st = tuple(int(c) for c in state_str)
        key = (ei, st)
        got = geo.tabla_transiciones.get(key)
        assert got is not None, f"Transición {state_str} no está en tabla"
        for idx, (g, e) in enumerate(zip(got, expected)):
            assert g == pytest.approx(e, abs=1e-4), (
                f"t_{['A','B','C'][idx]}(000, {state_str}): "
                f"esperado={e:.5f} obtenido={g:.5f}"
            )


class TestGeometricN3FullRun:
    """Prueba la ejecución completa de GeometricSIA en N3C."""

    def test_aplica_estrategia_devuelve_solution(self):
        tpm_path = SAMPLES / "N3C.csv"
        if not tpm_path.exists():
            pytest.skip("N3C.csv no encontrado")
        tpm = np.genfromtxt(tpm_path, delimiter=",")
        geo = GeometricSIA(Manager(estado_inicial="000"))
        sol = geo.aplicar_estrategia("111", "111", "111", tpm)
        assert sol is not None
        assert hasattr(sol, "perdida")
        assert sol.perdida >= 0.0
        assert sol.n_nodos == 3
        assert sol.k == 2

    def test_loss_n3a_coincide_bruteforce(self):
        """GeometricSIA debe dar el mismo resultado que BruteForce en N3A."""
        from src.controllers.strategies.force import BruteForce
        tpm_path = SAMPLES / "N3A.csv"
        if not tpm_path.exists():
            pytest.skip("N3A.csv no encontrado")
        tpm = np.genfromtxt(tpm_path, delimiter=",")
        estado, c = "100", "111"
        geo = GeometricSIA(Manager(estado_inicial=estado))
        bf  = BruteForce(Manager(estado_inicial=estado))
        sol_geo = geo.aplicar_estrategia(c, c, c, tpm)
        sol_bf  = bf.aplicar_estrategia(c, c, c)
        assert sol_geo.perdida == pytest.approx(sol_bf.perdida, abs=1e-4), (
            f"Geometric={sol_geo.perdida} BruteForce={sol_bf.perdida}"
        )
