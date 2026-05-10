import sys
import os
import re
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.main import ejecutar_kparticion_desde_excel, GEOMIP_ROOT, METHOD2_ROOT

def get_all_tpms():
    sample_dirs = (
        METHOD2_ROOT / "src" / ".samples",
        METHOD2_ROOT / ".samples",
        GEOMIP_ROOT / "data" / "samples",
    )
    pattern = re.compile(r"N(\d+)[A-Z]\.csv$")
    tpms = []
    
    for sample_dir in sample_dirs:
        if not sample_dir.exists():
            continue
        for sample_file in sample_dir.glob("N*.csv"):
            match = pattern.match(sample_file.name)
            if match:
                n_bits = int(match.group(1))
                estado_inicio = "1" + ("0" * (n_bits - 1))
                tpms.append((sample_file.stem, estado_inicio))
    
    # Return unique tpms based on name
    return {name: est for name, est in tpms}.items()

if __name__ == "__main__":
    print("Iniciando simulación batch completa para todos los sistemas y particiones k=3, 4, 5...")
    ruta_entrada = GEOMIP_ROOT / "results" / "Pruebas_Metodo2.xlsx"
    
    all_tpms = list(get_all_tpms())
    if not all_tpms:
        print("No se encontraron archivos TPM (.csv).")
        sys.exit(1)
        
    for name, estado_inicio in all_tpms:
        n_nodos = len(estado_inicio)
        for k in [3, 4, 5]:
            # Validar que k no exceda el número de nodos disponibles
            if k > n_nodos:
                print(f"\n⊘ Saltando {name} con k={k} (insuficientes nodos: solo {n_nodos} disponibles)")
                continue
            
            ruta_salida = GEOMIP_ROOT / "results" / f"resultados_kpartition_{name}_k{k}.xlsx"
            print(f"\n==========================================")
            print(f" Procesando {name} con k={k} ({n_nodos} nodos)")
            print(f"==========================================")
            try:
                ejecutar_kparticion_desde_excel(
                    ruta_excel=ruta_entrada,
                    ruta_salida=ruta_salida,
                    k=k,
                    inicio=0,
                    cantidad=50,
                    estado_inicio=estado_inicio
                )
            except Exception as e:
                print(f"Error procesando {name} con k={k}: {e}")
                
    print("\nProceso global de k-particiones completado exitosamente.")
