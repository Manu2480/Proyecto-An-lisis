# tests/test_solutions.py
"""
Verifica que todas las estrategias disponibles en Method2 devuelvan un
objeto Solution válido con los campos mínimos requeridos.
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

from src.models.core.solution import Solution
from src.controllers.manager import Manager
from src.controllers.strategies.geometric import GeometricSIA
from src.controllers.strategies.kpartition import KPartitionSIA
from src.controllers.strategies.force import BruteForce
from src.controllers.strategies.q_nodes import QNodes


TPM_SMALL = SAMPLES / "N3A.csv"
ESTADO    = "100"
COND      = "111"


@pytest.fixture(scope="module")
def tpm_n3a():
    if not TPM_SMALL.exists():
        pytest.skip("N3A.csv no disponible")
    return np.genfromtxt(TPM_SMALL, delimiter=",")


REQUIRED_ATTRS = ["perdida", "particion", "estrategia", "tiempo_ejecucion",
                  "tiempo_ms", "n_nodos", "k",
                  "distribucion_subsistema", "distribucion_particion"]


def _check_solution(sol: Solution):
    """Verifica que sol tenga todos los atributos requeridos y tipos correctos."""
    for attr in REQUIRED_ATTRS:
        assert hasattr(sol, attr), f"Solution no tiene el atributo '{attr}'"
    # perdida: float o None (para inviables)
    if sol.perdida is not None:
        assert isinstance(sol.perdida, (float, int, np.floating)), (
            f"perdida debe ser numérico, es {type(sol.perdida)}"
        )
        assert sol.perdida >= 0.0, f"perdida debe ser >= 0, es {sol.perdida}"
    assert isinstance(sol.estrategia, str) and sol.estrategia, "estrategia debe ser str no vacío"
    assert sol.tiempo_ejecucion >= 0.0
    assert sol.tiempo_ms == pytest.approx(sol.tiempo_ejecucion * 1000.0)
    assert sol.k >= 2, f"k debe ser >= 2, es {sol.k}"


class TestSolutionGeometric:
    def test_geometric_devuelve_solution(self, tpm_n3a):
        sol = GeometricSIA(Manager(estado_inicial=ESTADO)).aplicar_estrategia(
            COND, COND, COND, tpm_n3a
        )
        assert isinstance(sol, Solution)
        _check_solution(sol)
        assert sol.n_nodos == 3
        assert sol.k == 2

    def test_geometric_distribucion_no_vacia(self, tpm_n3a):
        sol = GeometricSIA(Manager(estado_inicial=ESTADO)).aplicar_estrategia(
            COND, COND, COND, tpm_n3a
        )
        assert sol.distribucion_subsistema is not None
        assert len(sol.distribucion_subsistema) > 0


class TestSolutionBruteForce:
    def test_bruteforce_devuelve_solution(self, tpm_n3a):
        sol = BruteForce(Manager(estado_inicial=ESTADO)).aplicar_estrategia(
            COND, COND, COND
        )
        assert isinstance(sol, Solution)
        _check_solution(sol)

    def test_bruteforce_perdida_no_negativa(self, tpm_n3a):
        sol = BruteForce(Manager(estado_inicial=ESTADO)).aplicar_estrategia(
            COND, COND, COND
        )
        assert sol.perdida >= 0.0


class TestSolutionKPartition:
    @pytest.mark.parametrize("k", [3, 4])
    def test_kpart_devuelve_solution(self, tpm_n3a, k):
        sol = KPartitionSIA(Manager(estado_inicial="10000"), k=k).aplicar_estrategia(
            "11111", "11111", "11111",
            np.genfromtxt(SAMPLES / "N5A.csv", delimiter=",")
            if (SAMPLES / "N5A.csv").exists()
            else tpm_n3a
        )
        assert isinstance(sol, Solution)
        assert hasattr(sol, "perdida")
        assert hasattr(sol, "k")

    def test_kpart_inviable_es_solution(self):
        """k > total_nodos (indices+dims=6 en N3 completo) devuelve Solution con Inviable."""
        tpm = np.genfromtxt(TPM_SMALL, delimiter=",") if TPM_SMALL.exists() else None
        if tpm is None:
            pytest.skip("N3A.csv no disponible")
        sol = KPartitionSIA(Manager(estado_inicial=ESTADO), k=7).aplicar_estrategia(
            COND, COND, COND, tpm
        )
        assert isinstance(sol, Solution)
        assert "Inviable" in str(sol.particion)


class TestSolutionQNodes:
    def test_qnodes_devuelve_solution(self, tpm_n3a):
        # QNodes en Method2 no acepta tpm como argumento posicional
        sol = QNodes(Manager(estado_inicial=ESTADO)).aplicar_estrategia(
            COND, COND, COND
        )
        assert isinstance(sol, Solution)
        _check_solution(sol)


class TestSolutionCamposNuevos:
    """Verifica específicamente los campos añadidos en la estandarización."""

    def test_tiempo_ms_es_propiedad(self, tpm_n3a):
        sol = GeometricSIA(Manager(estado_inicial=ESTADO)).aplicar_estrategia(
            COND, COND, COND, tpm_n3a
        )
        assert sol.tiempo_ms == pytest.approx(sol.tiempo_ejecucion * 1000.0)

    def test_k_default_es_2(self, tpm_n3a):
        sol = GeometricSIA(Manager(estado_inicial=ESTADO)).aplicar_estrategia(
            COND, COND, COND, tpm_n3a
        )
        assert sol.k == 2

    def test_n_nodos_correcto(self, tpm_n3a):
        sol = GeometricSIA(Manager(estado_inicial=ESTADO)).aplicar_estrategia(
            COND, COND, COND, tpm_n3a
        )
        assert sol.n_nodos == 3
