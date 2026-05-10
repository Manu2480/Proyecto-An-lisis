import sys
import traceback
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.controllers.manager import Manager
from src.controllers.strategies.kpartition import KPartitionSIA
from src.main import GEOMIP_ROOT, METHOD2_ROOT, resolver_tpm_path
import numpy as np

def run_debug():
    estado_inicio = "100" # N3
    condiciones = "111"
    alcance = "011"
    mecanismo = "111"
    k = 3
    
    tpm_path = resolver_tpm_path(estado_inicio)
    tpm = np.genfromtxt(tpm_path, delimiter=",")
    
    config_sistema = Manager(estado_inicial=estado_inicio)
    
    print("Iniciando depuracion...")
    try:
        analizador_k = KPartitionSIA(config_sistema, k=k)
        sia_k = analizador_k.aplicar_estrategia(condiciones, alcance, mecanismo, tpm)
        print("Exito:")
        print("Particion:", sia_k.particion)
        print("Perdida:", sia_k.perdida)
        print("Estrategia:", getattr(sia_k, 'estrategia', None))
    except Exception as e:
        print("CRASH DETECTADO:")
        traceback.print_exc()

if __name__ == "__main__":
    run_debug()
