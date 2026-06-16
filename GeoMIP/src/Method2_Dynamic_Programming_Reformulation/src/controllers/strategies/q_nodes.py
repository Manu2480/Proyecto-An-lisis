"""
Estrategia QNodes (KQNodes): biparticion exacta con el algoritmo Q del curso.

Va agrupando nodos de a uno, eligiendo en cada paso el que menos empeora la
perdida. Usa memoria (memoria_omega) para no recalcular lo mismo.

Cuando se usa:
  - benchmark con k=2 en n=10, 15, 20
  - run_qnodes_k2.py para n=22, 25
  - Comparar contra GeoMIP

Guia para principiantes:
  documentacion-sustentacion-kqgmip/GUIA_STRATEGIES_PRINCIPIANTES.txt
"""
import time
from typing import Union
import numpy as np
from src.middlewares.slogger import SafeLogger
from src.funcs.base import emd_efecto, ABECEDARY
from src.middlewares.profile import profiler_manager, profile
from src.funcs.format import fmt_biparte_q
from src.controllers.manager import Manager
from src.models.base.sia import SIA

from src.models.core.solution import Solution
from src.constants.models import (
    QNODES_ANALYSIS_TAG,
    QNODES_LABEL,
    QNODES_STRAREGY_TAG,
)
from src.constants.base import (
    TYPE_TAG,
    NET_LABEL,
    INFTY_POS,
    LAST_IDX,
    EFECTO,
    ACTUAL,
)


class QNodes(SIA):
    """
    Encuentra la mejor biparticion (k=2) con el algoritmo Q.

    Recibe un gestor con la red. Guarda resultados en memoria_omega y
    memoria_particiones para no repetir calculos costosos.
    """

    def __init__(self, gestor: Manager):
        """Prepara caches vacias, etiquetas y el registro de tiempos."""
        super().__init__(gestor)
        profiler_manager.start_session(
            f"{NET_LABEL}{len(gestor.estado_inicial)}{gestor.pagina}"
        )
        self.m: int
        self.n: int
        self.tiempos: tuple[np.ndarray, np.ndarray]
        self.etiquetas = [tuple(s.lower() for s in ABECEDARY), ABECEDARY]
        self.vertices: set[tuple]
        self.memoria_omega: dict[frozenset, tuple[float, np.ndarray]] = {}
        self.memoria_particiones = dict()

        self.indices_alcance: np.ndarray
        self.indices_mecanismo: np.ndarray

        self.logger = SafeLogger(QNODES_STRAREGY_TAG)

    @profile(context={TYPE_TAG: QNODES_ANALYSIS_TAG})
    def aplicar_estrategia(
        self,
        condicion: str,
        alcance: str,
        mecanismo: str,
        tpm=None,
    ):
        """
        Punto de entrada: analiza un subsistema y devuelve la mejor biparticion.

        Recibe:
          condicion  - nodos fijos en background
          alcance    - nodos futuros activos
          mecanismo  - nodos presentes activos
          tpm        - matriz de transicion (opcional)

        Hace:
          1. Prepara subsistema y limpia caches del caso
          2. Ejecuta algorithm() con todos los nodos
          3. Formatea la particion ganadora

        Devuelve: Solution con perdida, particion y tiempo
        """
        self.sia_preparar_subsistema(condicion, alcance, mecanismo, tpm if tpm is not None else self.sia_cargar_tpm())

        self.memoria_omega.clear()
        self.memoria_particiones.clear()

        futuro = tuple(
            (EFECTO, efecto) for efecto in self.sia_subsistema.indices_ncubos
        )
        presente = tuple(
            (ACTUAL, actual) for actual in self.sia_subsistema.dims_ncubos
        )  #

        self.m = self.sia_subsistema.indices_ncubos.size
        self.n = self.sia_subsistema.dims_ncubos.size

        self.indices_alcance = self.sia_subsistema.indices_ncubos
        self.indices_mecanismo = self.sia_subsistema.dims_ncubos

        self.tiempos = (
            np.zeros(self.n, dtype=np.int8),
            np.zeros(self.m, dtype=np.int8),
        )

        vertices = list(presente + futuro)
        self.vertices = set(presente + futuro)
        mip = self.algorithm(vertices)

        fmt_mip = fmt_biparte_q(list(mip), self.nodes_complement(mip))

        return Solution(
            estrategia=QNODES_LABEL,
            perdida=self.memoria_particiones[mip][0],
            distribucion_subsistema=self.sia_dists_marginales,
            distribucion_particion=self.memoria_particiones[mip][1],
            tiempo_total=time.time() - self.sia_tiempo_inicio,
            particion=fmt_mip,
        )

    def algorithm(self, vertices: list[tuple[int, int]]):
        """
        Algoritmo Q: va formando grupos eligiendo el nodo que menos empeora la perdida.

        Recibe: lista de nodos (tiempo, indice) del presente y futuro
        Devuelve: clave de la mejor particion en memoria_particiones
        """
        omegas_origen = np.array([vertices[0]])
        deltas_origen = np.array(vertices[1:])

        vertices_fase = vertices

        omegas_ciclo = omegas_origen
        deltas_ciclo = deltas_origen

        total = len(vertices_fase) - 2
        for i in range(len(vertices_fase) - 2):
            self.logger.debug(f"total: {total-i}")
            omegas_ciclo = [vertices_fase[0]]
            deltas_ciclo = vertices_fase[1:]

            emd_particion_candidata = INFTY_POS

            for j in range(len(deltas_ciclo) - 1):
                # self.logger.critic(f"   {j=}")
                emd_local = 1e5
                indice_mip: int

                for k in range(len(deltas_ciclo)):
                    emd_union, emd_delta, dist_marginal_delta = self.funcion_submodular(
                        deltas_ciclo[k], omegas_ciclo
                    )
                    emd_iteracion = emd_union - emd_delta

                    if emd_iteracion < emd_local:
                        emd_local = emd_iteracion
                        indice_mip = k

                    emd_particion_candidata = emd_delta
                    dist_particion_candidata = dist_marginal_delta
                    ...
                # self.logger.critic(f"       [k]: {indice_mip}")

                omegas_ciclo.append(deltas_ciclo[indice_mip])
                deltas_ciclo.pop(indice_mip)
                ...

            self.memoria_particiones[
                tuple(
                    deltas_ciclo[LAST_IDX]
                    if isinstance(deltas_ciclo[LAST_IDX], list)
                    else deltas_ciclo
                )
            ] = emd_particion_candidata, dist_particion_candidata

            par_candidato = (
                [omegas_ciclo[LAST_IDX]]
                if isinstance(omegas_ciclo[LAST_IDX], tuple)
                else omegas_ciclo[LAST_IDX]
            ) + (
                deltas_ciclo[LAST_IDX]
                if isinstance(deltas_ciclo[LAST_IDX], list)
                else deltas_ciclo
            )

            omegas_ciclo.pop()
            omegas_ciclo.append(par_candidato)

            vertices_fase = omegas_ciclo
            ...

        return min(
            self.memoria_particiones, key=lambda k: self.memoria_particiones[k][0]
        )

    def _nodos_de_delta(
        self, deltas: Union[tuple, list[tuple]]
    ) -> frozenset[tuple[int, int]]:
        """Convierte un delta (un nodo o lista) en un frozenset para usar como clave de cache."""
        if isinstance(deltas, tuple):
            return frozenset((deltas,))
        return frozenset(deltas)

    def _nodos_de_omega(
        self, omegas: list[Union[tuple, list[tuple]]]
    ) -> frozenset[tuple[int, int]]:
        """Junta todos los nodos del grupo omega en un frozenset para la cache."""
        nodos: set[tuple[int, int]] = set()
        for omega in omegas:
            if isinstance(omega, list):
                nodos.update(omega)
            else:
                nodos.add(omega)
        return frozenset(nodos)

    def _emd_para_conjunto(
        self, nodos: frozenset[tuple[int, int]]
    ) -> tuple[float, np.ndarray]:
        """
        Calcula la perdida EMD de activar exactamente estos nodos.

        Si ya se calculo antes, devuelve el valor guardado en memoria_omega.
        Si no, biparte el subsistema, calcula EMD y guarda el resultado.

        Recibe: conjunto de nodos (tiempo, indice)
        Devuelve: (perdida_emd, vector_marginales)
        """
        cached = self.memoria_omega.get(nodos)
        if cached is not None:
            emd, marg = cached
            return emd, marg

        temporal: list[list[int]] = [[], []]
        for t, idx in nodos:
            temporal[t].append(idx)

        particion = self.sia_subsistema.bipartir(
            np.array(temporal[EFECTO], dtype=np.int8),
            np.array(temporal[ACTUAL], dtype=np.int8),
        )
        marginales = particion.distribucion_marginal()
        emd = emd_efecto(marginales, self.sia_dists_marginales)
        self.memoria_omega[nodos] = (emd, marginales)
        return emd, marginales

    def funcion_submodular(
        self, deltas: Union[tuple, list[tuple]], omegas: list[Union[tuple, list[tuple]]]
    ):
        """
        Evalua que pasa si unimos delta con omega.

        Recibe:
          deltas - un nodo candidato o grupo de nodos
          omegas - nodos ya agrupados

        Devuelve:
          (emd de la union, emd del delta solo, marginales del delta)
        """
        nodos_delta = self._nodos_de_delta(deltas)
        emd_delta, vector_delta_marginal = self._emd_para_conjunto(nodos_delta)

        nodos_union = nodos_delta | self._nodos_de_omega(omegas)
        emd_union, _ = self._emd_para_conjunto(nodos_union)

        return emd_union, emd_delta, vector_delta_marginal

    def nodes_complement(self, nodes: list[tuple[int, int]]):
        """Devuelve los nodos que no estan en la lista dada."""
        return list(set(self.vertices) - set(nodes))


# Alias del enunciado (KQNodes = heurística Q, k=2).
KQNodes = QNodes
