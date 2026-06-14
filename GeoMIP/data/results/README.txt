Resultados del proyecto K-QGMIP
==============================

Estructura de carpetas:

  n10/, n15/, n20/, n22/, n25/
    Resultados exactos (benchmark.py) y QNodes k=2 (run_qnodes_k2.py).

  aprox/                          benchmark KL_MC (referencia secundaria)
  rapido/                         benchmark heuristica rapida (k=2..5)
    n10..n25/                     un Excel final por red (post-fix jun 2026)
    benchmark_rapido_2026-06-14_00h32.xlsx
    _archive/2026-06-14/          checkpoints y corridas pre-fix

  comparativa/                    exacto vs rapido (gen_comparativa.py)
    n10..n25_comparativa.xlsx
    comparativa_long.csv
    comparativa_resumen.xlsx

  historico/                      corridas antiguas (mayo 2026)
  finales/                        consolidados de referencia
  logs/n10_n15, logs/n20_plus     logs de ejecucion

  _archive/
    limpieza_2026-06-14/          checkpoints, logs viejos, duplicados root
    old_runs/, result_viejos/     archivos muy antiguos

Finales canonicos (jun 2026):
  Exacto:  n{n}_completo_2026-05-*.xlsx (n10..n22)
  QNodes:  qnodes_k2_n{n}_2026-06-13_*.xlsx (n10,n15,n20; n22 en curso)
  Rapido:  n{n}_rapido_2026-06-13/14_*.xlsx (n10..n25, auditoria OK)

Nota: la ruta vieja GeoMIP/results/ ya no se usa.
Todo queda bajo GeoMIP/data/results/.
