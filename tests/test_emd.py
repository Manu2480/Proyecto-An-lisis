# tests/test_emd.py
"""
Verifica la función emd_efecto con ejemplos numéricos conocidos del documento
Ejemplos.md (hoja EMD).

Propiedad: dado que los nodos son condicionalmente independientes,
  EMD(p, q) = sum_i |p_i - q_i|
donde p_i, q_i son las probabilidades marginales de que el nodo i esté OFF.

Ejemplo del documento (hoja EMD):
  p = (B=0:0.5, B=1:0, C=0:0.5, C=1:0)  → marginals B=(0.5,0.5), C=(0.5,0.5)
  q = (B=0:0.25, B=1:0.25, C=0:0.25, C=1:0.25) → marginals B=(0.5,0.5), C=(0.5,0.5)
  EMD = |0.5-0.5| + |0.5-0.5| = 0

  Ejemplo II (hoja II):
  SC (sistema completo) B=0: 0.5  B=1: 0.5
  SP (sistema partido)  B=0: 0.75 B=1: 0.25
  EMD = |0.5 - 0.75| = 0.25
"""
import sys
from pathlib import Path
import numpy as np
import pytest

# Asegurar que conftest.py ya agregó Method2 al path
METHOD2 = Path(__file__).resolve().parents[1] / "GeoMIP" / "src" / "Method2_Dynamic_Programming_Reformulation"
if str(METHOD2) not in sys.path:
    sys.path.insert(0, str(METHOD2))

from src.funcs.base import emd_efecto


class TestEmdEfecto:
    """Pruebas unitarias para emd_efecto (EMD analítico)."""

    def test_distribuciones_identicas(self):
        """EMD entre distribuciones idénticas debe ser 0."""
        u = np.array([0.25, 0.75])
        v = np.array([0.25, 0.75])
        assert emd_efecto(u, v) == pytest.approx(0.0)

    def test_ejemplo_doc_hoja_emd_cero(self):
        """
        Ejemplo hoja EMD del doc: marginales idénticas → EMD = 0.
        p_B = (0.5, 0.5), q_B = (0.5, 0.5)
        p_C = (0.5, 0.5), q_C = (0.5, 0.5)
        """
        p = np.array([0.5, 0.5])
        q = np.array([0.5, 0.5])
        assert emd_efecto(p, q) == pytest.approx(0.0)

    def test_ejemplo_doc_hoja_ii(self):
        """
        Ejemplo hoja II del doc: SC vs SP para B.
        emd_efecto recibe P(nodo=OFF) para cada nodo.
        SC: P(B=OFF)=0.5   SP: P(B=OFF)=0.75
        EMD = |0.5 - 0.75| = 0.25  (un solo nodo)
        """
        sc = np.array([0.5])   # P(B=OFF) del sistema completo
        sp = np.array([0.75])  # P(B=OFF) del sistema partido
        assert emd_efecto(sc, sp) == pytest.approx(0.25, abs=1e-6)

    def test_emd_ejemplo_particion(self):
        """
        Hoja EjParticion del doc: EMD(SO, SP) con mecanismo AC sobre purview ABC.
        Para nodo B: P(B_OFF|SC)=0.5, P(B_OFF|SP)=0.75 → diff=0.25
        """
        so = np.array([0.5])
        sp = np.array([0.75])
        result = emd_efecto(so, sp)
        assert result == pytest.approx(0.25, abs=1e-6)

    def test_emd_multivar(self):
        """
        Para sistemas con múltiples nodos, EMD = sum de diferencias absolutas
        de marginales (independencia condicional).
        """
        u = np.array([0.3, 0.7, 0.2, 0.8])
        v = np.array([0.5, 0.5, 0.5, 0.5])
        expected = sum(abs(a - b) for a, b in zip(u, v))
        assert emd_efecto(u, v) == pytest.approx(expected, abs=1e-9)

    def test_emd_simetria(self):
        """EMD debe ser simétrica: emd(u,v) == emd(v,u)."""
        u = np.array([0.1, 0.4, 0.3, 0.2])
        v = np.array([0.25, 0.25, 0.25, 0.25])
        assert emd_efecto(u, v) == pytest.approx(emd_efecto(v, u), abs=1e-9)

    def test_emd_no_negativa(self):
        """EMD siempre debe ser ≥ 0."""
        rng = np.random.default_rng(42)
        for _ in range(50):
            n = rng.integers(2, 20)
            u = rng.random(n)
            v = rng.random(n)
            assert emd_efecto(u, v) >= 0.0
