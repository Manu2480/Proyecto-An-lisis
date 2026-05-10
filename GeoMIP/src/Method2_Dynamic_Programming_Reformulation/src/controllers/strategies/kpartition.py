import time
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist

import sys
from pathlib import Path

# Asegurar que el directorio padre de 'src' esté en el PYTHONPATH
_project_root = Path(__file__).resolve().parents[3]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# pyrefly: ignore [missing-import]
from src.models.base.sia import SIA
# pyrefly: ignore [missing-import]
from src.controllers.manager import Manager
# pyrefly: ignore [missing-import]
from src.controllers.strategies.geometric import GeometricSIA
# pyrefly: ignore [missing-import]
from src.models.core.solution import Solution
# pyrefly: ignore [missing-import]
from src.funcs.base import emd_efecto
# pyrefly: ignore [missing-import]
from src.funcs.format import fmt_parte_q
# pyrefly: ignore [missing-import]
from src.constants.models import GEOMETRIC_LABEL
# pyrefly: ignore [missing-import]
from src.models.core.system import System
# pyrefly: ignore [missing-import]
from src.constants.base import ACTUAL, EFECTO
import functools

class KPartitionSIA(SIA):
    def __init__(self, gestor: Manager, k: int):
        super().__init__(gestor)
        self.k = k
        self.geometric_base = GeometricSIA(gestor)
        # We will initialize these during application
        self._flat_data = []
        self.tabla_transiciones = {}
        
    def aplicar_estrategia(
        self,
        condicion: str,
        alcance: str,
        mecanismo: str,
        tpm: np.ndarray
    ):
        self.sia_preparar_subsistema(condicion, alcance, mecanismo, tpm)
        
        # Validation: check if k-partition is viable
        total_nodos = len(self.sia_subsistema.indices_ncubos) + len(self.sia_subsistema.dims_ncubos)
        if total_nodos < self.k:
            return Solution(
                estrategia=GEOMETRIC_LABEL + f"_k{self.k}",
                perdida=None,
                distribucion_subsistema=self.sia_dists_marginales,
                distribucion_particion=None,
                tiempo_total=time.time() - self.sia_tiempo_inicio,
                particion="Inviable (nodos insuficientes)"
            )
            
        if self.k == 2:
            return self.geometric_base.aplicar_estrategia(condicion, alcance, mecanismo, tpm)

        # Build table T using geometric base
        # This will also populate memoria_particiones in geometric_base
        self.geometric_base.sia_subsistema = self.sia_subsistema
        self.geometric_base.sia_dists_marginales = self.sia_dists_marginales
        self.geometric_base.sia_logger = self.sia_logger
        self.geometric_base.sia_tiempo_inicio = self.sia_tiempo_inicio
        
        self.geometric_base._flat_data = []
        for ncubo in self.sia_subsistema.ncubos:
            self.geometric_base._flat_data.append(ncubo.data.ravel())
        
        dims = self.sia_subsistema.dims_ncubos
        self.geometric_base.estado_inicial = self.sia_subsistema.estado_inicial[dims]
        self.geometric_base.estado_final = 1 - self.geometric_base.estado_inicial
        
        self.geometric_base.vertices = set(
            tuple((ACTUAL, actual) for actual in self.sia_subsistema.dims_ncubos) +
            tuple((EFECTO, efecto) for efecto in self.sia_subsistema.indices_ncubos)
        )
        
        # We run find_mip to get the optimal bipartition and build the cost table simultaneously
        mip = self.geometric_base.find_mip()
        self.tabla_transiciones = self.geometric_base.tabla_transiciones

        # Heuristic 1: Clustering
        particion_clustering = self._heuristica_clustering()
        perdida_clustering = self._evaluar_particion(particion_clustering)

        # Heuristic 2: Greedy Recursive
        particion_greedy = self._heuristica_greedy(mip)
        perdida_greedy = self._evaluar_particion(particion_greedy)

        # Compare and choose best
        if perdida_clustering <= perdida_greedy:
            mejor_particion = particion_clustering
            mejor_perdida = perdida_clustering
            # To track which heuristic won, we can append it to strategy name temporarily
            # For output, we might format the strategy name
            estrategia_usada = "Clustering"
        else:
            mejor_particion = particion_greedy
            mejor_perdida = perdida_greedy
            estrategia_usada = "Greedy"

        fmt_particion = self._fmt_kparticion(mejor_particion)

        return Solution(
            estrategia=f"{GEOMETRIC_LABEL}_k{self.k}_{estrategia_usada}",
            perdida=mejor_perdida,
            distribucion_subsistema=self.sia_dists_marginales,
            distribucion_particion=None, # TBD if needed
            tiempo_total=time.time() - self.sia_tiempo_inicio,
            particion=fmt_particion,
        )

    # _build_cost_table removed as find_mip now handles it

    def _heuristica_clustering(self):
        n_futuros = len(self.sia_subsistema.indices_ncubos)
        n_presentes = len(self.sia_subsistema.dims_ncubos)
        n_total = n_futuros + n_presentes
        if n_total == 0:
            return []

        # Construir matriz de costos C (presentes x futuros)
        # C[i, j] es el impacto del nodo presente i sobre el futuro j
        cost_matrix = np.zeros((n_presentes, n_futuros))
        estado_ini = self.geometric_base.estado_inicial.tolist()
        
        for i in range(n_presentes):
            vecino = estado_ini.copy()
            vecino[i] = 1 - vecino[i]
            key = tuple(estado_ini), tuple(vecino)
            costos = self.tabla_transiciones.get(key)
            if costos:
                cost_matrix[i, :] = [c if c is not None else 0 for c in costos]
        
        # Para clústeres, necesitamos representar ambos tipos de nodos en un espacio común.
        # Usaremos una aproximación de SVD (Singular Value Decomposition) simplificada
        # o simplemente perfiles aumentados que sean comparables.
        
        # Opción robusta: Matriz de adyacencia de grafo bipartito
        # A = [[0, C], [C^T, 0]]
        augmented_matrix = np.zeros((n_total, n_total))
        augmented_matrix[:n_presentes, n_presentes:] = cost_matrix
        augmented_matrix[n_presentes:, :n_presentes] = cost_matrix.T
        
        # El perfil de cada nodo es su fila en la matriz aumentada
        perfiles = augmented_matrix
        
        k_clusters = min(self.k, n_total)
        
        if k_clusters > 1:
            try:
                # Usar distancia euclídea sobre los perfiles aumentados
                dist_matrix = pdist(perfiles, metric='euclidean')
                if np.all(np.isfinite(dist_matrix)):
                    Z = linkage(dist_matrix, method='ward')
                    labels = fcluster(Z, k_clusters, criterion='maxclust')
                else:
                    labels = list(range(1, n_total + 1)) # Fallback a uno por nodo
            except Exception:
                labels = [((i % k_clusters) + 1) for i in range(n_total)]
        else:
            labels = [1] * n_total

        partes_dict = {}
        for i, label in enumerate(labels):
            if label not in partes_dict:
                partes_dict[label] = ([], [])
            
            if i < n_presentes:
                partes_dict[label][0].append(self.sia_subsistema.dims_ncubos[i])
            else:
                partes_dict[label][1].append(self.sia_subsistema.indices_ncubos[i - n_presentes])
            
        return [p for p in partes_dict.values() if p[0] or p[1]]

    def _heuristica_greedy(self, mip):
        parte1 = list(mip)
        parte2 = self.geometric_base.nodes_complement(list(mip))
        partes = [self._decode_part(parte1), self._decode_part(parte2)]
        
        # Eliminar partes vacías si las hay
        partes = [p for p in partes if p[0] or p[1]]
        
        while len(partes) < self.k:
            mejor_split = None
            mejor_idx = -1
            mejor_perdida = float('inf')
            
            for i, p in enumerate(partes):
                presentes, futuros = p
                if len(presentes) + len(futuros) <= 1: 
                    continue
                
                # Probar extraer cada nodo presente
                for p_node in presentes:
                    p1 = ([x for x in presentes if x != p_node], futuros)
                    p2 = ([p_node], [])
                    if not p1[0] and not p1[1]: continue
                    
                    partes_test = partes[:i] + [p1, p2] + partes[i+1:]
                    loss = self._evaluar_particion(partes_test)
                    if loss < mejor_perdida:
                        mejor_perdida = loss
                        mejor_split = (p1, p2)
                        mejor_idx = i
                        
                # Probar extraer cada nodo futuro
                for f_node in futuros:
                    p1 = (presentes, [x for x in futuros if x != f_node])
                    p2 = ([], [f_node])
                    if not p1[0] and not p1[1]: continue
                    
                    partes_test = partes[:i] + [p1, p2] + partes[i+1:]
                    loss = self._evaluar_particion(partes_test)
                    if loss < mejor_perdida:
                        mejor_perdida = loss
                        mejor_split = (p1, p2)
                        mejor_idx = i
                        
            if mejor_split:
                partes.pop(mejor_idx)
                partes.extend(mejor_split)
            else:
                break
                
        return partes

    def _decode_part(self, nodes: list[tuple[int, int]]):
        presentes = [n[1] for n in nodes if n[0] == 0]
        futuros = [n[1] for n in nodes if n[0] == 1]
        return (presentes, futuros)

    def _k_partir(self, partes) -> System:
        new_sys = System.__new__(System)
        new_sys.estado_inicial = self.sia_subsistema.estado_inicial
        
        fut_to_pres = {}
        for presentes, futuros in partes:
            for f in futuros:
                fut_to_pres[f] = presentes
                
        new_ncubos = []
        for cube in self.sia_subsistema.ncubos:
            if cube.indice in fut_to_pres:
                mecanismo = fut_to_pres[cube.indice]
                dims_to_marginalize = np.setdiff1d(cube.dims, mecanismo)
                new_ncubos.append(cube.marginalizar(dims_to_marginalize))
            else:
                new_ncubos.append(cube)
                
        new_sys.ncubos = tuple(new_ncubos)
        return new_sys

    def _reconstruir_tensor(self, distribucion_1d):
        node_dists = [np.array([p, 1 - p]) for p in distribucion_1d]
        if not node_dists: return np.array([])
        return functools.reduce(np.kron, node_dists)

    def _evaluar_particion(self, partes):
        if not partes: return float('inf')
        
        # Marginalizar las partes para encontrar el subsistema particionado
        sis_particionado = self._k_partir(partes)
        
        # 1D marginals array [P(X1=OFF), P(X2=OFF), ...]
        dist_particion = sis_particionado.distribucion_marginal()
        
        # La distribución tensorial conjunta se reconstruiría así:
        # tensor_reconstruido = self._reconstruir_tensor(dist_particion)
        # tensor_original = self._reconstruir_tensor(self.sia_dists_marginales)
        
        # Calcular EMD. Sabemos que EMD causal en hipercubo condicionalmente independiente = emd_efecto en 1D
        perdida = emd_efecto(dist_particion, self.sia_dists_marginales)
        return perdida

    def _fmt_kparticion(self, partes) -> str:
        tops = []
        bottoms = []
        for presentes, futuros in partes:
            parte_q = [(0, p) for p in presentes] + [(1, f) for f in futuros]
            t, b = fmt_parte_q(parte_q, to_sort=True)
            tops.append(t)
            bottoms.append(b)
        
        return "".join(tops) + "\n" + "".join(bottoms)
