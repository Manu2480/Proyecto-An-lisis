# tests/test_qnodes_memo.py
"""QNodes con memoización: misma pérdida que referencia y uso de caché."""
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
METHOD2 = ROOT / "GeoMIP" / "src" / "Method2_Dynamic_Programming_Reformulation"
SAMPLES = ROOT / "GeoMIP" / "data" / "samples"

if str(METHOD2) not in sys.path:
    sys.path.insert(0, str(METHOD2))

from src.controllers.manager import Manager
from src.controllers.strategies.q_nodes import QNodes


@pytest.fixture(scope="module")
def tpm_n3a():
    p = SAMPLES / "N3A.csv"
    if not p.exists():
        pytest.skip("N3A.csv no disponible")
    return np.genfromtxt(p, delimiter=",")


def test_qnodes_memo_misma_perdida_n3a(tpm_n3a):
    """La optimización no debe cambiar el resultado en N3A (vs BruteForce k=2)."""
    from src.controllers.strategies.force import BruteForce

    mgr = Manager(estado_inicial="100")
    sol_bf = BruteForce(Manager(estado_inicial="100")).aplicar_estrategia(
        "111", "111", "111"
    )
    sol_qn = QNodes(Manager(estado_inicial="100")).aplicar_estrategia(
        "111", "111", "111", tpm_n3a
    )
    assert sol_qn.perdida == pytest.approx(sol_bf.perdida, rel=0, abs=1e-6)


def test_qnodes_memo_llena_cache(tpm_n3a):
    qn = QNodes(Manager(estado_inicial="100"))
    qn.aplicar_estrategia("111", "111", "111", tpm_n3a)
    assert len(qn.memoria_omega) > 0
