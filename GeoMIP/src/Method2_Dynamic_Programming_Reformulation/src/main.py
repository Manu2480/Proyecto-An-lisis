# from src.controllers.manager import Manager

# from src.controllers.strategies.force import BruteForce
# from src.controllers.strategies.q_nodes import QNodes
# from src.controllers.strategies.geometric import GeometricSIA


# def iniciar():
#     """Punto de entrada principal"""
#                     # ABCD #
#     # estado_inicial = "100"
#     # condiciones =    "111"
#     # alcance =        "111"
#     # mecanismo =      "111"
#     # estado_inicial = "0000"
#     # condiciones =    "1111"
#     # alcance =        "1111"
#     # mecanismo =      "1111"
#     # estado_inicial = "1000"
#     # condiciones =    "1111"
#     # alcance =        "0111"
#     # mecanismo =      "1111"
#     # estado_inicial = "100000"
#     # condiciones =    "111111"
#     # alcance =        "101011"
#     # mecanismo =      "111111"
#     # estado_inicial = "100000"
#     # condiciones =    "111111"
#     # alcance =        "111111"
#     # mecanismo =      "111111"
#     # estado_inicial = "100000"
#     # condiciones =    "111111"
#     # alcance =        "111111"
#     # mecanismo =      "011111"
#     # estado_inicial = "1000000000"
#     # condiciones =    "1111111111"
#     # alcance =        "1111111111"
#     # mecanismo =      "1111111111"
#     estado_inicial = "1000000000"
#     condiciones =    "1111111111"
#     alcance =        "0101010101"
#     mecanismo =      "1111111111"
#     # estado_inicial = "1000000000"
#     # condiciones =    "1111111111"
#     # alcance =        "1111111110"
#     # mecanismo =      "1111111111"
#     # estado_inicial = "10000000000000000000"
#     # condiciones =    "11111111111111111111"
#     # alcance =        "11111111111111111111"
#     # mecanismo =      "11111111111111111111"
#     # estado_inicial = "10000000000000000000"
#     # condiciones =    "11111111111111111111"
#     # alcance =        "11011011011011011011"
#     # mecanismo =      "10101010101010101010"

#     gestor_sistema = Manager(estado_inicial)

#     ### Ejemplo de solución mediante módulo de fuerza bruta ###
#     analizador_fb = GeometricSIA(gestor_sistema)
#     # analizador_fb = BruteForce(gestor_sistema)
#     sia_uno = analizador_fb.aplicar_estrategia(
#         condiciones,
#         alcance,
#         mecanismo,
#     )
#     print(sia_uno)
import sys
from pathlib import Path

# Agregar el directorio padre de 'src' al path para poder importar módulos desde 'src'
_project_root = Path(__file__).resolve().parents[1]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# pyrefly: ignore [missing-import]
from src.controllers.manager import Manager
# pyrefly: ignore [missing-import]
from src.controllers.strategies.geometric import GeometricSIA
# pyrefly: ignore [missing-import]
from src.controllers.strategies.kpartition import KPartitionSIA
# pyrefly: ignore [missing-import]
from src.controllers.strategies.q_nodes import QNodes
# Optional import: this project often runs only geometric strategy.
try:
    # pyrefly: ignore [missing-import]
    from src.controllers.strategies.phi import Phi
except Exception:
    Phi = None
import multiprocessing
import numpy as np
import pandas as pd
import os
import re
from pathlib import Path


METHOD2_ROOT = Path(__file__).resolve().parents[1]
GEOMIP_ROOT = Path(__file__).resolve().parents[3]

def convertir_a_binario(texto, n_bits=20):
    posiciones = "ABCDEFGHIJKLMNOPQRST"[:n_bits]
    binario = ["0"] * n_bits
    texto = texto.strip().upper()
    for letra in texto:
        if letra in posiciones:
            binario[posiciones.index(letra)] = "1"
    return "".join(binario)


def parse_subsistema_line(fila: str, n_bits: int):
    if not isinstance(fila, str):
        return None, None

    partes = fila.split("|")
    if len(partes) != 2:
        return None, None

    alcance_texto = re.sub(r"[^A-Za-z]", "", partes[0]).upper()
    mecanismo_texto = re.sub(r"[^A-Za-z]", "", partes[1]).upper()
    if not alcance_texto or not mecanismo_texto:
        return None, None

    return (
        convertir_a_binario(alcance_texto, n_bits=n_bits),
        convertir_a_binario(mecanismo_texto, n_bits=n_bits),
    )


def ejecutar_con_tiempo(config_sistema, condiciones, alcance, mecanismo, resultado_queue, tpm):
    try:
        analizador_fi = GeometricSIA(config_sistema)
        sia_dos = analizador_fi.aplicar_estrategia(condiciones, alcance, mecanismo, tpm)
        resultado_queue.put({
            "particion": sia_dos.particion,
            "perdida": str(sia_dos.perdida).replace('.', ','),
            "tiempo": str(sia_dos.tiempo_ejecucion).replace('.', ','),
        })

    except Exception as e:
        resultado_queue.put({
            "particion": None,
            "perdida": None,
            "tiempo": None,
        })

def ejecutar_k_con_tiempo(config_sistema, condiciones, alcance, mecanismo, k, resultado_queue, tpm):
    try:
        analizador_k = KPartitionSIA(config_sistema, k=k)
        sia_k = analizador_k.aplicar_estrategia(condiciones, alcance, mecanismo, tpm)
        
        if isinstance(sia_k.particion, str) and "Inviable" in sia_k.particion:
            resultado_queue.put({
                "particion": sia_k.particion,
                "perdida": None,
                "tiempo": None,
                "estrategia": sia_k.estrategia
            })
        else:
            tiempo_val = getattr(sia_k, 'tiempo_ejecucion', getattr(sia_k, 'tiempo_total', None))
            resultado_queue.put({
                "particion": sia_k.particion,
                "perdida": str(sia_k.perdida).replace('.', ',') if sia_k.perdida is not None else None,
                "tiempo": str(tiempo_val).replace('.', ',') if tiempo_val is not None else None,
                "estrategia": getattr(sia_k, 'estrategia', None)
            })

    except Exception as e:
        resultado_queue.put({
            "particion": None,
            "perdida": None,
            "tiempo": None,
            "estrategia": None
        })

def resolver_tpm_path(estado_inicio: str) -> Path:
    """Find TPM file in common project locations based on state size."""
    sample_name = f"N{len(estado_inicio)}A.csv"
    candidates = (
        METHOD2_ROOT / "src" / ".samples" / sample_name,
        METHOD2_ROOT / ".samples" / sample_name,
        GEOMIP_ROOT / "data" / "samples" / sample_name,
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"No se encontró la TPM '{sample_name}'. Busqué en: {', '.join(str(c) for c in candidates)}"
    )


def inferir_estado_inicial() -> str:
    """Infer an initial state from available datasets (prefers largest NxA.csv)."""
    sample_dirs = (
        METHOD2_ROOT / "src" / ".samples",
        METHOD2_ROOT / ".samples",
        GEOMIP_ROOT / "data" / "samples",
    )
    pattern = re.compile(r"N(\d+)[A-Z]\.csv$")
    available_sizes = []

    for sample_dir in sample_dirs:
        if not sample_dir.exists():
            continue
        for sample_file in sample_dir.glob("N*.csv"):
            match = pattern.match(sample_file.name)
            if match:
                available_sizes.append(int(match.group(1)))

    if not available_sizes:
        raise FileNotFoundError("No hay archivos de muestras TPM disponibles en data/samples ni .samples.")

    n_bits = max(available_sizes)
    return "1" + ("0" * (n_bits - 1))


def ejecutar_desde_excel(
    ruta_excel: Path,
    ruta_salida: Path,
    inicio=0,
    cantidad=50,
    estado_inicio: str | None = None,
    condiciones: str | None = None,
):
    df = pd.read_excel(ruta_excel, sheet_name=8, usecols="B", skiprows=3, names=["Subsistema"]) #! here
    filas = df["Subsistema"].dropna().tolist()
    filas = filas[inicio:inicio + cantidad]
    resultados = []

    estado_inicio = estado_inicio or inferir_estado_inicial()
    condiciones = condiciones or ("1" * len(estado_inicio))
    tpm_path = resolver_tpm_path(estado_inicio)
    tpm = np.genfromtxt(tpm_path, delimiter=",")

    for i, fila in enumerate(filas, start=inicio + 1):
        alcance, mecanismo = parse_subsistema_line(fila, len(estado_inicio))
        if alcance is None or mecanismo is None:
            continue
        print(f"Iteración {i} - Alcance: {alcance}, Mecanismo: {mecanismo}")

        config_sistema = Manager(estado_inicial=estado_inicio)

        resultado_queue = multiprocessing.Queue()
        proceso = multiprocessing.Process(target=ejecutar_con_tiempo, args=(config_sistema, condiciones, alcance, mecanismo, resultado_queue, tpm))
        
        proceso.start()
        proceso.join(timeout=3600)  

        if proceso.is_alive():
            print(f"Iteración {i} - Tiempo límite alcanzado, terminando proceso...")
            proceso.terminate()
            proceso.join()
            resultado = {"perdida": None, "tiempo": None, "particion": None}
        else:
            resultado = (
                resultado_queue.get()
                if not resultado_queue.empty()
                else {"perdida": None, "tiempo": None, "particion": None}
            )

        resultados.append({
            "Iteración": i,
            "Alcance": alcance,
            "Mecanismo": mecanismo,
            "Partición": resultado["particion"],
            "Pérdida": resultado["perdida"],
            "Tiempo de ejecución (s)": resultado["tiempo"],
        })
    df_resultados = pd.DataFrame(resultados)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    df_resultados.to_excel(ruta_salida, index=False)
    print(f"Resultados guardados en {ruta_salida}")

def ejecutar_kparticion_desde_excel(
    ruta_excel: Path,
    ruta_salida: Path,
    k: int = 3,
    inicio=0,
    cantidad=50,
    estado_inicio: str | None = None,
    condiciones: str | None = None,
):
    if not ruta_excel.exists():
        print(f"Error: El archivo Excel no existe en {ruta_excel}")
        return

    try:
        df = pd.read_excel(ruta_excel, sheet_name=8, usecols="B", skiprows=3, names=["Subsistema"])
    except Exception as e:
        print(f"Error al leer la hoja del Excel: {e}")
        return

    filas = df["Subsistema"].dropna().tolist()
    filas = filas[inicio:inicio + cantidad]
    resultados = []

    estado_inicio = estado_inicio or inferir_estado_inicial()
    condiciones = condiciones or ("1" * len(estado_inicio))
    tpm_path = resolver_tpm_path(estado_inicio)
    tpm = np.genfromtxt(tpm_path, delimiter=",")

    for i, fila in enumerate(filas, start=inicio + 1):
        alcance, mecanismo = parse_subsistema_line(fila, len(estado_inicio))
        if alcance is None or mecanismo is None:
            continue
        print(f"Iteración {i} - Alcance: {alcance}, Mecanismo: {mecanismo}")

        config_sistema = Manager(estado_inicial=estado_inicio)

        resultado_queue = multiprocessing.Queue()
        proceso = multiprocessing.Process(target=ejecutar_k_con_tiempo, args=(config_sistema, condiciones, alcance, mecanismo, k, resultado_queue, tpm))
        
        proceso.start()
        proceso.join(timeout=3600)  

        if proceso.is_alive():
            print(f"Iteración {i} - Tiempo límite alcanzado, terminando proceso...")
            proceso.terminate()
            proceso.join()
            resultado = {"perdida": None, "tiempo": None, "particion": None, "estrategia": None}
        else:
            resultado = (
                resultado_queue.get()
                if not resultado_queue.empty()
                else {"perdida": None, "tiempo": None, "particion": None, "estrategia": None}
            )

        resultados.append({
            "Iteración": i,
            "Alcance": alcance,
            "Mecanismo": mecanismo,
            "k": k,
            "Partición": resultado["particion"],
            "Pérdida": resultado["perdida"],
            "Tiempo de ejecución (s)": resultado["tiempo"],
            "Heurística": resultado["estrategia"]
        })
    df_resultados = pd.DataFrame(resultados)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    df_resultados.to_excel(ruta_salida, index=False)
    print(f"Resultados de k-partición ({k}) guardados en {ruta_salida}")

def iniciar():
    ruta_entrada = Path(
        os.getenv(
            "GEOMIP_INPUT_XLSX",
            str(GEOMIP_ROOT / "results" / "Pruebas_Metodo2.xlsx"),
        )
    )
    ruta_salida = Path(
        os.getenv(
            "GEOMIP_OUTPUT_XLSX",
            str(GEOMIP_ROOT / "results" / "resultados_Geometric.xlsx"),
        )
    )
    ejecutar_desde_excel(ruta_entrada, ruta_salida)