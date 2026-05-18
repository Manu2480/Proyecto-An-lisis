import time
import math
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
    def __init__(self, gestor: Manager, k: int, forzar_heuristica: str = None):
        """
        Args:
            forzar_heuristica: None=mejor de ambas, 'greedy'=QNodes-style,
                               'clustering'=Geometric-style
        """
        super().__init__(gestor)
        self.k = k
        self.forzar_heuristica = forzar_heuristica
        self.geometric_base = GeometricSIA(gestor)
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
                particion="Inviable (nodos insuficientes)",
                n_nodos=len(self.sia_gestor.estado_inicial),
                k=self.k,
            )

        # ── MCTS: bypass find_mip completamente ──────────────────────────────
        # Activa cuando se fuerza explícitamente O cuando el mecanismo tiene
        # muchos nodos (>14) y el BFS exacto sería exponencialmente costoso.
        n_mec = len(self.sia_subsistema.dims_ncubos)
        usar_mcts = (self.forzar_heuristica == "mcts") or (n_mec > 15)

        if usar_mcts:
            mejor_particion = self._heuristica_mcts(self.k)
            mejor_perdida   = self._evaluar_particion(mejor_particion)
            fmt_particion   = self._fmt_kparticion(mejor_particion)
            return Solution(
                estrategia=f"{GEOMETRIC_LABEL}_k{self.k}_MCTS",
                perdida=mejor_perdida,
                distribucion_subsistema=self.sia_dists_marginales,
                distribucion_particion=None,
                tiempo_total=time.time() - self.sia_tiempo_inicio,
                particion=fmt_particion,
                n_nodos=len(self.sia_gestor.estado_inicial),
                k=self.k,
            )
        # ─────────────────────────────────────────────────────────────────────

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

        candidatos = {}

        if self.forzar_heuristica in (None, "greedy"):
            p = self._heuristica_greedy(mip)
            candidatos["Greedy"] = (p, self._evaluar_particion(p))

        if self.forzar_heuristica in (None, "kl"):
            p = self._heuristica_kernighan_lin(mip)
            candidatos["KL"] = (p, self._evaluar_particion(p))

        if self.forzar_heuristica in (None, "clustering"):
            p = self._heuristica_clustering()
            candidatos["Clustering"] = (p, self._evaluar_particion(p))

        if self.forzar_heuristica in (None, "spectral"):
            p = self._heuristica_espectral_emd()
            candidatos["Spectral"] = (p, self._evaluar_particion(p))

        # Si se forzó una heurística específica, solo hay un candidato
        if self.forzar_heuristica in ("greedy", "kl", "clustering", "spectral"):
            estrategia_usada = list(candidatos.keys())[0]
            mejor_particion, mejor_perdida = list(candidatos.values())[0]
        else:
            # Sin restricción: elegir la de menor pérdida
            estrategia_usada = min(candidatos, key=lambda k: candidatos[k][1])
            mejor_particion, mejor_perdida = candidatos[estrategia_usada]

        fmt_particion = self._fmt_kparticion(mejor_particion)

        return Solution(
            estrategia=f"{GEOMETRIC_LABEL}_k{self.k}_{estrategia_usada}",
            perdida=mejor_perdida,
            distribucion_subsistema=self.sia_dists_marginales,
            distribucion_particion=None,
            tiempo_total=time.time() - self.sia_tiempo_inicio,
            particion=fmt_particion,
            n_nodos=len(self.sia_gestor.estado_inicial),
            k=self.k,
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

    # ── Heurística 3: Kernighan-Lin ──────────────────────────────────────────
    def _heuristica_kernighan_lin(self, mip, max_iter: int = 20):
        """
        Kernighan-Lin inspirado para k-particiones.

        Fase 1 (extensión): usa el Greedy actual para llegar a k partes.
        Fase 2 (refinamiento KL): aplica pasadas de movimientos de un nodo
            entre partes existentes hasta que ningún movimiento mejore la EMD.

        La diferencia clave respecto al Greedy es que KL MUEVE nodos entre
        partes ya existentes (no solo extrae unilateralmente), escapando
        mínimos locales donde un intercambio bilateral sería beneficioso.

        Complejidad: O(max_iter · k² · n · 2^n)
        """
        # Fase 1: partir de la bipartición MIP y extender a k con Greedy
        partes = self._heuristica_greedy(mip)

        # Fase 2: refinamiento por movimientos de nodo entre pares de partes
        for _ in range(max_iter):
            improved = False
            perdida_actual = self._evaluar_particion(partes)

            for i in range(len(partes)):
                pi_pres, pi_fut = partes[i]
                nodos_i = [('p', v) for v in pi_pres] + [('f', v) for v in pi_fut]

                for j in range(len(partes)):
                    if i == j:
                        continue
                    pj_pres, pj_fut = partes[j]

                    for tipo, nodo in nodos_i:
                        # Construir partes candidatas al mover 'nodo' de i a j
                        if tipo == 'p':
                            new_pi = ([x for x in pi_pres if x != nodo], pi_fut)
                            new_pj = (pj_pres + [nodo], pj_fut)
                        else:
                            new_pi = (pi_pres, [x for x in pi_fut if x != nodo])
                            new_pj = (pj_pres, pj_fut + [nodo])

                        # No dejar partes vacías
                        if not new_pi[0] and not new_pi[1]:
                            continue

                        partes_test = (partes[:i] + [new_pi] +
                                       partes[i+1:j] + [new_pj] +
                                       partes[j+1:])
                        nueva_perdida = self._evaluar_particion(partes_test)

                        if nueva_perdida < perdida_actual - 1e-10:
                            perdida_actual = nueva_perdida
                            partes = partes_test
                            # Actualizar refs locales para la iteración actual
                            pi_pres, pi_fut = new_pi
                            nodos_i = ([('p', v) for v in pi_pres] +
                                       [('f', v) for v in pi_fut])
                            improved = True
                            break
                    if improved:
                        break
                if improved:
                    break

            if not improved:
                break

        return partes

    # ── Heurística 4: Espectral con pesos EMD ────────────────────────────────
    def _heuristica_espectral_emd(self):
        """
        Particionamiento espectral con afinidad basada en la cost_matrix EMD.

        CORRECCIÓN respecto a la versión Ward:
        - Ward usaba distancia euclidiana entre perfiles escalares → ignora EMD.
        - Esta versión construye la afinidad directamente desde C[i,j]:
            * C[i,j] = costo de separar el nodo presente i del nodo futuro j
              (extraído de tabla_transiciones[(s0, vecino_i)][j]).
            * Un C[i,j] alto → i y j deben ir juntos (separarlos es costoso).
          La afinidad entre pares de nodos es:
            * W[pres_i, fut_j]   = C[i,j]                (costo directo)
            * W[pres_i, pres_i'] = cosine(C[i,:], C[i',:]) (mismos futuros)
            * W[fut_j,  fut_j']  = cosine(C[:,j], C[:,j']) (mismos presentes)
        - Luego aplica corte espectral normalizado y k-means.

        Complejidad: O(n·2^n) para find_mip + O(n³) para eigendecomposición
        """
        n_futuros   = len(self.sia_subsistema.indices_ncubos)
        n_presentes = len(self.sia_subsistema.dims_ncubos)
        n_total     = n_futuros + n_presentes

        if n_total == 0:
            return []

        k_clusters = min(self.k, n_total)

        # ── 1. Cost-matrix C[n_presentes × n_futuros] desde tabla_transiciones ─
        estado_ini = self.geometric_base.estado_inicial.tolist()
        C = np.zeros((n_presentes, n_futuros))

        for i in range(n_presentes):
            vecino = estado_ini.copy()
            vecino[i] = 1 - vecino[i]
            key = (tuple(estado_ini), tuple(vecino))
            raw = self.tabla_transiciones.get(key)
            if raw:
                C[i, :] = [float(v) if v is not None else 0.0 for v in raw]

        # ── 2. Matriz de afinidad W[n_total × n_total] ───────────────────────
        # Nodos: [pres_0, …, pres_{p-1}, fut_0, …, fut_{m-1}]
        W = np.zeros((n_total, n_total))

        # Bloque pres×fut: afinidad directa = C[i,j]
        W[:n_presentes, n_presentes:] = C
        W[n_presentes:, :n_presentes] = C.T

        # Bloque pres×pres: similitud coseno entre filas de C
        for i in range(n_presentes):
            for ip in range(i + 1, n_presentes):
                n1 = np.linalg.norm(C[i]) + 1e-10
                n2 = np.linalg.norm(C[ip]) + 1e-10
                sim = float(C[i] @ C[ip]) / (n1 * n2)
                sim = max(0.0, sim)          # descartar similitudes negativas
                W[i, ip] = W[ip, i] = sim

        # Bloque fut×fut: similitud coseno entre columnas de C
        for j in range(n_futuros):
            for jp in range(j + 1, n_futuros):
                n1 = np.linalg.norm(C[:, j])  + 1e-10
                n2 = np.linalg.norm(C[:, jp]) + 1e-10
                sim = float(C[:, j] @ C[:, jp]) / (n1 * n2)
                sim = max(0.0, sim)
                W[n_presentes + j, n_presentes + jp] = sim
                W[n_presentes + jp, n_presentes + j] = sim

        # ── 3. Laplaciano normalizado (Ng-Jordan-Weiss) ───────────────────────
        deg = W.sum(axis=1)
        D_inv_sqrt = np.diag(1.0 / (np.sqrt(deg) + 1e-10))
        L_sym = np.eye(n_total) - D_inv_sqrt @ W @ D_inv_sqrt

        # ── 4. Primeros k_clusters vectores propios (menor eigenvalor) ────────
        try:
            from scipy.linalg import eigh
            _, eigenvectors = eigh(L_sym, subset_by_index=[0, k_clusters - 1])
            U = eigenvectors                 # shape (n_total, k_clusters)
            # Normalizar filas a norma unitaria
            norms = np.linalg.norm(U, axis=1, keepdims=True)
            U = U / (norms + 1e-10)
        except Exception:
            labels = [(i % k_clusters) for i in range(n_total)]
            return self._labels_to_partes(labels, n_presentes, k_clusters)

        # ── 5. K-means en espacio espectral ──────────────────────────────────
        labels = self._kmeans_simple(U, k_clusters)
        return self._labels_to_partes(labels, n_presentes, k_clusters)

    def _kmeans_simple(self, X: np.ndarray, k: int, max_iter: int = 100) -> list:
        """K-means sin sklearn. Inicialización k-means++."""
        n = len(X)
        if k >= n:
            return list(range(n))

        rng = np.random.default_rng(42)
        # Inicialización k-means++
        centers_idx = [rng.integers(n)]
        for _ in range(1, k):
            dists = np.min(
                [np.sum((X - X[c]) ** 2, axis=1) for c in centers_idx], axis=0
            )
            probs = dists / (dists.sum() + 1e-10)
            centers_idx.append(int(rng.choice(n, p=probs)))
        centers = X[centers_idx].copy()

        labels = np.zeros(n, dtype=int)
        for _ in range(max_iter):
            # Asignación
            dists_matrix = np.stack(
                [np.sum((X - c) ** 2, axis=1) for c in centers]
            )
            new_labels = np.argmin(dists_matrix, axis=0)
            if np.all(new_labels == labels):
                break
            labels = new_labels
            # Actualizar centroides
            for j in range(k):
                mask = labels == j
                if mask.any():
                    centers[j] = X[mask].mean(axis=0)
        return labels.tolist()

    def _labels_to_partes(self, labels: list, n_presentes: int,
                           k_clusters: int) -> list:
        """Convierte etiquetas de clustering a lista de (presentes, futuros)."""
        partes_dict: dict[int, tuple[list, list]] = {}
        for i, lbl in enumerate(labels):
            lbl = int(lbl)
            if lbl not in partes_dict:
                partes_dict[lbl] = ([], [])
            if i < n_presentes:
                partes_dict[lbl][0].append(
                    int(self.sia_subsistema.dims_ncubos[i])
                )
            else:
                partes_dict[lbl][1].append(
                    int(self.sia_subsistema.indices_ncubos[i - n_presentes])
                )
        return [p for p in partes_dict.values() if p[0] or p[1]]

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

    # ══════════════════════════════════════════════════════════════════════════
    # HEURÍSTICA 5: MCTS + MC-EMD  (para n≥20)
    # ══════════════════════════════════════════════════════════════════════════

    def _mc_emd(self, partes: list, n_samples: int, rng: np.random.Generator) -> float:
        """
        Capa 1 — Estimador Monte Carlo del EMD.

        Reemplaza la evaluación exacta de EMD (que requiere O(2^n_mec) ops)
        por una estimación sobre S estados muestreados aleatoriamente del
        espacio {0,1}^n_mec. El estimador es insesgado con error O(1/√S).

        Solo se usa cuando n_samples > 0; de lo contrario se delega a
        _evaluar_particion (exacto).

        Args:
            partes:    lista de (presentes, futuros) que define la partición
            n_samples: número de estados a muestrear (S)
            rng:       generador de números aleatorios
        Returns:
            Estimación del EMD (float)
        """
        if not partes:
            return float('inf')

        dims    = self.sia_subsistema.dims_ncubos
        s0_full = self.sia_subsistema.estado_inicial
        n_mec   = len(dims)

        # Muestreo mixto: 70% uniforme + 30% vecinos Hamming de s0
        # (los vecinos Hamming son más informativos para el cálculo de EMD)
        n_uniform = int(0.7 * n_samples)
        n_hamming = n_samples - n_uniform

        s0 = s0_full[dims]
        samples_u = rng.integers(0, 2, size=(n_uniform, n_mec), dtype=np.int8)
        samples_h = np.tile(s0, (n_hamming, 1)).astype(np.int8)
        flip_pos  = rng.integers(0, n_mec, size=n_hamming)
        samples_h[np.arange(n_hamming), flip_pos] ^= 1
        samples   = np.vstack([samples_u, samples_h])

        # Construir el sistema particionado (una sola vez)
        sis_part = self._k_partir(partes)

        total_diff = 0.0
        for state in samples:
            # Reconstruir el estado completo (para indexar NCubes con dims globales)
            s_full      = s0_full.copy().astype(np.int8)
            s_full[dims] = state

            diff = 0.0
            for nc_sys, nc_part in zip(self.sia_subsistema.ncubos, sis_part.ncubos):
                # P(node = OFF | estado) para el sistema original y la partición
                if nc_sys.dims.size > 0:
                    idx_sys  = tuple(int(s_full[j]) for j in nc_sys.dims)
                    p_sys    = 1.0 - float(nc_sys.data[idx_sys])
                else:
                    p_sys    = 1.0 - float(nc_sys.data)

                if nc_part.dims.size > 0:
                    idx_part = tuple(int(s_full[j]) for j in nc_part.dims
                                     if j < len(s_full))
                    p_part   = 1.0 - float(nc_part.data[idx_part])
                else:
                    p_part   = 1.0 - float(nc_part.data)

                diff += abs(p_sys - p_part)
            total_diff += diff

        return total_diff / n_samples

    def _heuristica_mcts(
        self,
        k: int,
        n_iter: int      = 300,
        c_ucb: float     = 1.414,
        n_samples_emd: int = 0,
        rollout_depth: int = 6,
        seed: int        = 42,
    ) -> list:
        """
        Capa 2 — Monte Carlo Tree Search para k-particiones.

        Estructura del árbol MCTS:
          Nodo   = k-partición (codificada como array de etiquetas enteras)
          Acción = mover un nodo de su parte actual a otra parte
          Valor  = −EMD (MCTS maximiza; nosotros minimizamos EMD)

        Por cada iteración:
          1. Selección:   elige la acción con mayor UCB desde el estado actual
          2. Expansión:   aplica la acción seleccionada → nuevo estado
          3. Rollout:     simulación aleatoria con mejora oportunista (depth pasos)
          4. Backprop:    actualiza visits y values en el árbol

        Capa MC-EMD (opcional): si n_samples_emd > 0, los rollouts usan
        _mc_emd() en vez de _evaluar_particion(), haciendo cada evaluación
        ~(2^n_mec / S) veces más rápida con error controlado O(1/√S).

        Args:
            k:             número de partes deseadas
            n_iter:        iteraciones MCTS (≥100 para resultados estables)
            c_ucb:         constante de exploración UCB1 (√2 ≈ 1.414)
            n_samples_emd: muestras MC-EMD; 0 = evaluación exacta
            rollout_depth: pasos aleatorios por rollout
            seed:          semilla para reproducibilidad
        Returns:
            Lista de (presentes, futuros) — la mejor k-partición encontrada
        """
        rng = np.random.default_rng(seed)

        nodos_pres = list(self.sia_subsistema.dims_ncubos)
        nodos_fut  = list(self.sia_subsistema.indices_ncubos)
        n_pres     = len(nodos_pres)
        n_fut      = len(nodos_fut)
        n_total    = n_pres + n_fut

        if n_total == 0 or k > n_total:
            return []

        # ── Representación interna ──────────────────────────────────────────
        # labels: array int8 de tamaño n_total, cada elemento ∈ [0, k-1]
        # índices 0..n_pres-1 → nodos presentes
        # índices n_pres..n_total-1 → nodos futuros

        def labels_to_partes(labels: np.ndarray) -> list:
            partes = [([], []) for _ in range(k)]
            for i, lbl in enumerate(labels):
                lbl = int(lbl) % k
                if i < n_pres:
                    partes[lbl][0].append(nodos_pres[i])
                else:
                    partes[lbl][1].append(nodos_fut[i - n_pres])
            return [(p, f) for p, f in partes if p or f]

        def evaluate_exact(labels: np.ndarray) -> float:
            return self._evaluar_particion(labels_to_partes(labels))

        def evaluate_mc(labels: np.ndarray) -> float:
            return self._mc_emd(labels_to_partes(labels), n_samples_emd, rng)

        # Función de evaluación activa (exacta o MC)
        eval_fn = evaluate_mc if n_samples_emd > 0 else evaluate_exact

        # ── Inicialización: partición balanceada aleatoria ──────────────────
        init_labels = np.array([i % k for i in range(n_total)], dtype=np.int8)
        rng.shuffle(init_labels)

        best_labels = init_labels.copy()
        best_emd    = evaluate_exact(best_labels)   # siempre exacto para el resultado

        # ── Estadísticas del árbol MCTS ─────────────────────────────────────
        # Clave: labels.tobytes() → entero o float
        visits: dict = {}   # key → número de visitas
        values: dict = {}   # key → suma de (−EMD) de rollouts que pasaron por aquí

        root_key = best_labels.tobytes()
        visits[root_key] = 1
        values[root_key] = -best_emd

        def ucb(child_key: bytes, parent_v: int) -> float:
            v = visits.get(child_key, 0)
            if v == 0:
                return float('inf')
            parent_v = max(parent_v, 1)
            return values.get(child_key, 0.0) / v + c_ucb * math.sqrt(math.log(parent_v) / v)

        def rollout(start_labels: np.ndarray) -> tuple:
            """
            Simulación aleatoria con mejora oportunista.
            Aplica hasta rollout_depth movimientos; acepta cada uno solo si
            mejora el EMD estimado (greedy estocástico).
            """
            cur     = start_labels.copy()
            cur_emd = eval_fn(cur)

            for _ in range(rollout_depth):
                u = int(rng.integers(0, n_total))
                j = int(rng.integers(0, k))
                if cur[u] == j:
                    continue
                nxt     = cur.copy()
                nxt[u]  = j
                nxt_emd = eval_fn(nxt)
                if nxt_emd < cur_emd:
                    cur, cur_emd = nxt, nxt_emd

            return cur_emd, cur

        # ── Loop principal MCTS ─────────────────────────────────────────────
        current_labels = best_labels.copy()
        current_key    = root_key
        current_emd    = best_emd

        for _ in range(n_iter):
            parent_v = max(visits.get(current_key, 1), 1)

            # 1. Selección: acción con mayor UCB
            best_ucb_val    = -float('inf')
            best_child_lbl  = None
            best_child_key  = None

            for u in range(n_total):
                cur_part = int(current_labels[u])
                for j in range(k):
                    if j == cur_part:
                        continue
                    child     = current_labels.copy()
                    child[u]  = j
                    ckey      = child.tobytes()
                    score     = ucb(ckey, parent_v)
                    if score > best_ucb_val:
                        best_ucb_val   = score
                        best_child_lbl = child
                        best_child_key = ckey

            if best_child_lbl is None:
                break

            # 2. Expansión + Rollout
            rollout_emd, rollout_lbl = rollout(best_child_lbl)

            # 3. Backpropagation
            visits[best_child_key] = visits.get(best_child_key, 0) + 1
            values[best_child_key] = values.get(best_child_key, 0.0) - rollout_emd
            visits[current_key]    = visits.get(current_key, 0) + 1

            # 4. Actualizar el mejor global (evaluación exacta)
            exact_child_emd = evaluate_exact(best_child_lbl)
            if exact_child_emd < best_emd:
                best_emd    = exact_child_emd
                best_labels = best_child_lbl.copy()

            exact_rollout_emd = evaluate_exact(rollout_lbl)
            if exact_rollout_emd < best_emd:
                best_emd    = exact_rollout_emd
                best_labels = rollout_lbl.copy()

            # 5. Próxima iteración: avanzar hacia el rollout si mejoró,
            #    reset ocasional al mejor global para escapar óptimos locales
            if rollout_emd < current_emd:
                current_labels = rollout_lbl.copy()
                current_key    = current_labels.tobytes()
                current_emd    = rollout_emd
            elif rng.random() < 0.15:
                current_labels = best_labels.copy()
                current_key    = best_labels.tobytes()
                current_emd    = best_emd

        return labels_to_partes(best_labels)
