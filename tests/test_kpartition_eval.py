# tests/test_kpartition_eval.py
"""
Cumplimiento del enunciado K-QGMIP:
  - KPartitionSIA(k=2) debe coincidir con GeometricSIA (misma pérdida/partición).
  - _evaluar_particion: vacía → inf, finita ≥ 0, coherencia con _reconstruir_tensor.
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
from src.controllers.strategies.kpartition import KPartitionSIA
from src.funcs.base import emd_causal, emd_efecto


def _biparticion_desde_mip(kp, mip):
    """Convierte la salida de find_mip en lista de (presentes, futuros)."""
    parte1 = list(mip)
    parte2 = kp.geometric_base.nodes_complement(list(mip))
    partes = [kp._decode_part(parte1), kp._decode_part(parte2)]
    return [p for p in partes if p[0] or p[1]]


def _prepare_kpart(name: str, estado: str, k: int = 2):
    """Prepara KPartitionSIA con subsistema listo para evaluar particiones."""
    tpm_path = SAMPLES / f"{name}.csv"
    if not tpm_path.exists():
        return None
    tpm = np.genfromtxt(tpm_path, delimiter=",")
    cond = "1" * len(estado)
    kp = KPartitionSIA(Manager(estado_inicial=estado), k=k)
    kp.sia_preparar_subsistema(cond, cond, cond, tpm)
    return kp


class TestK2EquivaleGeometric:
    """KPartitionSIA(k=2) delega en GeometricSIA y debe dar el mismo resultado."""

    CASES = [
        ("N3A", "100"),
        ("N5A", "10000"),
    ]

    @pytest.mark.parametrize("name,estado", CASES)
    def test_misma_perdida_que_geometric(self, name, estado):
        tpm_path = SAMPLES / f"{name}.csv"
        if not tpm_path.exists():
            pytest.skip(f"{name}.csv no disponible")
        tpm = np.genfromtxt(tpm_path, delimiter=",")
        cond = "1" * len(estado)
        mgr = Manager(estado_inicial=estado)

        sol_geo = GeometricSIA(mgr).aplicar_estrategia(cond, cond, cond, tpm)
        sol_k2  = KPartitionSIA(Manager(estado_inicial=estado), k=2).aplicar_estrategia(
            cond, cond, cond, tpm
        )

        assert sol_k2.k == 2
        assert sol_geo.perdida == pytest.approx(sol_k2.perdida, abs=1e-6)
        assert sol_geo.particion.strip() == sol_k2.particion.strip()

    @pytest.mark.parametrize("name,estado", CASES)
    def test_find_k_partition_equivale_aplicar_estrategia(self, name, estado):
        tpm_path = SAMPLES / f"{name}.csv"
        if not tpm_path.exists():
            pytest.skip(f"{name}.csv no disponible")
        tpm = np.genfromtxt(tpm_path, delimiter=",")
        cond = "1" * len(estado)
        kp = KPartitionSIA(Manager(estado_inicial=estado), k=2)

        sol_via = kp.aplicar_estrategia(cond, cond, cond, tpm)
        sol_find = kp.find_k_partition(cond, cond, cond, tpm)

        assert sol_via.perdida == pytest.approx(sol_find.perdida, abs=1e-6)
        assert sol_via.particion.strip() == sol_find.particion.strip()


class TestEvaluarParticion:
    """Pruebas unitarias de _evaluar_particion."""

    def test_particion_vacia_retorna_inf(self):
        kp = _prepare_kpart("N3A", "100", k=2)
        if kp is None:
            pytest.skip("N3A.csv no disponible")
        assert kp._evaluar_particion([]) == float("inf")

    def test_perdida_finita_no_negativa(self):
        kp = _prepare_kpart("N3A", "100", k=2)
        if kp is None:
            pytest.skip("N3A.csv no disponible")
        mip = kp._construir_tabla_costos()
        partes = _biparticion_desde_mip(kp, mip)
        perdida = kp._evaluar_particion(partes)
        assert np.isfinite(perdida)
        assert perdida >= 0.0

    def test_reconstruir_tensor_coherente_con_emd_efecto(self):
        kp = _prepare_kpart("N3A", "100", k=2)
        if kp is None:
            pytest.skip("N3A.csv no disponible")
        mip = kp._construir_tabla_costos()
        partes = _biparticion_desde_mip(kp, mip)

        sis_part = kp._k_partir(partes)
        dist_part = sis_part.distribucion_marginal()
        dist_orig = kp.sia_dists_marginales

        tensor_part = kp._reconstruir_tensor(dist_part)
        tensor_orig = kp._reconstruir_tensor(dist_orig)

        assert tensor_part.size == 2 ** len(dist_part)
        assert tensor_orig.size == 2 ** len(dist_orig)
        assert tensor_part.sum() == pytest.approx(1.0, abs=1e-6)
        assert tensor_orig.sum() == pytest.approx(1.0, abs=1e-6)

        emd_marginal = emd_efecto(dist_part, dist_orig)
        emd_tensor   = emd_causal(tensor_part, tensor_orig)
        assert emd_marginal == pytest.approx(emd_tensor, abs=1e-5)

    def test_evaluar_coincide_con_emd_efecto_manual(self):
        kp = _prepare_kpart("N5A", "10000", k=3)
        if kp is None:
            pytest.skip("N5A.csv no disponible")
        kp.k = 3
        mip = kp._construir_tabla_costos()
        partes = kp._heuristica_greedy(mip)

        perdida_fn = kp._evaluar_particion(partes)
        sis_part = kp._k_partir(partes)
        dist_part = sis_part.distribucion_marginal()
        perdida_manual = emd_efecto(dist_part, kp.sia_dists_marginales)

        assert perdida_fn == pytest.approx(perdida_manual, abs=1e-6)
