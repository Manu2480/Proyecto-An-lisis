"""
Estrategia Phi: usa la libreria externa PyPhi para encontrar biparticiones.

No es el motor principal del benchmark del proyecto, pero sirve como referencia
academica (teoria de informacion integrada). Compara resultados con nuestros
metodos propios si hace falta.

Cuando se usa: pruebas opcionales, no en DatosPruebas2026 por defecto.

Guia para principiantes:
  documentacion-sustentacion-kqgmip/GUIA_STRATEGIES_PRINCIPIANTES.txt
"""
import time
import numpy as np
from src.funcs.base import ABECEDARY, lil_endian
from src.funcs.format import fmt_biparticion
from src.controllers.manager import Manager

import math
import collections
from collections.abc import Iterable, Mapping, MutableMapping, Sequence

# Python 3.10+ moved these aliases to collections.abc; pyphi still imports from collections.
if not hasattr(collections, "Iterable"):
    setattr(collections, "Iterable", Iterable)
if not hasattr(collections, "Mapping"):
    setattr(collections, "Mapping", Mapping)
if not hasattr(collections, "MutableMapping"):
    setattr(collections, "MutableMapping", MutableMapping)
if not hasattr(collections, "Sequence"):
    setattr(collections, "Sequence", Sequence)

from pyphi import Network, Subsystem
from pyphi.labels import NodeLabels
from pyphi.models.cuts import Bipartition, Part

from src.middlewares.slogger import SafeLogger
from src.middlewares.profile import profiler_manager, profile

from src.models.base.sia import SIA
from src.models.core.solution import Solution
from src.models.enums.distance import MetricDistance
from src.models.base.application import aplicacion


from src.constants.base import (
    NET_LABEL,
    TYPE_TAG,
    STR_ONE,
)
from src.constants.models import (
    DUMMY_ARR,
    DUMMY_PARTITION,
    PYPHI_LABEL,
    PYPHI_STRAREGY_TAG,
    PYPHI_ANALYSIS_TAG,
)


class Phi(SIA):
    """
    Busca la mejor biparticion con PyPhi (effect_mip o cause_mip).

    Recibe un gestor con la red y el estado inicial.
    """

    def __init__(self, config: Manager) -> None:
        """Guarda el gestor y prepara el registro de tiempos."""
        super().__init__(config)
        profiler_manager.start_session(
            f"{NET_LABEL}{len(config.estado_inicial)}{config.pagina}"
        )
        self.logger = SafeLogger(PYPHI_STRAREGY_TAG)

    @profile(context={TYPE_TAG: PYPHI_ANALYSIS_TAG})
    def aplicar_estrategia(self, condiciones: str, alcance: str, mecanismo: str):
        """
        Punto de entrada: analiza un subsistema y devuelve la mejor biparticion.

        Recibe:
          condiciones - cadena de 0 y 1: que nodos quedan fijos en background
          alcance     - cadena de 0 y 1: nodos futuros que interesan
          mecanismo   - cadena de 0 y 1: nodos presentes que interesan

        Hace:
          1. Arma el subsistema con PyPhi
          2. Pide a PyPhi la particion minima (effect_mip o cause_mip)
          3. Formatea el resultado

        Devuelve: objeto Solution con perdida, particion y tiempo
        """
        self.sia_tiempo_inicio = time.time()
        alcance_idx, mecanismo_idx, subsistema = self.preparar_subsistema(
            condiciones, alcance, mecanismo
        )
        mip = (
            subsistema.effect_mip(mecanismo_idx, alcance_idx)
            if aplicacion.distancia_metrica == MetricDistance.EMD_EFECTO.value
            else subsistema.cause_mip(mecanismo_idx, alcance_idx)
        )
        
        small_phi: float = mip.phi
        repertorio = np.array(DUMMY_ARR, dtype=np.float32)
        repertorio_partido = np.array(DUMMY_ARR, dtype=np.float32)
        format = DUMMY_PARTITION

        if mip.repertoire is not None and mip.partitioned_repertoire is not None:
            repertorio = mip.repertoire.flatten()
            repertorio_partido = mip.partitioned_repertoire.flatten()

            states = int(math.log2(mip.repertoire.size))
            sub_estados: np.ndarray = lil_endian(states)

            repertorio.put(sub_estados, repertorio)
            repertorio_partido.put(sub_estados, repertorio_partido)

            mejor_biparticion: Bipartition = mip.partition
            prim: Part = mejor_biparticion.parts[True]
            dual: Part = mejor_biparticion.parts[False]

            prim_mech, prim_purv = prim.mechanism, prim.purview
            dual_mech, dual_purv = dual.mechanism, dual.purview
            format = fmt_biparticion(
                [dual_mech, dual_purv],
                [prim_mech, prim_purv],
            )

        return Solution(
            estrategia=PYPHI_LABEL,
            perdida=small_phi,
            distribucion_subsistema=repertorio,
            distribucion_particion=repertorio_partido,
            tiempo_total=time.time() - self.sia_tiempo_inicio,
            particion=format,
        )

    def preparar_subsistema(self, condiciones: str, futuros: str, presentes: str):
        """
        Carga la red en PyPhi y filtra nodos segun las cadenas binarias.

        Recibe: condiciones, futuros (alcance), presentes (mecanismo)
        Devuelve: indices de alcance, indices de mecanismo, subsistema PyPhi
        """
        estado_inicial = tuple(int(s) for s in self.sia_gestor.estado_inicial)
        longitud = len(estado_inicial)

        indices = tuple(range(longitud))
        etiquetas = tuple(ABECEDARY[:longitud])

        completo = NodeLabels(etiquetas, indices)
        mpt_estados_nodos_on = self.sia_cargar_tpm()
        red = Network(tpm=mpt_estados_nodos_on, node_labels=completo)
        self.sia_logger.critic("Original creado.")

        candidato = tuple(
            completo[i] for i, bit in enumerate(condiciones) if bit == STR_ONE
        )
        self.sia_logger.critic("Candidato creado.")

        subsistema = Subsystem(network=red, state=estado_inicial, nodes=candidato)
        self.sia_logger.critic("Subsistema creado.")
        alcance = tuple(
            ind
            for ind, (bit, cond) in enumerate(zip(futuros, condiciones))
            if (bit == STR_ONE) and (cond == STR_ONE)
        )
        mecanismo = tuple(
            ind
            for ind, (bit, cond) in enumerate(zip(presentes, condiciones))
            if (bit == STR_ONE) and (cond == STR_ONE)
        )

        return alcance, mecanismo, subsistema
