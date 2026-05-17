"""
GeoMIP/data/validate_tpms.py
Validador de matrices de transición de probabilidad (TPMs).

Comprueba que cada archivo CSV en GeoMIP/data/samples/ tenga:
  - Dimensiones correctas: 2^n filas × n columnas
  - Valores en [0, 1] (TPM binaria probabilística)
  - Cada fila suma a 1 (si se interpreta como distribución)
    ← En realidad las TPMs aquí almacenan estados-nodos binarios (0/1 exacto)
       por lo que el valor debe ser exactamente 0 o 1 (no fracciones).
  - Sin NaN ni Inf

Uso:
    uv run python validate_tpms.py
    uv run python validate_tpms.py --dir custom/path
    uv run python validate_tpms.py --file N3C.csv

Salida:
    Tabla con estado de cada archivo + resumen final.
    Código de salida: 0 si todos pasan, 1 si alguno falla.
"""
import argparse
import sys
import math
from pathlib import Path

import numpy as np

# ── Constantes ──────────────────────────────────────────────────────────────
DEFAULT_SAMPLES = Path(__file__).parent / "samples"
TOL = 1e-9           # tolerancia para comparaciones float
MAX_N_FULL_LOAD = 20 # para n > 20 sólo se validan headers y muestras

# ── Colores ANSI ─────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

def _ok(msg):  return f"[OK] {msg}"
def _err(msg): return f"[ERR] {msg}"
def _warn(msg): return f"[WARN] {msg}"


# ── Función de validación ────────────────────────────────────────────────────
def validate_file(path: Path, verbose: bool = True) -> dict:
    """
    Valida un CSV de TPM.

    Returns:
        dict con keys: name, n, rows, cols, ok, errors
    """
    name = path.name
    errors = []
    warnings = []

    # ── Inferir n desde el nombre (Nnn*.csv)
    n_expected = None
    stem = path.stem  # p.ej. "N17A"
    digits = ""
    for ch in stem[1:]:
        if ch.isdigit():
            digits += ch
        else:
            break
    if digits:
        n_expected = int(digits)

    # ── Leer CSV ─────────────────────────────────────────────────────────────
    try:
        if n_expected is not None and n_expected > MAX_N_FULL_LOAD:
            # Para matrices muy grandes cargamos sólo las primeras 1000 filas
            # para verificar formato, y calculamos dimensiones por tamaño de archivo.
            data = np.genfromtxt(path, delimiter=",", max_rows=1000)
            expected_rows = 2 ** n_expected
            # Estima filas por tamaño de archivo
            file_bytes   = path.stat().st_size
            header_bytes = path.read_bytes()[:200].count(b"\n")
            # bytes por fila aproximado
            sample_bytes_per_row = file_bytes / expected_rows if expected_rows > 0 else 1
            warnings.append(f"n={n_expected}: sólo primeras 1000/{expected_rows} filas cargadas para validación rápida")
        else:
            data = np.genfromtxt(path, delimiter=",")
            expected_rows = None
    except Exception as exc:
        return dict(name=name, n=n_expected, rows=None, cols=None,
                    ok=False, errors=[f"Error leyendo CSV: {exc}"])

    if data.ndim == 1:
        data = data.reshape(1, -1)
    rows, cols = data.shape

    # ── Validar dimensiones ───────────────────────────────────────────────────
    if n_expected is not None:
        if cols != n_expected:
            errors.append(f"Columnas={cols}, esperado n={n_expected}")
        exp_rows = 2 ** n_expected
        if expected_rows is None and rows != exp_rows:
            errors.append(f"Filas={rows}, esperado 2^{n_expected}={exp_rows}")
        elif expected_rows is not None and rows < min(1000, exp_rows):
            errors.append(f"Pocas filas cargadas ({rows}), posible archivo truncado")
    else:
        # Sin n esperado: inferir n desde columnas
        n_inferred = cols
        exp_rows = 2 ** n_inferred
        if rows != exp_rows:
            warnings.append(f"Inferido n={n_inferred} → esperado {exp_rows} filas, hay {rows}")

    # ── Validar NaN / Inf ────────────────────────────────────────────────────
    if not np.all(np.isfinite(data)):
        nan_count = np.sum(~np.isfinite(data))
        errors.append(f"Hay {nan_count} valores NaN/Inf")

    # ── Validar valores en [0, 1] ────────────────────────────────────────────
    finite_data = data[np.isfinite(data)]
    out_of_range = np.any((finite_data < -TOL) | (finite_data > 1 + TOL))
    if out_of_range:
        bad = finite_data[(finite_data < -TOL) | (finite_data > 1 + TOL)]
        errors.append(f"Valores fuera de [0,1]: {bad[:5]} ...")

    # Detectar si es TPM determinista (binaria) o probabilística
    unique_vals = np.unique(finite_data)
    is_binary = np.all((np.abs(unique_vals - 0) < TOL) | (np.abs(unique_vals - 1) < TOL))
    tpm_type = "binaria" if is_binary else "probabilistica"

    ok = len(errors) == 0
    result = dict(name=name, n=n_expected or cols, rows=rows, cols=cols,
                  ok=ok, errors=errors, warnings=warnings,
                  tpm_type=tpm_type if "tpm_type" in dir() else "unknown")
    return result


def validate_directory(samples_dir: Path, verbose: bool = True) -> list[dict]:
    csv_files = sorted(samples_dir.glob("*.csv"))
    if not csv_files:
        print(f"No se encontraron .csv en {samples_dir}")
        return []

    results = []
    max_name = max(len(f.name) for f in csv_files) + 2
    header = f"{'Archivo':<{max_name}} {'n':>3}  {'filas':>10}  {'cols':>4}  {'tipo':<14} Estado"
    print(header)
    print("-" * len(header))

    for f in csv_files:
        r = validate_file(f, verbose)
        results.append(r)
        rows_str = str(r["rows"]) if r["rows"] is not None else "?"
        estado = _ok("OK") if r["ok"] else _err("FALLA")
        tipo   = r.get("tpm_type", "?")
        print(f"{r['name']:<{max_name}} {str(r['n'] or '?'):>3}  {rows_str:>10}  {str(r['cols'] or '?'):>4}  {tipo:<14} {estado}")
        for w in r.get("warnings", []):
            print(f"  {_warn(w)}")
        for e in r["errors"]:
            print(f"  {_err(e)}")

    total  = len(results)
    passed = sum(1 for r in results if r["ok"])
    failed = total - passed
    print("-" * len(header))
    print(f"\nResumen: {passed}/{total} archivos OK", end="")
    if failed:
        print(f"  ({failed} con errores)")
    else:
        print(f"  (Todos validos)")
    return results


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Validador de TPMs para GeoMIP")
    parser.add_argument("--dir",  default=str(DEFAULT_SAMPLES), help="Directorio de muestras")
    parser.add_argument("--file", default=None, help="Validar un solo archivo CSV")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if args.file:
        path = Path(args.file)
        if not path.is_absolute():
            path = Path(args.dir) / path
        r = validate_file(path, verbose=args.verbose)
        estado = _ok("OK") if r["ok"] else _err("FALLA")
        print(f"{r['name']}: n={r['n']}, rows={r['rows']}, cols={r['cols']} — {estado}")
        for e in r["errors"]:
            print(f"  {_err(e)}")
        sys.exit(0 if r["ok"] else 1)
    else:
        results = validate_directory(Path(args.dir), verbose=args.verbose)
        if not results:
            sys.exit(1)
        all_ok = all(r["ok"] for r in results)
        sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
