"""
Estrategia GeometricSIA (KGeoMIP): biparticion EXACTA con el metodo geometrico.

Construye una tabla de costos entre estados del mecanismo y elige la biparticion
con menor perdida EMD. Es la referencia exacta para k=2 en el benchmark.

Cuando se usa:
  - benchmark exacto columna Geo_k2
  - KPartitionSIA cuando k=2 sin otra heuristica forzada
  - Como base para armar la tabla de costos en k=3,4,5

Guia para principiantes:
  documentacion-sustentacion-kqgmip/GUIA_STRATEGIES_PRINCIPIANTES.txt
"""
import copy
import heapq
import os
from src.constants.error import ERROR_INCOMPATIBLE_SIZES
from src.models.core.system import System
from src.constants.base import NET_LABEL, STR_ZERO
from src.funcs.base import ABECEDARY
from src.middlewares.slogger import SafeLogger
from src.funcs.base import emd_efecto
from src.models.base.sia import SIA
from src.constants.base import (
    ACTUAL,
    EFECTO,
    TYPE_TAG,
)
from src.constants.models import (
    GEOMETRIC_ANALYSIS_TAG,
    GEOMETRIC_LABEL,
    GEOMETRIC_STRAREGY_TAG,
)
from src.controllers.manager import Manager
from src.funcs.format import fmt_biparte_q
from src.middlewares.profile import profiler_manager, profile
from src.models.core.solution import Solution
import numpy as np
import time
from typing import List, Dict, Tuple

from concurrent.futures import ThreadPoolExecutor
import itertools


# Memoiza find_mip (tabla_transiciones + memoria_particiones) por subsistema TPM.
_FIND_MIP_CACHE: dict[tuple, dict] = {}


def limpiar_cache_find_mip() -> None:
    """
    Vacia la memoria guardada de find_mip.

    Se llama entre casos del benchmark para no llenar la RAM.
    """
    _FIND_MIP_CACHE.clear()


class GeometricSIA(SIA):
    """
    Encuentra la mejor biparticion (k=2) con el metodo geometrico del curso.

    Recibe un gestor con la red. Guarda tablas de costos y particiones evaluadas.
    """

    def __init__(self, gestor: Manager):
        """Prepara etiquetas, tablas vacias y el registro de tiempos."""
        super().__init__(gestor)
        profiler_manager.start_session(
            f"{NET_LABEL}{len(gestor.estado_inicial)}{gestor.pagina}"
        )
        self.etiquetas = [tuple(s.lower() for s in ABECEDARY), ABECEDARY]
        self.logger = SafeLogger(GEOMETRIC_STRAREGY_TAG)
        self.tabla_transiciones: dict ={}
        self.vertices :set[tuple]
        self.tabla :dict[int, list[tuple[int, int]]] = {}
        self.memoria_particiones: dict[tuple[int, int], tuple[float, float]] = {}

    @profile(context={TYPE_TAG: GEOMETRIC_ANALYSIS_TAG})
    def aplicar_estrategia(
        self,
        condicion: str,
        alcance: str,
        mecanismo: str,
        tpm: np.ndarray #! COMENTAR PARA UN SOLO ESTADO INICIAL
    ):
        """
        Punto de entrada: analiza un subsistema y devuelve la mejor biparticion.

        Recibe:
          condicion  - nodos fijos en background
          alcance    - nodos futuros activos
          mecanismo  - nodos presentes activos
          tpm        - matriz de probabilidad de transicion

        Hace:
          1. Prepara el subsistema
          2. Llena la tabla de costos (find_mip)
          3. Formatea la particion ganadora

        Devuelve: Solution con perdida, particion, tiempo y k=2
        """
        self.sia_preparar_subsistema(condicion, alcance, mecanismo, tpm) #! COMENTAR PARA UN SOLO ESTADO INICIAL
        # self.sia_preparar_subsistema(condicion, alcance, mecanismo) #! DESCOMENTAR PARA UN SOLO ESTADO INICIAL

        futuro = tuple(
            (EFECTO, efecto) for efecto in self.sia_subsistema.indices_ncubos
        )
        presente = tuple(
            (ACTUAL, actual) for actual in self.sia_subsistema.dims_ncubos
        )


        self._flat_data = []
        for idx, ncubo in enumerate(self.sia_subsistema.ncubos):
            # garantías: ncubo.data.shape == (2,2,...,2)
            # np.ravel() lo aplana. El orden ‘C’ equivale 
            # a little-endian si tus tuples están invertidas.
            self._flat_data.append(ncubo.data.ravel())

        self.vertices = set(presente + futuro)
        dims = self.sia_subsistema.dims_ncubos
        self.estado_inicial = self.sia_subsistema.estado_inicial[dims]
        self.estado_final = 1 - self.estado_inicial
        mip = self.find_mip()
        # print(mip)
        fmt_mip = fmt_biparte_q(list(mip), self.nodes_complement(mip))

        return Solution(
            estrategia= GEOMETRIC_LABEL,
            perdida=self.memoria_particiones[mip][0],
            distribucion_subsistema=self.sia_dists_marginales,
            distribucion_particion=self.memoria_particiones[mip][1],
            tiempo_total=time.time() - self.sia_tiempo_inicio,
            particion=fmt_mip,
            n_nodos=len(self.sia_gestor.estado_inicial),
            k=2,
        )
    
    def nodes_complement(self, nodes: list[tuple[int, int]]):
        """
        Devuelve los nodos que NO estan en la lista dada.

        Recibe: lista de nodos (tiempo, indice)
        Devuelve: lista con el complemento respecto a todos los vertices
        """
        return list(set(self.vertices) - set(nodes))
    
    def find_mip(self):
        """
        Corazon del metodo geometrico: busca la biparticion con menor perdida.

        Pasos:
          1. Si ya calculamos este caso, reutiliza la memoria guardada
          2. Llena tabla_transiciones nivel por nivel
          3. Arma candidatos con identificar_particiones_optimas
          4. Evalua cada candidato con bipartir y emd_efecto
          5. Guarda el de menor perdida

        Devuelve: lista de nodos de la mejor biparticion
        """
        ck = getattr(self, "_prep_cache_key", None)
        if ck and ck in _FIND_MIP_CACHE:
            snap = _FIND_MIP_CACHE[ck]
            self.tabla_transiciones = copy.deepcopy(snap["tabla_transiciones"])
            self.memoria_particiones = copy.deepcopy(snap["memoria_particiones"])
            self.caminos = copy.deepcopy(snap["caminos"])
            self.idx_ncubos = list(range(len(self.sia_subsistema.indices_ncubos)))
            return snap["best_mip"]

        quiet = os.environ.get("KQGMIP_QUIET", "").lower() in ("1", "true", "yes")
        if not quiet:
            self.sia_logger.critic("empieza.")
        self.tabla_transiciones.clear()
        self.memoria_particiones.clear()
        estado_inicial = self.estado_inicial
        estado_final = self.estado_final
        self.idx_ncubos = list(range(len(self.sia_subsistema.indices_ncubos)))
        self.caminos = {0: [estado_inicial.tolist()]}
        self.tabla_transiciones[
            tuple(self.caminos[0][0]), tuple(self.caminos[0][0])
        ] = [0.0 for _ in range(len(self.sia_subsistema.indices_ncubos))]
        for nivel in range(1, len(estado_inicial) + 1):
            self.calcular_costos_nivel(estado_final, nivel)
        candidatos = self.identificar_particiones_optimas()
        for idx, (presentes, futuros) in enumerate(candidatos):
            presentes = self.sia_subsistema.dims_ncubos[presentes]
            futuros = self.sia_subsistema.indices_ncubos[futuros]
            dist = self.sia_subsistema.bipartir(futuros, presentes).distribucion_marginal()
            emd = emd_efecto(dist, self.sia_dists_marginales)
            key = [(0, nodo) for nodo in presentes]
            key.extend([(1, nodo) for nodo in futuros])
            self.memoria_particiones[tuple(key)] = (emd, dist)
        best = min(self.memoria_particiones, key=lambda k: self.memoria_particiones[k][0])

        if ck is not None:
            _FIND_MIP_CACHE[ck] = {
                "tabla_transiciones": copy.deepcopy(self.tabla_transiciones),
                "memoria_particiones": copy.deepcopy(self.memoria_particiones),
                "caminos": copy.deepcopy(self.caminos),
                "best_mip": best,
            }
        return best
    
    def calcular_costos_nivel(self,estado_final: np.ndarray, nivel):
        """
        Explora estados vecinos a distancia hamming dada y calcula costos.

        Recibe: estado final objetivo y numero de nivel (cuantos bits cambian)
        Llena: self.caminos y llama calcular_costo para cada vecino nuevo
        """
        n = len(estado_final)      
        visitados:set[tuple] = set()
        self.caminos[nivel] = []
        for estado_anterior in self.caminos[nivel - 1]:
            estado_actual = np.array(estado_anterior)
            for i in range(n):
                if estado_actual[i] != estado_final[i]:
                    nuevo_estado = estado_actual.copy()
                    nuevo_estado[i] = estado_final[i]
                    nuevo_estado_tuple = tuple(nuevo_estado)
                    if nuevo_estado_tuple not in visitados:
                        self.caminos[nivel].append(nuevo_estado.tolist())
                        self.calcular_costo(self.caminos[0][0],nuevo_estado.tolist(),self.idx_ncubos)
                        visitados.add(nuevo_estado_tuple)

    def calcular_costo(self, estado_inicial:tuple, estado_final:tuple, ncubos:list[int]):
        """
        Calcula el costo de ir de un estado a otro en las variables futuras.

        Recibe:
          estado_inicial, estado_final - tuplas de 0 y 1
          ncubos - indices de variables futuras a considerar

        Usa distancia hamming y factor 1/2^distancia. Guarda en tabla_transiciones.
        """
        key = tuple(estado_inicial), tuple(estado_final)
        if key not in self.tabla_transiciones:
            self.tabla_transiciones[key] = [None]*len(self.sia_subsistema.indices_ncubos)
        distancia_hamming = self.hamming(estado_inicial, estado_final)
        factor = 1/(2**distancia_hamming)
        # index_inicial = tuple(np.array(estado_inicial)[::-1])
        # index_final = tuple(np.array(estado_final)[::-1])


        estado_ini_int = int("".join(map(str, estado_inicial[::-1])), 2)
        estado_fin_int = int("".join(map(str, estado_final[::-1])), 2)

        # Con eso, cada flat_data[idx][...] ya te da directamente X[i] o X[j].
        diffs = np.abs(
            np.array([flat[estado_ini_int] for flat in self._flat_data])
        - np.array([flat[estado_fin_int] for flat in self._flat_data])
        )
        self.tabla_transiciones[key] = diffs.tolist()
        # for idx in ncubos:
        #     self.tabla_transiciones[key][idx] = (abs(self.sia_subsistema.ncubos[idx].data[index_inicial]-self.sia_subsistema.ncubos[idx].data[index_final]))
        
        if distancia_hamming > 1:
            for i in range(len(estado_inicial)):
                if estado_inicial[i] != estado_final[i]:
                    nuevo_estado = estado_final.copy()
                    nuevo_estado[i] = estado_inicial[i]
                    nuevo_estado_tuple = tuple(nuevo_estado)
                    temp_key = tuple(estado_inicial), nuevo_estado_tuple
                    for n in ncubos:
                        self.tabla_transiciones[key][n] = self.tabla_transiciones[key][n] + self.tabla_transiciones[temp_key][n]
        tmp =[]
        for i,n in enumerate(self.tabla_transiciones[key]):
            if n is not None:
                tmp.append(factor * n)
            else:
                tmp.append(n)
        self.tabla_transiciones[key] = tmp

    def identificar_particiones_optimas(self):
        """
        Lee la tabla de costos y arma candidatos a biparticion.

        Cada candidato es una pareja (presentes, futuros) con indices de nodos.
        Devuelve: lista de candidatos para evaluar con EMD
        """
        # idx_nivel_cero = 0
        # idx_nivel_cero_2 = 1
        # costo=1e5
        key = tuple(self.caminos[0][0]), tuple(self.estado_final)
        costos: list = self.tabla_transiciones[key]
        # print(f"costos nivel cero {costos}")
        # for idx, valor in enumerate(costos):
        #     if valor < costo:
        #         costo = valor
        #         idx_nivel_cero = idx
        # presentes_nivel_cero = [i for i in range(len(self.estado_final))]
        # furutros_nivel_cero = [i for i in range(len(self.sia_subsistema.indices_ncubos)) if i != idx_nivel_cero]
        # candidatos = [[presentes_nivel_cero, furutros_nivel_cero]]
        # pares = [(valor, idx) for idx, valor in enumerate(costos)]
        # menores = heapq.nsmallest(len(self.estado_inicial), pares, key=lambda x: x[0])
        candidatos = []
        n_vars = len(costos)
        for idx in range(n_vars):
            presentes = [i for i in range(len(self.estado_final))]
            futuros = [i for i in range(n_vars) if i != idx]
            candidatos.append([presentes, futuros])
        # _, idx_nivel_cero_1 = dos_menores[0]
        # _, idx_nivel_cero_2 = dos_menores[1]
        # print(idx_nivel_cero_1, idx_nivel_cero_2)
        # presentes_1 = [i for i in range(n_vars)]
        # futuros_1  = [i for i in range(n_vars) if i != idx_nivel_cero_1]
        # presentes_2 = [i for i in range(n_vars)]
        # futuros_2  = [i for i in range(n_vars) if i != idx_nivel_cero_2]
        # candidatos = [
        #     [presentes_1, futuros_1],
        #     [presentes_2, futuros_2]
        # ]
        # print(f"candidatos nivel cero {candidatos}")
        es_par = len(self.caminos) % 2 == 0
        if es_par:
            mitad = len(self.caminos) // 2
        else:
            mitad = (len(self.caminos) // 2) + 1
        for nivel in range(1,mitad):
            # candidato_nivel = self.caminos[nivel][0]
            costo_candidato_nivel = 1e5
            presentes_nivel = []
            futuros_nivel = []
            for estado in self.caminos[nivel]:
                # candidato = estado
                costo_candidato = 0
                presentes = []
                futuros = []
                actual = self.tabla_transiciones.get((tuple(self.caminos[0][0]), tuple(estado)), None)
                estado_complementario = (1-np.array(estado)).tolist()
                complementario = self.tabla_transiciones.get((tuple(self.caminos[0][0]), tuple(estado_complementario)), None)
                for idx,i in enumerate(estado):
                    if i == self.caminos[0][0][idx]:
                        presentes.append(idx)
                for idx,_ in enumerate(self.idx_ncubos):
                    if actual[idx] <= complementario[idx]:
                        futuros.append(idx)
                        costo_candidato += actual[idx]
                    else:
                        costo_candidato += complementario[idx]
                if costo_candidato < costo_candidato_nivel:
                    # candidato_nivel = candidato
                    costo_candidato_nivel = costo_candidato
                    presentes_nivel = presentes
                    futuros_nivel = futuros
            candidatos.append([presentes_nivel, futuros_nivel])
        return candidatos

    def hamming(self,a: List[int], b: List[int]) -> int:
        """Cuenta cuantos bits son distintos entre dos estados. Devuelve un entero."""
        return sum(x != y for x, y in zip(a, b))


# Alias del enunciado (KGeoMIP = bipartición geométrica, k=2).
KGeoMIP = GeometricSIA