"""Catalogos objetivo y normalizacion de denominaciones.

Referencia: docs/handoff_v0.md, secciones 4.3, 4.4, 4.5 y 6.5.
"""
from __future__ import annotations

import re
import unicodedata

EDAD_MIN = 0
EDAD_MAX = 100

PROVINCIAS = (
    "BUENOS AIRES", "AMBA", "CORDOBA", "SANTA FE", "CATAMARCA", "CHACO",
    "CORRIENTES", "ENTRE RIOS", "FORMOSA", "JUJUY", "LA PAMPA", "LA RIOJA",
    "MENDOZA", "MISIONES", "SAN JUAN", "SAN LUIS", "SANTIAGO DEL ESTERO",
    "TUCUMAN", "CHUBUT", "NEUQUEN", "RIO NEGRO", "SALTA", "SANTA CRUZ",
    "TIERRA DEL FUEGO",
)

PLANES = ("S1", "SMG02", "S2", "SMG20", "SMG30", "SMG40", "SMG50", "SMG60", "SMG70")

SIN_DATO = "sin dato"

# Dos agrupamientos de edad distintos y deliberados.
#
# _TRAMOS_COMUNES: identicos en ambos, del grupo 03 en adelante. Solo los dos
# primeros tramos difieren, y la unica edad que cambia de grupo es la 1.
_TRAMOS_COMUNES = (
    ("03", 6, 10), ("04", 11, 15), ("05", 16, 20), ("06", 21, 25),
    ("07", 26, 30), ("08", 31, 35), ("09", 36, 40), ("10", 41, 45),
    ("11", 46, 50), ("12", 51, 55), ("13", 56, 60), ("14", 61, 65),
    ("15", 66, 70), ("16", 71, 75), ("17", 76, 80), ("18", 81, 85),
    ("19", 86, 90), ("20", 91, 95), ("21", 96, 10**6),
)

# AGRUPAMIENTO DE SALIDA. Las etiquetas de la plantilla aprobada, interpretadas
# literalmente: "01) 0 a 1" contiene las edades 0 y 1. Es el que se usa para
# buscar la proporcion de situ y para escribir la columna `edad` del Excel.
_LIMITES_SALIDA = (("01", 0, 1), ("02", 2, 5)) + _TRAMOS_COMUNES

# AGRUPAMIENTO DE LA REFERENCIA. El que la referencia corporativa usa por
# dentro: asigna la edad 0 al grupo 01 y las edades 1 a 5 al grupo 02, en
# contra de sus propias etiquetas. NO se usa para calcular nada. Su unico uso
# es verificar que el archivo de referencia sea el esperado.
_LIMITES_REFERENCIA = (("01", 0, 0), ("02", 1, 5)) + _TRAMOS_COMUNES

# Etiquetas textuales de la plantilla aprobada
# (Referencia/referencia_tabla_a_completar.xlsx). Se escriben tal cual.
ETIQUETA_GRUPO = {
    "01": "01) 0 a 1", "02": "02) 2 a 5", "03": "03) 6 a 10",
    "04": "04) 11 a 15", "05": "05) 16 a 20", "06": "06) 21 a 25",
    "07": "07) 26 a 30", "08": "08) 31 a 35", "09": "09) 36 a 40",
    "10": "10) 41 a 45", "11": "11) 46 a 50", "12": "12) 51 a 55",
    "13": "13) 56 a 60", "14": "14) 61 a 65", "15": "15) 66 a 70",
    "16": "16) 71 a 75", "17": "17) 76 a 80", "18": "18) 81 a 85",
    "19": "19) 86 a 90", "20": "20) 91 a 95", "21": "21) +",
}

ETIQUETA_PLAN = {
    "S1": "01) S1", "SMG02": "02) SMG02", "S2": "03) S2",
    "SMG20": "04) SMG20", "SMG30": "05) SMG30", "SMG40": "06) SMG40",
    "SMG50": "07) SMG50", "SMG60": "08) SMG60", "SMG70": "09) SMG70",
}

GRUPOS_ETARIOS = tuple(codigo for codigo, _, _ in _LIMITES_SALIDA)


def normalizar(texto) -> str:
    """Minusculas, sin acentos, sin espacios repetidos. Para comparar denominaciones."""
    if texto is None:
        return ""
    s = unicodedata.normalize("NFKD", str(texto))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


def grupo_etario(edad: int) -> str:
    """Grupo etario de salida de una edad entera. Etiquetas literales.

    La edad 1 cae en el grupo 01, como dice la etiqueta "01) 0 a 1".
    """
    for codigo, desde, hasta in _LIMITES_SALIDA:
        if desde <= edad <= hasta:
            return codigo
    raise ValueError(f"edad fuera de rango: {edad!r}")


def grupo_referencia(edad: int) -> str:
    """Grupo etario segun el agrupamiento interno de la referencia corporativa.

    Difiere de grupo_etario solo en la edad 1. Uso exclusivo: verificar que el
    archivo de referencia sea el esperado. No interviene en ningun calculo.
    """
    for codigo, desde, hasta in _LIMITES_REFERENCIA:
        if desde <= edad <= hasta:
            return codigo
    raise ValueError(f"edad fuera de rango: {edad!r}")


def codigo_de_etiqueta(etiqueta) -> str:
    """Extrae el codigo de grupo de una etiqueta de la referencia o de la tabla ST.

    Tolera relleno y espacios internos multiples: '01)   0 a 1    ' y '01) 0 a 1'
    devuelven ambos '01'.
    """
    m = re.match(r"\s*(\d{2})\)", str(etiqueta))
    if not m:
        raise ValueError(f"etiqueta de grupo etario no reconocida: {etiqueta!r}")
    return m.group(1)


# --- Provincia -------------------------------------------------------------

# Denominaciones que siempre resuelven al area metropolitana.
_AMBA = {
    "capital federal", "caba", "ciudad autonoma de buenos aires",
    "ciudad de buenos aires", "c.a.b.a.", "amba", "gba",
    "buenos aires-gba", "buenos aires gba", "gran buenos aires",
}

# Denominaciones que resuelven a una provincia del catalogo.
_ALIAS = {
    "cordoba": "CORDOBA",
    "santa fe": "SANTA FE",
    "entre rios": "ENTRE RIOS",
    "rio negro": "RIO NEGRO",
    "neuquen": "NEUQUEN",
    "tucuman": "TUCUMAN",
    "santiago del estero": "SANTIAGO DEL ESTERO",
    "tierra del fuego": "TIERRA DEL FUEGO",
}

_BUENOS_AIRES = {"buenos aires", "pcia de buenos aires", "provincia de buenos aires"}


def homologar_provincia(valor, *, fuente_distingue_amba: bool = False,
                        localidad_es_amba: bool | None = None) -> str:
    """Homologa una denominacion de provincia al catalogo objetivo.

    fuente_distingue_amba: la fuente separa en otras filas el AMBA o el GBA, asi que
        'Buenos Aires' a secas significa el interior de la provincia.
    localidad_es_amba: resultado del catalogo de partidos, cuando hay localidad.
        Tiene prioridad sobre la heuristica anterior.

    Devuelve SIN_DATO si no hay match. Nunca inventa un mapeo.
    """
    n = normalizar(valor)
    if not n:
        return SIN_DATO
    if n in _AMBA:
        return "AMBA"
    if n in _BUENOS_AIRES:
        if localidad_es_amba is not None:
            return "AMBA" if localidad_es_amba else "BUENOS AIRES"
        return "BUENOS AIRES" if fuente_distingue_amba else "AMBA"
    if n in _ALIAS:
        return _ALIAS[n]
    for p in PROVINCIAS:
        if normalizar(p) == n:
            return p
    return SIN_DATO


def homologar_plan(valor) -> str:
    """Homologa un plan al catalogo objetivo. SIN_DATO si no es homologable."""
    n = normalizar(valor).replace(" ", "")
    for p in PLANES:
        if normalizar(p).replace(" ", "") == n:
            return p
    return SIN_DATO


def fuente_distingue_amba(valores) -> bool:
    """True si la fuente nombra explicitamente el AMBA, la CABA o el GBA.

    Handoff 6.5: cuando la fuente distingue en otra fila el AMBA o el GBA,
    'Buenos Aires' a secas significa el interior de la provincia.
    """
    return any(normalizar(v) in _AMBA for v in valores if v)
