Resultados del proyecto K-QGMIP
==============================

Estructura de carpetas:

  n10/, n15/, n20/, n22/, n25/
    Resultados por tamano de red (Excel completo y checkpoints).
    benchmark.py y benchmark_aprox.py guardan aqui.

  aprox/                          benchmark KL_MC (Geo + KL aprox)
  rapido/                         benchmark MCTS+MC-EMD record (k=2..5)
  comparativa/                    tablas exacto vs rapido para graficos

  historico/
    Corridas antiguas (intentos previos, formatos viejos).
    Restaurado desde git commit d668300.

  finales/
    Benchmarks consolidados de referencia (mayo 2026).

  logs/
    n10_n15/  logs de corridas pequenas
    n20_plus/ logs de corridas n>=20

  _archive/
    Resultados muy viejos y checkpoints descartados.

  benchmark_completo_*.xlsx
    Excel consolidado con hojas por n (en la raiz).

Nota: la ruta vieja GeoMIP/results/ ya no se usa.
Todo queda bajo GeoMIP/data/results/.
