"""Construccion de carteras, escenarios de situ y controles de cierre.

Referencia: docs/handoff_v0.md, secciones 6.11, 6.12 y 7.

La cartera se modela con edad entera. La agregacion a grupo etario ocurre solo
al escribir el Excel, contra las etiquetas de la plantilla aprobada.

Una cartera nunca mezcla alternativas de plan: cada alternativa es un escenario
de cotizacion distinto y sumarlas produce un total sin sentido. La clave de
toda fila lleva subpoblacion y alternativa para que el doble conteo sea
imposible por construccion.
"""
from __future__ import annotations

from collections import defaultdict

from .catalogos import ETIQUETA_GRUPO, ETIQUETA_PLAN, PLANES, grupo_etario

# La tabla de escenarios se aplica segun sus propias etiquetas de grupo, como
# supuesto adoptado. Su procedencia no esta verificada: el handoff 11 deja
# constancia de que no se reproduce desde la referencia corporativa. No se
# afirma nada sobre como fueron calculadas sus proporciones.

TOLERANCIA = 1e-6

ALTERNATIVA_OBSERVADA = "observada"


class ErrorDeCierre(RuntimeError):
    """Una cantidad no se conservo. Es error de software, no decision humana."""


class FilaBase:
    """Fila de cartera antes de partir por situ."""

    __slots__ = ("subpoblacion", "alternativa", "edad", "provincia", "plan",
                 "origen_plan", "cantidad")

    def __init__(self, subpoblacion, alternativa, edad, provincia, plan,
                 origen_plan, cantidad):
        self.subpoblacion = subpoblacion
        self.alternativa = alternativa
        self.edad = edad
        self.provincia = provincia
        self.plan = plan
        self.origen_plan = origen_plan
        self.cantidad = cantidad

    @property
    def clave(self):
        return (self.subpoblacion, self.alternativa, self.edad,
                self.provincia, self.plan)


def expandir_planes(filas) -> list:
    """Expande a las nueve alternativas de cotizacion lo que no tiene plan.

    `filas` son tuplas (subpoblacion, edad, provincia, plan_o_None, cantidad).

    Una fila con plan homologado observado se conserva tal cual y aparece en
    TODAS las alternativas: es poblacion real, no un escenario. Una fila sin
    plan homologable se repite una vez por alternativa con el plan de esa
    alternativa. Asi cada alternativa k es una cartera completa y coherente:
    la porcion observada mas la porcion desconocida cotizada al plan k.

    Cuando ninguna fila tiene plan observado, las nueve alternativas son las
    nueve carteras del handoff 6.6. Cuando todas lo tienen, se emite una sola
    alternativa `observada` y no hay expansion.
    """
    hay_sin_plan = any(plan is None for _, _, _, plan, _ in filas)
    if not hay_sin_plan:
        return [FilaBase(sub, ALTERNATIVA_OBSERVADA, edad, prov, plan,
                         "observado", cant)
                for sub, edad, prov, plan, cant in filas]

    salida = []
    for alternativa in PLANES:
        for sub, edad, prov, plan, cant in filas:
            if plan is None:
                salida.append(FilaBase(sub, alternativa, edad, prov,
                                       alternativa, "alternativa", cant))
            else:
                salida.append(FilaBase(sub, alternativa, edad, prov, plan,
                                       "observado", cant))
    return salida


def totales_por_alternativa(filas) -> dict:
    """{(subpoblacion, alternativa): cantidad}. Nunca suma entre alternativas."""
    tot = defaultdict(float)
    for f in filas:
        tot[(f.subpoblacion, f.alternativa)] += f.cantidad
    return dict(tot)


def aplicar_escenario(filas, tabla, escenario: str) -> list:
    """Parte cada fila en situ 1 y situ 0 con la proporcion de su grupo etario.

    Devuelve tuplas (subpoblacion, alternativa, edad, provincia, plan,
    origen_plan, situ, cantidad). No redondea.
    """
    if escenario not in ("optimista", "pesimista"):
        raise ValueError(f"escenario desconocido: {escenario!r}")
    salida = []
    for f in filas:
        p = tabla[grupo_etario(f.edad)][escenario]
        salida.append((f.subpoblacion, f.alternativa, f.edad, f.provincia,
                       f.plan, f.origen_plan, 1, f.cantidad * p))
        salida.append((f.subpoblacion, f.alternativa, f.edad, f.provincia,
                       f.plan, f.origen_plan, 0, f.cantidad * (1.0 - p)))
    return salida


def _cierra(obtenido: float, esperado: float) -> bool:
    if esperado == 0:
        return abs(obtenido) <= TOLERANCIA
    return abs(obtenido - esperado) / abs(esperado) <= TOLERANCIA


def controlar_cierre(filas_base, filas_escenario, escenario: str) -> dict:
    """Control estricto por subpoblacion y alternativa. Falla ruidosamente.

    Verifica tres cosas: que el total de cada alternativa se conserve al
    aplicar el escenario, que situ 0 mas situ 1 reproduzca la cantidad previa
    a la particion en cada fila, y que todas las alternativas cubran la misma
    poblacion.

    El `total_licitacion` que devuelve es la suma de las subpoblaciones dentro
    de una alternativa. No es la suma de las alternativas y no debe usarse
    como si lo fuera.
    """
    esperado = totales_por_alternativa(filas_base)

    obtenido = defaultdict(float)
    for sub, alt, _, _, _, _, _, cant in filas_escenario:
        obtenido[(sub, alt)] += cant

    for clave, esp in esperado.items():
        obt = obtenido.get(clave, 0.0)
        if not _cierra(obt, esp):
            raise ErrorDeCierre(
                f"escenario {escenario}: la subpoblacion {clave[0]!r} "
                f"alternativa {clave[1]!r} no cierra. esperado={esp!r} "
                f"obtenido={obt!r} desvio_relativo={abs(obt - esp) / esp:.3e}"
            )

    por_fila = defaultdict(float)
    for sub, alt, edad, prov, plan, _, _, cant in filas_escenario:
        por_fila[(sub, alt, edad, prov, plan)] += cant
    # Varias filas base pueden compartir clave (una persona por fila, por
    # ejemplo). Se comparan agregados contra agregados.
    esperado_por_clave = defaultdict(float)
    for f in filas_base:
        esperado_por_clave[f.clave] += f.cantidad
    for clave, esp in esperado_por_clave.items():
        obt = por_fila.get(clave, 0.0)
        if not _cierra(obt, esp):
            raise ErrorDeCierre(
                f"escenario {escenario}: situ 0 mas situ 1 no reproduce la "
                f"cantidad previa en {clave!r}: {obt!r} vs {esp!r}"
            )

    # Total de la licitacion = suma de SUBPOBLACIONES dentro de una alternativa.
    # Nunca suma entre alternativas: nueve alternativas de 100 personas son la
    # misma poblacion de 100 cotizada de nueve formas, no 900 personas.
    por_alternativa = defaultdict(float)
    for (_, alt), v in esperado.items():
        por_alternativa[alt] += v

    # Toda alternativa cubre la misma poblacion, asi que sus totales tienen que
    # coincidir. Una diferencia es error de construccion, no dato.
    valores = list(por_alternativa.values())
    if valores and not all(_cierra(v, valores[0]) for v in valores):
        raise ErrorDeCierre(
            f"escenario {escenario}: las alternativas cubren poblaciones "
            f"distintas, y deberian cubrir la misma: {dict(por_alternativa)!r}"
        )

    return {
        "escenario": escenario,
        "alternativas_controladas": len(esperado),
        "total_licitacion": valores[0] if valores else 0.0,
        "total_por_alternativa": dict(por_alternativa),
        "totales_por_subpoblacion_y_alternativa": {
            f"{s} | {a}": v for (s, a), v in sorted(esperado.items())
        },
    }


def agregar_para_salida(filas_escenario) -> dict:
    """Agrega a la grilla de la plantilla, conservando el eje de alternativa.

    Devuelve {(subpoblacion, alternativa): {(etiqueta_grupo, provincia,
    etiqueta_plan, situ): cantidad}}. La edad entera colapsa recien aca.
    """
    bloques = defaultdict(lambda: defaultdict(float))
    for sub, alt, edad, prov, plan, _, situ, cant in filas_escenario:
        clave = (ETIQUETA_GRUPO[grupo_etario(edad)], prov,
                 ETIQUETA_PLAN[plan], situ)
        bloques[(sub, alt)][clave] += cant
    return {k: dict(v) for k, v in bloques.items()}


def comparar_escenarios(bloques_a, bloques_b, nombre_a="optimista",
                        nombre_b="pesimista") -> dict:
    """Compara dos escenarios combinacion por combinacion, sumando situ.

    Un total general igual puede esconder combinaciones distintas que se
    compensan. Los escenarios difieren unicamente en el eje situ, asi que al
    sumar situ 0 mas situ 1 cada combinacion tiene que dar lo mismo en ambos.

    Devuelve el reporte. Falla si difieren.
    """
    def _sumar_situ(bloques):
        agregado = defaultdict(float)
        for (sub, alt), celdas in bloques.items():
            for (grupo, provincia, plan, _situ), cantidad in celdas.items():
                agregado[(sub, alt, grupo, provincia, plan)] += cantidad
        return dict(agregado)

    a, b = _sumar_situ(bloques_a), _sumar_situ(bloques_b)

    solo_a = sorted(set(a) - set(b))
    solo_b = sorted(set(b) - set(a))
    if solo_a or solo_b:
        raise ErrorDeCierre(
            f"{nombre_a} y {nombre_b} no cubren las mismas combinaciones. "
            f"solo en {nombre_a}: {solo_a[:5]} ({len(solo_a)}); "
            f"solo en {nombre_b}: {solo_b[:5]} ({len(solo_b)})"
        )

    discrepancias = [
        (clave, a[clave], b[clave]) for clave in a
        if not _cierra(b[clave], a[clave])
    ]
    if discrepancias:
        raise ErrorDeCierre(
            f"{nombre_a} y {nombre_b} difieren en {len(discrepancias)} "
            f"combinaciones al sumar situ. Ejemplos: {discrepancias[:3]}"
        )

    return {
        "combinaciones_comparadas": len(a),
        "maxima_diferencia_absoluta": max(
            (abs(a[k] - b[k]) for k in a), default=0.0),
        "nota": (f"{nombre_a} y {nombre_b} cubren las mismas combinaciones de "
                 f"(subpoblacion, alternativa, grupo etario, provincia, plan) "
                 f"con la misma cantidad al sumar situ 0 y situ 1."),
    }
