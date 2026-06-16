"""
Carpeta strategies: motores que buscan como partir una red en k grupos.

Este archivo solo importa y expone las estrategias para que el resto del
programa las use sin conocer cada archivo por separado.

Estrategias disponibles:
  BruteForce    - prueba todas las biparticiones (solo redes pequenas)
  QNodes        - algoritmo Q exacto para k=2 (KQNodes en el enunciado)
  GeometricSIA  - GeoMIP exacto para k=2 (KGeoMIP en el enunciado)
  KPartitionSIA - k-particiones k=2,3,4,5 con heuristicas

Guia detallada para principiantes:
  documentacion-sustentacion-kqgmip/GUIA_STRATEGIES_PRINCIPIANTES.txt
"""

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
