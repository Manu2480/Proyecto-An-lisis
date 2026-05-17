# README para Mauricio — Proyecto K-QGMIP

Hola Mauri, te dejo esta guía para que puedas ponerte al día y ejecutar tu parte del proyecto sin complicaciones. Yo voy a correr la red de **n=22** y tú la de **n=10**.

---

## ¿De qué trata el proyecto?

Estamos implementando y comparando algoritmos para encontrar la **partición mínima de información (MIP)** en redes de transición de estados. En términos simples: dada una red de `n` nodos, queremos dividirla en `k` partes de forma que la "pérdida de información" (medida con EMD — Earth Mover's Distance) sea la mínima posible.

Esto viene de la Teoría de Información Integrada (IIT), que es un framework para medir la irreducibilidad de un sistema.

---

## ¿Qué llevamos hecho?

1. **Algoritmos implementados** (en `GeoMIP/src/Method2_Dynamic_Programming_Reformulation/`):
   - `QNodes` — heurística greedy para k=2
   - `GeometricSIA` — programación dinámica para k=2 (más rápido y mejor que QNodes)
   - `KPartitionSIA` — generalización a k=3,4,5 con dos heurísticas:
     - **Greedy** (estilo QNodes original)
     - **Kernighan-Lin (KL)** — heurística nueva, siempre igual o mejor que Greedy en calidad

2. **Benchmark completo** (`GeoMIP/src/benchmark.py`):
   - Corre todas las estrategias sobre los 50 subconjuntos de prueba de cada red
   - Guarda los resultados en Excel por red en `GeoMIP/results/n{numero}/`
   - Ya tiene los 50 casos exactos de `DatosPruebas2026_1.md` programados para n=10, 15, 20, 22, 25

3. **Resultados ya obtenidos**:
   - n=10 (49 casos): corrió completamente, todos convergieron ✓
   - n=15 (50 casos): corrió completamente, todos convergieron ✓
   - n=20: inviable con el hardware actual (≥35 min por caso)

4. **Optimización reciente**: implementé un caché de subsistemas en `sia.py` que evita recalcular 8 veces por caso la misma operación costosa. Esto mejora mucho el rendimiento para redes grandes.

5. **Bitácoras**: cada sesión de trabajo está documentada en `bitacoras/` (hay 20 entradas). Si quieres entender alguna decisión técnica, está todo ahí.

---

## Cómo preparar el entorno

### Requisitos previos
- Python 3.11 o superior
- `uv` instalado (gestor de paquetes rápido): `pip install uv`

### Instalación (una sola vez)

```bash
cd GeoMIP/src/Method2_Dynamic_Programming_Reformulation
uv sync
```

Eso instala todas las dependencias (numpy, pandas, scipy, etc.) en un entorno virtual local `.venv/`.

---

## Cómo correr el benchmark de n=10

Desde la raíz del repo:

```bash
cd GeoMIP/src/Method2_Dynamic_Programming_Reformulation
uv run python ../benchmark.py --n 10
```

O si quieres especificar el timeout máximo (en segundos, por estrategia):

```bash
uv run python ../benchmark.py --n 10 --timeout 120
```

Para n=10 con 120 segundos de timeout es más que suficiente — cada caso tarda menos de 30 segundos en total.

### ¿Qué hace exactamente?

Corre estas estrategias sobre los **49 subconjuntos** de la red N10A.csv:

| Estrategia       | k | Descripción                            |
|------------------|---|----------------------------------------|
| QNodes           | 2 | Heurística greedy base                 |
| GeometricSIA     | 2 | Programación dinámica (más preciso)    |
| KPartitionSIA-QN | 3,4,5 | Greedy extendido a k partes        |
| KPartitionSIA-KL | 3,4,5 | Kernighan-Lin extendido a k partes |

Al final calcula automáticamente qué combinación (k, estrategia) es la mejor para cada caso.

### ¿Dónde quedan los resultados?

- Checkpoint cada 5 casos: `GeoMIP/results/n10/checkpoint_FECHA.xlsx`
- Resultado final: `GeoMIP/results/n10/n10_completo_FECHA.xlsx`
- Excel consolidado (todas las redes): `GeoMIP/results/benchmark_completo_FECHA.xlsx`

---

## Estructura del proyecto (lo que más usarás)

```
projecto-analisis-20261/
├── GeoMIP/
│   ├── data/
│   │   └── samples/
│   │       └── N10A.csv          ← la TPM de tu red (ya está en el repo)
│   ├── results/
│   │   └── n10/                  ← aquí quedan tus resultados
│   └── src/
│       ├── benchmark.py          ← el script que corres
│       └── Method2_Dynamic_Programming_Reformulation/
│           └── src/
│               ├── controllers/strategies/
│               │   ├── geometric.py    ← GeometricSIA
│               │   ├── kpartition.py   ← KPartitionSIA (Greedy + KL)
│               │   └── q_nodes.py      ← QNodes
│               └── models/base/
│                   └── sia.py          ← clase base con el caché
├── bitacoras/                    ← historial de decisiones técnicas
└── README_MAURICIO.md            ← este archivo
```

---

## Puntos clave que debes saber

- **No modifiques** `sia.py` ni `benchmark.py` sin avisarme, porque yo también los uso para n=22.
- La red **N10A.csv ya está en el repo** (solo pesa ~1 KB porque son 10 nodos = 1024 filas).
- Si algo falla al importar, asegúrate de correr el comando desde la carpeta `Method2_Dynamic_Programming_Reformulation/`, no desde la raíz.
- Los resultados que generes guárdalos en `GeoMIP/results/n10/` (el benchmark lo hace automáticamente).
- Cuando termines, haz commit y push de los Excels de resultados en esa carpeta.

---

## Comando resumen (copia y pega)

```bash
cd "GeoMIP/src/Method2_Dynamic_Programming_Reformulation"
uv sync
uv run python ../benchmark.py --n 10 --timeout 120
```

Tiempo estimado: **menos de 5 minutos** para los 49 casos completos.

---

Cualquier duda me avisas. Suerte!
