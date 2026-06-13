"""Estrategias SIA: k=2 (bipartición) y k≥3 (k-particiones)."""

from src.controllers.strategies.force import BruteForce
from src.controllers.strategies.q_nodes import QNodes, KQNodes
from src.controllers.strategies.geometric import GeometricSIA, KGeoMIP, limpiar_cache_find_mip
from src.controllers.strategies.kpartition import KPartitionSIA

__all__ = [
    "BruteForce",
    "QNodes",
    "KQNodes",
    "GeometricSIA",
    "KGeoMIP",
    "KPartitionSIA",
    "limpiar_cache_find_mip",
]
