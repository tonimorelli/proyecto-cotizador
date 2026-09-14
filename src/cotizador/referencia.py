"""Carga de la referencia corporativa y precomputo de la distribucion etaria.

Referencia: docs/handoff_v0.md, secciones 3.2 y 6.4.

La referencia pesa decenas de MB y una pasada completa tarda cerca de un minuto.
El precomputo la recorre una sola vez y deja un CSV chico con la distribucion de
edad dentro de cada grupo etario, ponderada por suma_contador.
"""
from __future__ import annotations

import csv
import pathlib
from collections import defaultdict

from .catalogos import EDAD_MIN, EDAD_MAX, codigo_de_etiqueta, grupo_referencia

HOJA = "Hoja1"
COL_EDAD = "edad"
COL_GRUPO = "grupo_etario"
COL_PESO = "suma_contador"


class ReferenciaInconsistente(RuntimeError):
    """La referencia no agrupa las edades como se la verifico el 2026-09-13."""


def precomputar(path_referencia, path_salida) -> dict:
    """Recorre la referencia una vez y escribe la distribucion etaria.

    Devuelve un resumen con los controles aplicados.

    Falla si la referencia dejo de agrupar las edades como catalogos.grupo_referencia
    dice que las agrupa. Eso no valida nuestro agrupamiento de salida, que es
    distinto a proposito: verifica que el archivo de entrada siga siendo el que
    se inspecciono. Un cambio ahi invalidaria los pesos precomputados.
    """
    import openpyxl

    wb = openpyxl.load_workbook(path_referencia, read_only=True, data_only=True)
    ws = wb[HOJA]
    filas = ws.iter_rows(values_only=True)
    encabezado = next(filas)
    idx = {h: i for i, h in enumerate(encabezado) if h}
    for col in (COL_EDAD, COL_GRUPO, COL_PESO):
        if col not in idx:
            raise KeyError(f"la referencia no tiene la columna {col!r}")

    peso = defaultdict(float)          # (grupo, edad) -> suma_contador
    total_leido = 0.0
    total_excluido = 0.0
    n_filas = 0
    n_sin_edad = 0
    n_sin_peso = 0
    divergencias = set()

    for fila in filas:
        n_filas += 1
        edad = fila[idx[COL_EDAD]]
        if edad is None:
            n_sin_edad += 1
            continue
        edad = int(edad)
        p = fila[idx[COL_PESO]]
        if p is None:
            n_sin_peso += 1
            p = 0
        total_leido += p

        grupo_declarado = codigo_de_etiqueta(fila[idx[COL_GRUPO]])
        if grupo_declarado != grupo_referencia(edad):
            divergencias.add((edad, grupo_declarado, grupo_referencia(edad)))

        if edad > EDAD_MAX:
            total_excluido += p
            continue
        peso[(grupo_declarado, edad)] += p

    wb.close()

    if divergencias:
        muestra = sorted(divergencias)[:5]
        raise ReferenciaInconsistente(
            "la referencia cambio su agrupamiento interno de edades respecto del "
            "verificado el 2026-09-13. Ejemplos (edad, grupo_en_el_archivo, "
            f"grupo_esperado): {muestra}"
        )

    # Normalizar a proporciones dentro de cada grupo.
    por_grupo = defaultdict(float)
    for (g, _), p in peso.items():
        por_grupo[g] += p

    path_salida = pathlib.Path(path_salida)
    path_salida.parent.mkdir(parents=True, exist_ok=True)
    with path_salida.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["grupo_etario", "edad", "suma_contador", "proporcion"])
        for (g, edad) in sorted(peso):
            p = peso[(g, edad)]
            w.writerow([g, edad, repr(p), repr(p / por_grupo[g])])

    return {
        "filas_leidas": n_filas,
        "filas_descartadas_sin_edad": n_sin_edad,
        "filas_con_peso_nulo": n_sin_peso,
        "capitas_leidas": total_leido,
        "capitas_excluidas_por_edad": total_excluido,
        "grupos": len(por_grupo),
        "edades_con_soporte": len({e for _, e in peso}),
        "salida": str(path_salida),
    }


def cargar_distribucion(path_csv) -> dict:
    """Lee el CSV precomputado. Devuelve {grupo: {edad: proporcion}}."""
    dist: dict[str, dict[int, float]] = defaultdict(dict)
    with open(path_csv, newline="", encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            dist[fila["grupo_etario"]][int(fila["edad"])] = float(fila["proporcion"])
    return dict(dist)


def soporte_muestral(path_csv) -> dict:
    """Devuelve {grupo: suma_contador} para declarar el soporte en Supuestos."""
    soporte: dict[str, float] = defaultdict(float)
    with open(path_csv, newline="", encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            soporte[fila["grupo_etario"]] += float(fila["suma_contador"])
    return dict(soporte)


class RangoSinSoporte(ValueError):
    """El rango recibido no tiene ninguna edad con peso en la referencia."""


def pesos_por_edad(path_csv) -> dict:
    """Devuelve {edad: suma_contador} absoluto, sin normalizar por grupo.

    Es el insumo de distribuir_rango. Los pesos tienen que ser absolutos y
    comparables entre grupos: un rango recibido puede cruzar los limites de
    los grupos de la referencia, y normalizar dentro de cada grupo repartiria
    mal entre ellos.
    """
    pesos: dict[int, float] = defaultdict(float)
    with open(path_csv, newline="", encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            pesos[int(fila["edad"])] += float(fila["suma_contador"])
    return dict(pesos)


def distribuir_rango(pesos: dict, desde: int, hasta, cantidad: float) -> dict:
    """Reparte `cantidad` entre las edades enteras de un rango recibido.

    Usa los pesos absolutos de la referencia renormalizados SOBRE EL RANGO, no
    sobre el grupo. `hasta` puede ser None para un tramo abierto ("65 y mas"),
    en cuyo caso se topea en EDAD_MAX.

    Devuelve {edad: cantidad}. La suma reproduce `cantidad`: el reparto
    conserva el total del rango y no se redondea.
    """
    desde = max(int(desde), EDAD_MIN)
    hasta = EDAD_MAX if hasta is None else min(int(hasta), EDAD_MAX)
    if hasta < desde:
        raise ValueError(f"rango invalido: {desde} a {hasta}")

    edades = [e for e in range(desde, hasta + 1) if pesos.get(e)]
    total = sum(pesos[e] for e in edades)
    if not edades or total <= 0:
        raise RangoSinSoporte(
            f"el rango {desde} a {hasta} no tiene soporte en la referencia"
        )
    return {e: cantidad * pesos[e] / total for e in edades}


def soporte_de_rango(pesos: dict, desde: int, hasta) -> float:
    """suma_contador que respalda un rango recibido. Se declara en Supuestos."""
    desde = max(int(desde), EDAD_MIN)
    hasta = EDAD_MAX if hasta is None else min(int(hasta), EDAD_MAX)
    return sum(pesos.get(e, 0.0) for e in range(desde, hasta + 1))
