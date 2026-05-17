"""
run_full_benchmark.py
=====================
Script orquestador que espera a que los CSV grandes estén listos
y luego lanza el benchmark completo n=17..25.

Ejecutar desde:
  GeoMIP/src/Method2_Dynamic_Programming_Reformulation/
  uv run python ../../run_full_benchmark.py
"""
import subprocess
import sys
import time
from pathlib import Path

SAMPLES = Path(__file__).parent.parent / "data" / "samples"
SCRIPT  = Path(__file__).parent.parent / "src" / "benchmark.py"
METHOD2 = Path(__file__).parent

# N que necesitan CSV ya generados
REQUIRED = {
    17: "N17A.csv",
    18: "N18A.csv",
    19: "N19A.csv",
    20: "N20A.csv",
    21: "N21A.csv",
    22: "N22A.csv",
    23: "N23A.csv",
    24: "N24A.csv",
    25: "N25A.csv",
}

def wait_for_csvs(ns: list[int], poll_secs: int = 30):
    """Espera hasta que todos los CSV necesarios existan."""
    needed = {n: SAMPLES / REQUIRED[n] for n in ns if n in REQUIRED}
    pending = {n: p for n, p in needed.items() if not p.exists()}
    if pending:
        print(f"Esperando {len(pending)} CSV(s): {[REQUIRED[n] for n in pending]}")
    while pending:
        time.sleep(poll_secs)
        pending = {n: p for n, p in pending.items() if not p.exists()}
        done = [n for n in needed if n not in pending]
        if done:
            print(f"  CSV listos: {[REQUIRED[n] for n in done]}")
        if pending:
            still = [REQUIRED[n] for n in pending]
            print(f"  Aun esperando: {still}")
    print("Todos los CSV disponibles.")


def run_batch(ns: list[int], timeout: int = 3600, k: list[int] = None):
    """Lanza benchmark.py para el conjunto de n dado."""
    if k is None:
        k = [3, 4]
    ns_str = " ".join(str(n) for n in ns)
    k_str  = " ".join(str(x) for x in k)
    cmd = [
        sys.executable, str(SCRIPT),
        "--n", *[str(n) for n in ns],
        "--timeout", str(timeout),
        "--k", *[str(x) for x in k],
        "--skip-bruteforce",
    ]
    print(f"\n{'='*60}")
    print(f"Lanzando: n={ns_str}  timeout={timeout}s  k={k_str}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=str(METHOD2))
    return result.returncode


if __name__ == "__main__":
    # Fase A: n=17,18,19 (CSV ya existen)
    wait_for_csvs([17, 18, 19])
    rc = run_batch([17, 18, 19], timeout=1800, k=[3, 4])
    print(f"Fase A terminada (rc={rc})")

    # Fase B: n=20,21,22 (CSV ya existen)
    wait_for_csvs([20, 21, 22])
    rc = run_batch([20, 21, 22], timeout=1800, k=[3, 4])
    print(f"Fase B terminada (rc={rc})")

    # Fase C: n=23,24,25 (esperamos a que genere_large_tpms termine)
    wait_for_csvs([23, 24, 25], poll_secs=60)
    rc = run_batch([23, 24, 25], timeout=3600, k=[3])
    print(f"Fase C terminada (rc={rc})")

    print("\nBenchmark completo n=17..25 finalizado.")
