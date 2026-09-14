"""Carga y validacion de la tabla de escenarios de situacion terapeutica.

Referencia: docs/handoff_v0.md, secciones 3.3 y 6.11.

La tabla es un insumo aprobado. Se consume como esta y no se recalcula.
Solo se valida su forma.
"""
from __future__ import annotations

from .catalogos import GRUPOS_ETARIOS, codigo_de_etiqueta

HOJA = "Hoja1"
COL_OPTIMISTA = "Optimista"
COL_PESIMISTA = "Pesimista"


class TablaEscenariosInvalida(ValueError):
    """La tabla de escenarios no cumple la validacion de forma."""


def cargar(path_tabla) -> dict:
    """Devuelve {grupo: {'optimista': p, 'pesimista': p}}.

    Valida forma: los 21 grupos presentes y sin repetir, proporciones en [0, 1]
    y optimista menor o igual que pesimista en cada grupo.
    """
    import openpyxl

    wb = openpyxl.load_workbook(path_tabla, data_only=True)
    ws = wb[HOJA]
    filas = ws.iter_rows(values_only=True)
    encabezado = next(filas)
    idx = {h: i for i, h in enumerate(encabezado) if h}
    for col in (COL_OPTIMISTA, COL_PESIMISTA):
        if col not in idx:
            raise TablaEscenariosInvalida(f"falta la columna {col!r}")

    tabla: dict[str, dict[str, float]] = {}
    for fila in filas:
        if fila[0] is None:
            continue
        grupo = codigo_de_etiqueta(fila[0])
        if grupo in tabla:
            raise TablaEscenariosInvalida(f"grupo etario repetido: {grupo}")
        tabla[grupo] = {
            "optimista": float(fila[idx[COL_OPTIMISTA]]),
            "pesimista": float(fila[idx[COL_PESIMISTA]]),
        }
    wb.close()

    faltantes = set(GRUPOS_ETARIOS) - set(tabla)
    sobrantes = set(tabla) - set(GRUPOS_ETARIOS)
    if faltantes or sobrantes:
        raise TablaEscenariosInvalida(
            f"grupos faltantes: {sorted(faltantes)}; sobrantes: {sorted(sobrantes)}"
        )

    for grupo, v in tabla.items():
        for escenario, p in v.items():
            if not 0.0 <= p <= 1.0:
                raise TablaEscenariosInvalida(
                    f"proporcion fuera de [0, 1] en grupo {grupo}, {escenario}: {p}"
                )
        if v["optimista"] > v["pesimista"]:
            raise TablaEscenariosInvalida(
                f"optimista mayor que pesimista en el grupo {grupo}: "
                f"{v['optimista']} > {v['pesimista']}"
            )
    return tabla


def proporcion(tabla: dict, edad: int, escenario: str) -> float:
    """Proporcion de situ 1 para una edad entera y un escenario."""
    from .catalogos import grupo_etario

    if escenario not in ("optimista", "pesimista"):
        raise ValueError(f"escenario desconocido: {escenario!r}")
    return tabla[grupo_etario(edad)][escenario]
