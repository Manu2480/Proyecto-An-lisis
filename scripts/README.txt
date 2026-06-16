Scripts de graficas — proyecto K-QGMIP
======================================

Solo quedan utilidades de visualizacion y auditoria de graficas.
Las ejecuciones de benchmark van por consola desde GeoMIP/src/ (ver VIDEO_GUIA_COMANDOS.txt).

Archivos:
  generar_graficas_proyecto.py  Una figura por matriz: outputs/plots/proyecto/n{n}/matriz_n{n}.png
  generar_graficas.py           PNG en outputs/plots/ (plantilla enunciado)
  run_graficas_proyecto.sh        WSL: instala matplotlib y corre proyecto
  audit_graficas_proyecto.py      Valida cifras de las graficas vs CSV
  run_audit_graficas.sh           Wrapper WSL auditoria

Comandos rapidos (desde raiz del repo, PowerShell):

  uv run --directory GeoMIP/src/Method2_Dynamic_Programming_Reformulation python ../../../scripts/generar_graficas_proyecto.py

  uv run --directory GeoMIP/src/Method2_Dynamic_Programming_Reformulation python ../../../scripts/generar_graficas.py
