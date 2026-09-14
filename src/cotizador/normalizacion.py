"""Propagacion dentro del grupo familiar y verificaciones previas al cruce.

Referencia: docs/handoff_v0.md, secciones 6.7, 6.9 y 6.10.
"""
from __future__ import annotations

from collections import defaultdict


def propagar_en_grupo(registros, campos) -> dict:
    """Propaga atributos declarados una sola vez por grupo familiar.

    `registros` son dicts con al menos la clave `grupo`. Las fuentes
    individuales declaran provincia o categoria en la fila del titular y dejan
    vacias las de conyuge e hijos. Eso es estructura jerarquica, no informacion
    faltante: el atributo se propaga por el identificador del grupo.

    Propaga solo cuando el grupo tiene UN unico valor no vacio. Si tiene dos
    distintos no inventa nada: lo registra como conflicto y deja el campo
    vacio. Devuelve el reporte para declarar en Supuestos.
    """
    por_grupo = defaultdict(list)
    for r in registros:
        por_grupo[r["grupo"]].append(r)

    reporte = {c: {"filas_completadas": 0, "grupos_sin_valor": 0,
                   "grupos_en_conflicto": 0, "conflictos": []} for c in campos}

    for campo in campos:
        for grupo, filas in por_grupo.items():
            valores = {f[campo] for f in filas if f.get(campo)}
            if not valores:
                reporte[campo]["grupos_sin_valor"] += 1
                continue
            if len(valores) > 1:
                reporte[campo]["grupos_en_conflicto"] += 1
                if len(reporte[campo]["conflictos"]) < 20:
                    reporte[campo]["conflictos"].append(
                        {"grupo": grupo, "valores": sorted(valores)})
                continue
            unico = valores.pop()
            for f in filas:
                if not f.get(campo):
                    f[campo] = unico
                    reporte[campo]["filas_completadas"] += 1
    return reporte


def verificar_doble_conteo(registros, campo_cantidad) -> dict:
    """Compara sumar la columna de capitas contra contar filas.

    Handoff 6.7: son dos caminos al mismo total. Se usa uno y se verifica
    contra el otro. Nunca se suman entre si.
    """
    suma = sum(float(r[campo_cantidad]) for r in registros
               if r.get(campo_cantidad) not in (None, ""))
    filas = len(registros)
    return {
        "suma_columna_capitas": suma,
        "conteo_de_filas": filas,
        "coinciden": abs(suma - filas) < 1e-9,
        "camino_usado": "conteo de filas",
        "nota": ("La columna de capitas y el conteo de filas son dos caminos "
                 "al mismo total. Se usa el conteo y se verifica contra la "
                 "columna. No se suman entre si."),
    }


def verificar_antes_de_cruzar(distribuciones) -> dict:
    """Chequea poblacion, periodo y cobertura antes de cruzar o reescalar.

    `distribuciones` es una lista de dicts con `id_fuente`, `subpoblacion`,
    `periodo`, `cobertura` y `total`.

    Reescalar dos distribuciones que miden poblaciones distintas, momentos
    distintos o coberturas distintas convierte una diferencia real en un factor
    de ajuste silencioso. Antes de aplicar 6.10 hay que descartar esos tres
    casos. Este control no decide: informa y marca revision humana.
    """
    hallazgos, apto = [], True

    subpoblaciones = {d["subpoblacion"] for d in distribuciones}
    if len(subpoblaciones) > 1:
        apto = False
        hallazgos.append(
            f"cubren subpoblaciones distintas ({sorted(subpoblaciones)}): "
            "no se reescalan entre si, cada una cierra por separado")

    periodos = {d.get("periodo") for d in distribuciones}
    if len(periodos) > 1:
        apto = False
        hallazgos.append(
            f"periodos distintos ({sorted(str(p) for p in periodos)}): la "
            "diferencia de totales puede ser real y no un error de lectura")
    if None in periodos or "" in periodos:
        apto = False
        hallazgos.append(
            "al menos una distribucion no declara periodo: no se puede "
            "descartar que la diferencia de totales sea real")

    coberturas = {d.get("cobertura") for d in distribuciones}
    if len(coberturas) > 1:
        apto = False
        hallazgos.append(
            f"coberturas distintas ({sorted(str(c) for c in coberturas)}): "
            "corresponde la regla 6.9, no el reescalado de 6.10")

    return {
        "distribuciones": len(distribuciones),
        "apto_para_reescalar": apto and len(distribuciones) > 1,
        "hallazgos": hallazgos,
        "requiere_revision_humana": not apto and len(distribuciones) > 1,
    }
