"""Validacion de particiones en resultados benchmark rapido."""
from __future__ import annotations

import re

import pandas as pd


def count_groups(s) -> int | None:
    if pd.isna(s):
        return None
    text = str(s).strip()
    if not text or text.lower().startswith("inviable"):
        return 0
    top = text.splitlines()[0]
    return len(re.findall(r"\|[^|]*\|", top))


def validate_rapido_df(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """
    Verifica que cada fila tenga exactamente k grupos en cada columna *_particion
    y que MCTS_k*_ok sea True cuando exista.
    """
    if df.empty or "#Prueba" not in df.columns:
        return True, []

    errors: list[str] = []
    part_cols = [c for c in df.columns if "particion" in c.lower()]

    for col in part_cols:
        m = re.search(r"k(\d+)", col, re.I)
        if not m:
            continue
        k = int(m.group(1))
        counts = df[col].map(count_groups)

        mas = df.loc[counts > k, "#Prueba"]
        if len(mas):
            errors.append(
                f"{col}: {len(mas)} filas con MAS de {k} grupos "
                f"(casos {sorted(mas.tolist())})"
            )

        menos = df.loc[counts < k, "#Prueba"]
        if len(menos):
            errors.append(
                f"{col}: {len(menos)} filas con MENOS de {k} grupos "
                f"(casos {sorted(menos.tolist())})"
            )

        ok_col = col.replace("particion", "ok")
        if ok_col in df.columns:
            no_conv = df.loc[df[ok_col].fillna(False) == False, "#Prueba"]
            if len(no_conv):
                errors.append(
                    f"{ok_col}: {len(no_conv)} filas sin converger "
                    f"(casos {sorted(no_conv.tolist())})"
                )

    return len(errors) == 0, errors


def report_validation(df: pd.DataFrame, label: str = "") -> bool:
    ok, errors = validate_rapido_df(df)
    prefix = f"[{label}] " if label else ""
    if ok:
        print(f"  {prefix}validacion OK ({len(df)} filas)", flush=True)
        return True
    print(f"  {prefix}VALIDACION RECHAZADA — deteniendo corrida", flush=True)
    for err in errors:
        print(f"    ! {err}", flush=True)
    return False
