# PROMPT COMPLETO — Proyecto K-QGMIP
## Para agente/programador IA — Análisis y Diseño de Algoritmos 2026-1

---

## 0. INSTRUCCIÓN INICIAL OBLIGATORIA

Antes de escribir una sola línea de código o tomar cualquier decisión de diseño,
debes leer **todos** los archivos de documentación disponibles en el repositorio:

```
docs/
├── Manual_Tecnico_KQMIP.md
├── Ejemplos.md
├── DatosPruebas2026_1.md
├── 1_Guia_Proyecto_ADA.md
└── 2_GeoMIP.md
```

Léelos en ese orden. Extrae y consolida mentalmente:
- El modelo matemático completo (TPM, marginalización, producto tensorial, EMD).
- El contrato de la clase base `SIA` y cómo se conecta con las estrategias.
- Los ejemplos numéricos del documento GeoMIP (capítulo 4) — son la referencia
  de validación más importante.
- Los casos de prueba del Excel `DatosPruebas2026_1` (sistemas de 10 y 15 nodos).
- Las especificaciones del Manual Técnico (lo que debe aparecer en el entregable).

**No avances al paso 1 hasta haber completado esta lectura.**

---

## 1. CONTEXTO Y OBJETIVO DEL PROYECTO

### 1.1 Problema central

Se trabaja sobre **Integrated Information Theory (IIT)** y su componente de
**System Irreducibility Analysis (SIA)**. Dado un sistema de nodos binarios
descrito por una Matriz de Probabilidad de Transición (TPM), el objetivo es
encontrar la **Minimum Information Partition (MIP)**: la partición del sistema
en k grupos que minimiza la pérdida de información causal medida con
**Earth Mover's Distance (EMD)** con métrica de Hamming.

### 1.2 Estado actual del repositorio

El repositorio `projecto-analisis-20261` tiene la siguiente estructura funcional:

```
projecto-analisis-20261/
├── QNodes/           ← Implementación base: k=2 únicamente
│   ├── exec.py
│   ├── src/
│   │   ├── main.py
│   │   ├── controllers/manager.py
│   │   ├── strategies/
│   │   │   ├── force.py        ← Fuerza bruta (referencia exacta)
│   │   │   ├── q_nodes.py      ← Heurística Q voraz
│   │   │   └── phi.py          ← Interfaz PyPhi
│   │   ├── models/
│   │   │   ├── base/sia.py     ← Clase abstracta central
│   │   │   └── core/
│   │   │       ├── system.py   ← Condicionamiento, particiones, márgenes
│   │   │       ├── ncube.py    ← Tensor n-dimensional por nodo
│   │   │       └── solution.py ← Objeto resultado
│   │   └── funcs/
│   │       ├── iit.py          ← EMD
│   │       ├── force.py        ← Generación de candidatos
│   │       └── format.py       ← Formato de salida
│   └── .samples/               ← TPMs N2–N10 en CSV
│
└── GeoMIP/
    ├── data/samples/           ← TPMs N3–N15 (variantes A,B,C...)
    ├── results/                ← Excels de entrada/salida
    └── src/
        ├── Method2_Dynamic_Programming_Reformulation/
        │   ├── exec.py
        │   ├── run_kpart.py
        │   ├── src/
        │   │   ├── main.py
        │   │   ├── controllers/strategies/
        │   │   │   ├── geometric.py    ← GeoMIP k=2 (DP geométrica)
        │   │   │   ├── kpartition.py   ← k=3,4,5 (greedy + clustering)
        │   │   │   ├── q_nodes.py
        │   │   │   └── force.py
        │   │   └── models/, funcs/     ← Misma arquitectura que QNodes
        └── Method3_Batch_Processing/   ← Batch geométrico sobre todas las TPM
```

**Lo que ya está implementado y funciona:**
- Fuerza bruta para k=2 (referencia exacta, inviable para n>12).
- Heurística QNodes para k=2.
- GeoMIP (`GeometricSIA`) para k=2 con programación dinámica y tabla de costos.
- Extensión k-particiones (`KPartitionSIA`) para k=3,4,5 via greedy encadenado
  + clustering jerárquico sobre la matriz de costos.
- Batch processing (Method2 y Method3) con entrada/salida Excel.
- Dataset: TPMs de N3 a N15 con variantes A,B,C.

**Lo que NO está y debe construirse:**
- TPMs de prueba para n = 6, 17, 18, 19, 20, 21, 22, 23, 24, 25 nodos.
- Pipeline de benchmarking automatizado para matrices grandes.
- Análisis de complejidad empírico (curvas tiempo vs n).
- Documento técnico completo en LaTeX.
- Optimizaciones de rendimiento para n > 15.

---

## 2. PLAN DE ACCIÓN — EJECUTAR EN ESTE ORDEN EXACTO

### FASE 0 — Diagnóstico previo (NO escribir código aún)

Antes de tocar el código, responde estas preguntas explícitamente en tu salida:

1. ¿La implementación de `geometric.py` reproduce correctamente los resultados
   del Capítulo 4 del documento `2_GeoMIP.md` para el sistema N3C?
   Verifica manualmente los valores de la Tabla 4.2 (costos desde estado 000).

2. ¿`kpartition.py` produce resultados coherentes con `force.py` para sistemas
   pequeños (N3, N5)? ¿La pérdida de k=3 es ≤ pérdida de k=2?

3. ¿El `Manager` en ambas ramas (QNodes y GeoMIP) carga correctamente las TPMs?
   ¿Hay duplicación de lógica entre ambas ramas que deba unificarse?

4. ¿El generador `creation.py` puede crear TPMs deterministas reproducibles para
   n = 17 a 25? ¿Qué tiempo y memoria requiere para n=25?

5. ¿Hay tests unitarios? Si no los hay, ¿cuáles son los 5 casos mínimos que
   deben existir antes de proceder?

**Documenta las respuestas. Si encuentras bugs en este diagnóstico, corrígelos
antes de continuar.**

---

### FASE 1 — Refactorización del repositorio base

**Criterio:** Refactorizar solo lo necesario para eliminar duplicación y
facilitar el trabajo siguiente. No reescribir por gusto estético.

#### 1.1 Unificación de modelos compartidos

`QNodes/src/models/` y `GeoMIP/src/Method2/src/models/` son casi idénticos.
Evalúa si tiene sentido crear un paquete `shared/` en la raíz con:
```
shared/
├── models/
│   ├── base/sia.py
│   └── core/ (system, ncube, solution)
└── funcs/ (iit/EMD, format)
```
Y que tanto QNodes como GeoMIP lo importen. **Solo hazlo si no rompe los
entornos `uv` existentes.** Si el riesgo es alto, documenta la deuda técnica
y continúa sin unificar.

#### 1.2 Limpieza de archivos irrelevantes

Mueve a una carpeta `_archive/` (no borres):
- `hyper-v0.py` ... `hyper-v8.py` (visualizaciones experimentales).
- `result viejos/` bajo `GeoMIP/results/`.
- `pruebas_Metodo1.xlsx` (resultados de método no implementado).

#### 1.3 Estandarización de entrada/salida

Asegúrate de que **todas las estrategias** (force, qnodes, geometric, kpartition)
devuelvan un objeto `Solution` con al menos:
```python
@dataclass
class Solution:
    particion: tuple          # e.g. ({'A','B'}, {'C','D'}) para k=2
    perdida: float            # EMD mínima encontrada
    tiempo_ms: float          # tiempo de cómputo en milisegundos
    estrategia: str           # nombre de la estrategia usada
    n_nodos: int              # tamaño del sistema
    k: int                    # número de partes de la partición
```

#### 1.4 Tests de regresión mínimos

Antes de continuar, implementa en `tests/` al menos:
```
tests/
├── test_emd.py           ← verifica EMD de ejemplos conocidos del doc
├── test_geometric_n3.py  ← reproduce Tabla 4.2 de 2_GeoMIP.md exactamente
├── test_kpart_coherence.py ← perdida(k=3) ≤ perdida(k=2) para N3,N5,N7
└── test_solutions.py     ← verifica que todas las estrategias devuelven Solution
```

Ejecuta con `uv run pytest tests/` y confirma que pasan antes de continuar.

---

### FASE 2 — Generación de matrices de prueba grandes

El dataset actual llega hasta N15. Se necesitan TPMs para:

```
n ∈ {6, 17, 18, 19, 20, 21, 22, 23, 24, 25}
```

**Nota:** N6 puede estar ya en el dataset; verificar primero.

#### 2.1 Estrategia de generación

Usar `GeoMIP/data/creation.py` (`SystemCreator`) para generar redes sintéticas.
Para cada n, generar **al menos 2 variantes** (ej. N17A, N17B) con semillas
fijas para reproducibilidad:

```python
# Ejemplo de uso esperado
creator = SystemCreator(n=17, seed=42)
tpm = creator.generate()
creator.save(tpm, "GeoMIP/data/samples/N17A.csv")
```

Si `creation.py` no soporta semillas, agrégaselas como parámetro.

#### 2.2 Validación de las nuevas TPMs

Para cada nueva TPM generada, verificar:
- Cada fila suma 1 (distribución de probabilidad válida).
- No hay filas completamente nulas.
- La TPM es de tamaño `2^n × 2^n` (estado-estado) o `2^n × n` (estado-nodo).
- El archivo CSV tiene el formato esperado por el Manager.

Crear script: `GeoMIP/data/validate_tpms.py` que corra estas comprobaciones
sobre todo el directorio `samples/`.

#### 2.3 Estimación de memoria y tiempo

Para n=20: la TPM estado-estado tiene `2^20 × 2^20 = 10^12` entradas (inviable).
La representación **estado-nodo** tiene `2^20 × 20 ≈ 20M` entradas (manejable).

**Verificar que el código usa representación estado-nodo para n > 15.**
Si no es así, esto es un bug crítico a corregir antes de continuar.

Documenta la memoria estimada para cada n:
| n  | Estados | TPM estado-nodo (float64) | RAM estimada |
|----|---------|--------------------------|--------------|
| 17 | 131,072 | 131,072 × 17             | ~17 MB       |
| 20 | 1M      | 1M × 20                  | ~160 MB      |
| 25 | 33M     | 33M × 25                 | ~6.6 GB      |

Para n=25 puede ser inviable en RAM estándar. Documenta el límite práctico
observado en la máquina de pruebas y ajusta el dataset objetivo en consecuencia.

---

### FASE 3 — Benchmarking completo

#### 3.1 Script de benchmark unificado

Crear `GeoMIP/src/benchmark.py` que para cada TPM en el dataset ejecute todas
las estrategias disponibles y registre resultados:

```python
# Pseudocódigo del benchmark
for tpm_file in sorted(glob("data/samples/N*.csv")):
    n = parse_n(tpm_file)
    for subsistema in generar_subsistemas_representativos(n, max_casos=10):
        for k in [2, 3, 4, 5]:
            for estrategia in get_estrategias_disponibles(n, k):
                resultado = ejecutar_con_timeout(estrategia, subsistema, timeout=3600)
                registrar(resultado, tpm_file, k, estrategia)

exportar_excel("GeoMIP/results/benchmark_completo.xlsx")
```

**Reglas de timeout:**
- n ≤ 10: timeout = 60s por caso.
- 10 < n ≤ 15: timeout = 300s.
- 15 < n ≤ 20: timeout = 1800s.
- n > 20: solo estrategias heurísticas (no fuerza bruta).

#### 3.2 Subsistemas representativos por tamaño

Para no explotar el espacio combinatorio, usar estos subsistemas fijos:
- Sistema completo (alcance = mecanismo = todos los nodos).
- Mitad superior vs mitad inferior.
- Primeros ⌊n/3⌋ nodos como mecanismo, resto como alcance.
- Estado inicial = todos en 0, todos en 1, y uno aleatorio con semilla fija.

#### 3.3 Métricas a registrar por cada ejecución

```
| tpm | n | estado_inicial | alcance | mecanismo | k | estrategia |
| particion | perdida_emd | tiempo_ms | memoria_mb | convergio |
```

#### 3.4 Validación cruzada

Para n ≤ 10 y k=2: comparar GeometricSIA vs BruteForce.
Calcular tasa de acierto exacto y error relativo según los umbrales del
documento `2_GeoMIP.md` sección 5.2.2:

| Nivel      | Tasa acierto | Error relativo máx |
|------------|--------------|-------------------|
| Excelente  | >90%         | <1%               |
| Bueno      | >80%         | <5%               |
| Aceptable  | >70%         | <10%              |

---

### FASE 4 — Optimizaciones para matrices grandes

Implementar solo las que sean necesarias según los resultados del benchmark.
No optimizar prematuramente.

#### 4.1 Memoización en la tabla de costos

La función `CalcularCostoDeTransicion` es recursiva. Verificar que usa caché
(memoización). Si no, agregar `@functools.lru_cache` o `dict` explícito.

#### 4.2 Representación sparse para n > 18

Para TPMs de n > 18, la tabla de transiciones puede ser escasa. Evaluar uso de
`scipy.sparse` si más del 80% de las entradas son 0.

#### 4.3 Paralelización del cálculo de tabla T

El cálculo de `T[v, i, j]` para diferentes variables `v` es independiente.
Usar `concurrent.futures.ProcessPoolExecutor` para paralelizar por variable:

```python
with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
    futures = {executor.submit(calcular_tabla_variable, v, tensors[v]): v
               for v in variables}
```

#### 4.4 Límite práctico documentado

Después de benchmarking, documentar en el README:
```
Límites observados en <especificaciones de la máquina>:
- Fuerza bruta viable: n ≤ X
- GeoMIP k=2 viable: n ≤ Y
- GeoMIP k=5 viable: n ≤ Z
- Memoria pico para n=20: W GB
```

---

### FASE 5 — Documento técnico en LaTeX

**Este es el entregable académico principal.** Debe generarse como código LaTeX
compilable (no PDF, no Word). Estructura obligatoria según `Manual_Tecnico_KQMIP.md`:

#### 5.1 Instrucciones de generación

Crear el archivo `docs/ManualTecnico_KQMIP.tex` con la siguiente estructura.
Usar el paquete `memoir` o `report`. Incluir:

```latex
\documentclass[12pt, a4paper]{report}
\usepackage[utf8]{inputenc}
\usepackage[spanish]{babel}
\usepackage{amsmath, amssymb, amsthm}
\usepackage{algorithm2e}       % pseudocódigos
\usepackage{listings}          % código Python
\usepackage{booktabs}          % tablas profesionales
\usepackage{pgfplots}          % gráficas de rendimiento
\usepackage{tikz}              % diagramas UML y arquitectura
\usepackage{hyperref}
\usepackage{biblatex}
```

#### 5.2 Secciones requeridas (del Manual_Tecnico_KQMIP.md)

```
\chapter{Resumen Ejecutivo}
  - Descripción del problema (MIP/SIA en IIT)
  - Enfoque algorítmico: GeoMIP + k-particiones
  - Resultados principales (tabla resumen del benchmark)
  - Limitaciones y recomendaciones

\chapter{Fundamentos Teóricos}
  - Definición formal de k-particiones (con notación matemática)
  - Formulación del problema de optimización (ecuación 1.1 de GeoMIP)
  - Extensión de bi-partición a k-partición
  - Análisis de complejidad del espacio de soluciones
    P_{k=2}(V) = 2^{u+v-1} - 1  vs  \Theta(k^{2n-1} - 1)

\chapter{Arquitectura del Software}
  \section{Diagrama de Arquitectura General}   % TikZ
  \section{Diagrama de Clases UML}             % TikZ
    % Clase base SIA → herencia hacia KGeoMIP y KQNodes
    % NCube, System, Solution, Manager
  \section{Diagrama de Paquetes}               % TikZ
    % Estructura de directorios src/
  \section{Diagrama de Secuencia}              % TikZ
    % Flujo: Manager → GeometricSIA → tabla T → MIP

\chapter{Descripción Algorítmica}
  \section{GeoMIP k=2: Tabla de Costos y DP}
    % Algoritmo 1 del doc GeoMIP (BFS modificado)
    % Función de costo t(i,j) con factor exponencial
  \section{Extensión a k-particiones}
    % Algoritmo greedy encadenado
    % Clustering jerárquico sobre T
  \section{Análisis de Complejidad Teórica}
    % O(n * 2^n) vs O(2^{2n-1}) fuerza bruta

\chapter{Resultados Experimentales}
  \section{Benchmark de Validación (n ≤ 10)}
    % Tabla: tasa de acierto vs fuerza bruta por estrategia
  \section{Escalabilidad (n = 6 a 25)}
    % Gráfica tiempo vs n para cada estrategia (pgfplots)
    % Gráfica pérdida EMD vs n
  \section{Comparativa k=2 vs k=3,4,5}
    % Para n fijo, ¿mejora la pérdida al aumentar k?
  \section{Límites Prácticos Observados}

\chapter{Manual de Uso}
  \section{Requisitos e Instalación}
    % uv sync, dependencias, SO compatible
  \section{Ejecución de un Caso Individual (QNodes)}
  \section{Ejecución Batch (Method2/Method3)}
  \section{Generación de Nuevas TPMs}
  \section{Interpretación de Resultados}

\chapter{Conclusiones y Trabajo Futuro}
```

#### 5.3 Figuras obligatorias en el documento

Todas generadas con TikZ o pgfplots dentro del .tex (no imágenes externas):

1. **Hipercubo 3D** con etiquetas binarias y aristas coloreadas por distancia
   Hamming (reproducir Figura 2.2 de GeoMIP).
2. **Diagrama de clases UML** con herencia SIA → GeometricSIA, KPartitionSIA,
   QNodesSIA, BruteForceSIA.
3. **Gráfica de curvas tiempo vs n** para cada estrategia (log-log).
4. **Tabla de benchmark** comparativa con booktabs.
5. **Diagrama de secuencia** del flujo principal.

#### 5.4 Tablas de resultados

Los resultados del benchmark deben insertarse como tablas LaTeX generadas
automáticamente desde Python. Crear `docs/gen_tables.py` que:
- Lee `GeoMIP/results/benchmark_completo.xlsx`.
- Genera archivos `.tex` parciales en `docs/tables/`.
- El `.tex` principal los incluye con `\input{tables/benchmark_n10.tex}`.

---

## 3. CONVENCIONES DE NOMENCLATURA

Según `Manual_Tecnico_KQMIP.md`:

| Estrategia           | Repositorio/Carpeta | Clase principal  |
|----------------------|---------------------|------------------|
| GeoMIP K-particiones | `KGeoMIP`           | `KGeoMIP`        |
| QNodes K-particiones | `KQNodes`           | `KQNodes`        |

Aplicar en:
- Nombre de clases Python.
- Nombres de archivos Excel de resultados.
- Referencias en el documento LaTeX.
- Nombre del repositorio Git si aplica.

---

## 4. CRITERIOS DE ACEPTACIÓN

El proyecto se considera completo cuando:

### Código
- [ ] `uv run pytest tests/` pasa al 100%.
- [ ] `uv run exec.py` en Method2 produce resultados en < 1h para n ≤ 15.
- [ ] `uv run benchmark.py` genera `benchmark_completo.xlsx` con datos para
      todos los n de {6,10,12,15,17,18,19,20,21,22,23,24,25} (o hasta el
      límite práctico documentado).
- [ ] Todas las estrategias retornan objetos `Solution` válidos.
- [ ] No hay imports circulares ni dependencias hardcodeadas a rutas absolutas.

### Resultados
- [ ] GeometricSIA alcanza tasa de acierto ≥ 70% vs fuerza bruta para n ≤ 10.
- [ ] KPartitionSIA produce pérdida(k=3) ≤ pérdida(k=2) en ≥ 80% de los casos.
- [ ] Curvas de escalabilidad muestran ventaja clara de GeoMIP sobre fuerza bruta.

### Documento LaTeX
- [ ] `pdflatex ManualTecnico_KQMIP.tex` compila sin errores.
- [ ] Contiene todas las secciones del capítulo 2 de `Manual_Tecnico_KQMIP.md`.
- [ ] Los diagramas UML están en TikZ (no imágenes externas).
- [ ] Las tablas de resultados se generan desde `gen_tables.py`.
- [ ] Bibliografía incluye al menos: Tononi (IIT), PyPhi paper, Blondel (Louvain).

---

## 5. RESTRICCIONES Y ADVERTENCIAS

1. **No uses PyPhi como dependencia de producción** para n > 15. Es demasiado
   lento. Úsalo solo como referencia de validación en casos pequeños.

2. **No generes TPMs estado-estado para n > 18** en RAM. Usa siempre la
   representación estado-nodo (`2^n × n`).

3. **Los resultados de k-partición deben ser reproducibles**. Todas las
   funciones con aleatoriedad deben aceptar un parámetro `seed`.

4. **El documento LaTeX debe ser autocontenido**: no referencias a rutas
   locales absolutas, no imágenes externas, funcionar en cualquier máquina
   con una distribución TeX estándar (TeX Live 2023+).

5. **No borres archivos del repo base**. Mueve, refactoriza, archiva — pero
   mantén trazabilidad del trabajo previo.

6. **Documenta todo lo que no implementes**. Si el límite de n=25 no es viable
   en la máquina disponible, documentarlo explícitamente es parte del entregable.

---

## 6. ORDEN DE ENTREGA SUGERIDO

```
Semana 1:  Fase 0 (diagnóstico) + Fase 1 (refactorización)
Semana 2:  Fase 2 (matrices grandes) + tests de regresión
Semana 3:  Fase 3 (benchmark completo)
Semana 4:  Fase 4 (optimizaciones según necesidad) + Fase 5 (LaTeX)
```

---

*Prompt generado para el proyecto K-QGMIP — Análisis y Diseño de Algoritmos 2026-1*
*Universidad de Caldas — Facultad de Inteligencia Artificial e Ingenierías*
