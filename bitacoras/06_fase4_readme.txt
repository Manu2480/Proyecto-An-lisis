BITÁCORA 06 — Fase 4: Documentación de límites y README
Fecha: 16/05/2026
Fase: 4 — Optimizaciones y documentación de límites prácticos

ACCIONES:
  Se reescribió el README.md raíz para documentar todos los puntos
  del estado actual del proyecto: estrategias, datasets, límites
  prácticos por CPU, estructura de carpetas y nomenclatura.

ARCHIVOS MODIFICADOS:
  README.md (reescrito completamente)
    + Tabla de estrategias con módulos y descripción
    + Requisitos actualizados (Windows + Linux)
    + Instrucciones de instalación y ejecución (uv sync)
    + Comandos para benchmark, tests y validador
    + Tabla de datasets con n, filas y tipo
    + Tabla de límites prácticos por estrategia
    + Estructura de directorios actualizada
    + Nomenclatura (KGeoMIP, KQNodes, SIA, MIP)
    + Historial de cambios relevantes (bugs corregidos)

LÍMITES DOCUMENTADOS:
  BruteForce:   n <= 6  (exponencial, solo validación cruzada)
  QNodes:       n <= 15 (greedy, no garantiza optimalidad)
  GeometricSIA: n <= 15 (DP en hipercubo, O(2^n * n) memoria)
  KPartitionSIA: n <= 12 (añade overhead clustering por k)

NOTA:
  GPU/multicore (Fase 4B del ADDENDUM) se implementa SOLO si los resultados
  del benchmark justifican el esfuerzo. Ver ADDENDUM_GPU_PARALLELIZACION.md.
