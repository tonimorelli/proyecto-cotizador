"""Lectura de distribuciones agregadas y construccion de cruces inferidos.

Referencia: docs/handoff_v0.md, secciones 6.8, 6.9 y 6.10.

Una licitacion puede llegar sin padron individual: cantidades por rango etario
y plan en una tabla, y provincia en otra. Estas tablas son exports de tabla
dinamica, con bloques de segmento uno al lado del otro y subtotales por
subpoblacion intercalados entre las filas de datos.

El cruce no se hace por independencia total cuando hay una dimension
compartida. Aca la comparten: ambas tablas abren por plan, asi que la
provincia se cruza DENTRO de cada plan y el supuesto de independencia queda
restringido a lo que efectivamente no se observo.
"""
from __future__ import annotations

import re
from collections import defaultdict

# "0 A 18", "19 a 27", "36-50"
_RANGO_CERRADO = re.compile(r"^\s*(\d{1,3})\s*(?:A|a|-|—)\s*(\d{1,3})\s*$")
# "65 +", "65+", "65 y mas"
_RANGO_ABIERTO = re.compile(r"^\s*(\d{1,3})\s*(?:\+|y\s*m[aá]s)\s*$", re.I)

_TOTALES = {"total", "total general", "totales", "suma", "etiquetas de fila"}


def interpretar_rango(texto):
    """Devuelve (desde, hasta) de una etiqueta de rango. hasta=None si es abierto."""
    if texto is None:
        return None
    s = str(texto).strip()
    m = _RANGO_CERRADO.match(s)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = _RANGO_ABIERTO.match(s)
    if m:
        return int(m.group(1)), None
    return None


def _es_total(texto) -> bool:
    return str(texto or "").strip().lower() in _TOTALES


def _bloques_de_columnas(filas, fila_enc):
    """Mapea cada columna de plan a su bloque de segmento.

    La fila de encabezado trae los planes repetidos por bloque; la fila de
    arriba trae el nombre del segmento sobre la primera columna de su bloque.
    Devuelve {columna: (segmento, plan)}.
    """
    encabezado = filas[fila_enc]
    superior = filas[fila_enc - 1] if fila_enc > 0 else [None] * len(encabezado)

    segmentos = {}
    for c, v in enumerate(superior):
        if v is not None and str(v).strip():
            segmentos[c] = str(v).strip()

    columnas, segmento_actual = {}, None
    for c, v in enumerate(encabezado):
        if c in segmentos:
            segmento_actual = segmentos[c]
        etiqueta = str(v).strip() if v is not None else ""
        if not etiqueta or _es_total(etiqueta):
            continue
        if segmento_actual is None:
            continue
        columnas[c] = (segmento_actual, etiqueta)
    return columnas


def leer_cruzada_edad_plan(ws) -> tuple:
    """Lee una tabla cruzada de rango etario por plan, con subpoblaciones.

    Devuelve ({(subpoblacion, segmento, (desde, hasta), plan): cantidad},
              reporte).
    """
    filas = [list(r) for r in ws.iter_rows(values_only=True)]

    def _no_numericas(fila):
        n = 0
        for c in fila:
            if c is None or not str(c).strip():
                continue
            try:
                float(c)
            except (TypeError, ValueError):
                n += 1
        return n

    # Primera fila que trae un rango etario: ahi empiezan los datos.
    primera_dato = next(
        (i for i, f in enumerate(filas)
         if any(interpretar_rango(c) for c in f)), None)
    if primera_dato is None:
        return {}, {"error": "no se encontro ninguna fila de rango etario"}

    # El encabezado de planes es la ultima fila de rotulos antes de los datos.
    # Arriba de ella esta la fila de segmentos.
    fila_enc = next((i for i in range(primera_dato - 1, 0, -1)
                     if _no_numericas(filas[i]) >= 2), None)
    if fila_enc is None:
        return {}, {"error": "no se encontro la fila de encabezado de planes"}

    columnas = _bloques_de_columnas(filas, fila_enc)
    if not columnas:
        return {}, {"error": "no se identificaron columnas de plan"}

    col_etiqueta = min(
        (c for c in range(max(len(f) for f in filas))
         if any(interpretar_rango(f[c]) for f in filas[fila_enc + 1:] if c < len(f))),
        default=None)
    if col_etiqueta is None:
        return {}, {"error": "no se encontro la columna de rangos etarios"}

    datos = defaultdict(float)
    subpoblacion, subpoblaciones, rangos, ignoradas = None, [], set(), []
    for fila in filas[fila_enc + 1:]:
        if col_etiqueta >= len(fila):
            continue
        etiqueta = fila[col_etiqueta]
        if etiqueta is None or not str(etiqueta).strip():
            continue
        rango = interpretar_rango(etiqueta)
        if rango is None:
            if _es_total(etiqueta):
                ignoradas.append(str(etiqueta).strip())
                continue
            subpoblacion = str(etiqueta).strip()
            if subpoblacion not in subpoblaciones:
                subpoblaciones.append(subpoblacion)
            continue
        if subpoblacion is None:
            ignoradas.append(f"{etiqueta} (antes de cualquier subpoblacion)")
            continue
        rangos.add(rango)
        for c, (segmento, plan) in columnas.items():
            if c >= len(fila) or fila[c] in (None, ""):
                continue
            try:
                cantidad = float(fila[c])
            except (TypeError, ValueError):
                continue
            if cantidad:
                datos[(subpoblacion, segmento, rango, plan)] += cantidad

    return dict(datos), {
        "subpoblaciones": subpoblaciones,
        "segmentos": sorted({s for s, _ in columnas.values()}),
        "planes": sorted({p for _, p in columnas.values()}),
        "rangos": sorted(rangos, key=lambda r: r[0]),
        "filas_de_total_ignoradas": ignoradas,
        "total": sum(datos.values()),
    }


def leer_cruzada_provincia_plan(ws, subpoblaciones) -> tuple:
    """Lee bloques de provincia por plan, uno por subpoblacion, lado a lado.

    Cada bloque termina con una fila cuyo rotulo es el nombre de la
    subpoblacion y cuyos valores son el total del bloque.
    """
    filas = [list(r) for r in ws.iter_rows(values_only=True)]
    ancho = max((len(f) for f in filas), default=0)
    esperadas = {str(s).strip().lower() for s in subpoblaciones}

    # Columnas rotulo: las que contienen el nombre de alguna subpoblacion.
    columnas_rotulo = []
    for c in range(ancho):
        for f in filas:
            if c < len(f) and f[c] is not None and \
                    str(f[c]).strip().lower() in esperadas:
                columnas_rotulo.append(c)
                break

    datos = defaultdict(float)
    reporte = {"bloques": [], "sin_bloque": []}
    for col in columnas_rotulo:
        fila_enc = None
        for i, f in enumerate(filas):
            if col < len(f) and f[col] is not None and \
                    _es_total(str(f[col]).strip()):
                fila_enc = i
                break
        if fila_enc is None:
            continue
        planes = {}
        for c in range(col + 1, ancho):
            v = filas[fila_enc][c] if c < len(filas[fila_enc]) else None
            etiqueta = str(v).strip() if v is not None else ""
            if not etiqueta:
                break
            if _es_total(etiqueta) or etiqueta.lower() == "total":
                break
            planes[c] = etiqueta
        sub_bloque, n = None, 0
        for f in filas[fila_enc + 1:]:
            if col >= len(f) or f[col] is None or not str(f[col]).strip():
                continue
            rotulo = str(f[col]).strip()
            if rotulo.lower() in esperadas:
                sub_bloque = rotulo
                break
        if sub_bloque is None:
            continue
        for f in filas[fila_enc + 1:]:
            if col >= len(f) or f[col] is None or not str(f[col]).strip():
                continue
            rotulo = str(f[col]).strip()
            if rotulo.lower() in esperadas or _es_total(rotulo):
                continue
            for c, plan in planes.items():
                if c >= len(f) or f[c] in (None, ""):
                    continue
                try:
                    cantidad = float(f[c])
                except (TypeError, ValueError):
                    continue
                if cantidad:
                    datos[(sub_bloque, rotulo, plan)] += cantidad
                    n += 1
        reporte["bloques"].append(
            {"subpoblacion": sub_bloque, "columna_rotulo": col,
             "planes": sorted(planes.values()), "celdas": n,
             "total": sum(v for (s, _, _), v in datos.items() if s == sub_bloque)})
    return dict(datos), reporte


def distribucion_provincial_por_plan(provincia_plan) -> dict:
    """p(provincia | subpoblacion, plan) desde la tabla observada.

    Devuelve {(subpoblacion, plan): {provincia: proporcion}}. Es la base del
    cruce condicionado: la provincia se reparte dentro de cada plan, no por
    independencia total.
    """
    por_clave = defaultdict(dict)
    for (sub, provincia, plan), cantidad in provincia_plan.items():
        por_clave[(sub, plan)][provincia] = \
            por_clave[(sub, plan)].get(provincia, 0.0) + cantidad
    salida = {}
    for clave, provincias in por_clave.items():
        total = sum(provincias.values())
        if total > 0:
            salida[clave] = {p: v / total for p, v in provincias.items()}
    return salida


def distribucion_provincial_por_subpoblacion(provincia_plan) -> dict:
    """p(provincia | subpoblacion), marginando el plan.

    Respaldo para cuando un plan no tiene provincias observadas.
    """
    por_sub = defaultdict(dict)
    for (sub, provincia, plan), cantidad in provincia_plan.items():
        por_sub[sub][provincia] = por_sub[sub].get(provincia, 0.0) + cantidad
    salida = {}
    for sub, provincias in por_sub.items():
        total = sum(provincias.values())
        if total > 0:
            salida[sub] = {p: v / total for p, v in provincias.items()}
    return salida


def construir_cartera(edad_plan, provincia_plan, pesos, homologar_provincia,
                      fuente_distingue_amba) -> tuple:
    """Cruza la distribucion etaria con la provincial y reparte a edad entera.

    El cruce es CONDICIONADO al plan, que es la dimension que ambas tablas
    comparten (6.8). La distribucion provincial se observo solo sobre
    titulares, asi que aplicarla a los familiares es la regla 6.9: se supone
    que el grupo familiar reside donde reside el titular.

    Devuelve (filas, reporte). Las filas son (subpoblacion, edad, provincia,
    plan_original, cantidad).
    """
    from .referencia import distribuir_rango

    por_plan = distribucion_provincial_por_plan(provincia_plan)
    por_sub = distribucion_provincial_por_subpoblacion(provincia_plan)

    provincias_por_sub = defaultdict(set)
    for (sub, provincia, _plan) in provincia_plan:
        provincias_por_sub[sub].add(provincia)
    distingue = {sub: fuente_distingue_amba(ps)
                 for sub, ps in provincias_por_sub.items()}

    homologadas, no_homologables = {}, defaultdict(float)
    for sub, provincias in provincias_por_sub.items():
        for p_orig in provincias:
            homologadas[(sub, p_orig)] = homologar_provincia(
                p_orig, fuente_distingue_amba=distingue.get(sub, False))

    filas = defaultdict(float)
    reporte = {"cruces_condicionados": 0, "cruces_por_marginal": 0,
               "segmentos_por_regla_6_9": set(), "sin_provincia": 0.0,
               "homologacion": {}, "rangos_distribuidos": 0}

    for (sub, segmento, rango, plan), cantidad in edad_plan.items():
        dist = por_plan.get((sub, plan))
        if dist:
            reporte["cruces_condicionados"] += 1
        else:
            dist = por_sub.get(sub)
            if dist:
                reporte["cruces_por_marginal"] += 1
        if not dist:
            reporte["sin_provincia"] += cantidad
            continue
        if segmento.strip().upper() not in ("TITULAR", "TITULARES"):
            reporte["segmentos_por_regla_6_9"].add(segmento)

        desde, hasta = rango
        reparto = distribuir_rango(pesos, desde, hasta, cantidad)
        reporte["rangos_distribuidos"] += 1
        for p_orig, q in dist.items():
            destino = homologadas.get((sub, p_orig), "sin dato")
            if destino == "sin dato":
                no_homologables[p_orig] += cantidad * q
            for edad, c in reparto.items():
                filas[(sub, edad, destino, plan)] += c * q

    reporte["segmentos_por_regla_6_9"] = sorted(reporte["segmentos_por_regla_6_9"])
    reporte["provincias_no_homologables"] = dict(no_homologables)
    reporte["homologacion"] = {
        f"{sub} | {orig}": dest for (sub, orig), dest in sorted(homologadas.items())}
    reporte["distingue_amba"] = distingue
    reporte["total"] = sum(filas.values())
    return [(sub, edad, prov, plan, c)
            for (sub, edad, prov, plan), c in sorted(
                filas.items(), key=lambda x: (x[0][0], x[0][1], x[0][2], x[0][3]))], reporte
