# tests/test_refinar_kl.py
"""_refinar_kl debe conservar exactamente k partes (sin duplicar)."""
import re
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
from src.controllers.strategies.kpartition import KPartitionSIA


def _count_groups(particion: str) -> int:
    top = str(particion).splitlines()[0]
    return len(re.findall(r"\|[^|]*\|", top))


@pytest.mark.parametrize("k", [2, 3, 4, 5])
def test_kl_mc_rapida_respeta_k_grupos(k):
    tpm_path = SAMPLES / "N5A.csv"
    if not tpm_path.exists():
        pytest.skip("N5A.csv no disponible")
    tpm = np.genfromtxt(tpm_path, delimiter=",")
    sol = KPartitionSIA(
        Manager(estado_inicial="10000"),
        k=k,
        forzar_heuristica="kl_mc",
        n_samples_mc=200,
        perdida_mc_final=True,
    ).aplicar_estrategia("11111", "11111", "11111", tpm)
    assert sol.k == k
    assert _count_groups(sol.particion) == k


def test_mcts_respeta_k_grupos():
    tpm_path = SAMPLES / "N5A.csv"
    if not tpm_path.exists():
        pytest.skip("N5A.csv no disponible")
    tpm = np.genfromtxt(tpm_path, delimiter=",")
    sol = KPartitionSIA(
        Manager(estado_inicial="10000"),
        k=3,
        forzar_heuristica="mcts",
        mcts_n_iter=40,
        mcts_n_samples=200,
        mcts_rollout_depth=3,
    ).aplicar_estrategia("11111", "11111", "11111", tpm)
    assert _count_groups(sol.particion) == 3
