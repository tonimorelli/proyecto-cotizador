"""Inventario de la carpeta, lectores por formato y tabla de fuentes.

Referencia: docs/handoff_v0.md, secciones 3.1, 6.1 y 7.1.

Ninguna fuente se declara completa sin leerla. Todo archivo que no se pudo
leer, o que se leyo parcialmente, queda registrado como tal en Diagnostico.
"""
from __future__ import annotations

import email
import hashlib
import pathlib
import re
import unicodedata
import warnings
from dataclasses import dataclass, field
from email import policy

warnings.filterwarnings("ignore")

# Huella de columnas del export del sistema propio. Reconocedor deterministico:
# corre antes que el agente y no depende de el. Handoff 6.1.
HUELLA_PADRON_INTERNO = frozenset(
    {"contra", "inte", "plan_codi", "megacuenta", "Capitas", "cuota_medica"}
)

def normalizar_texto(t) -> str:
    """Minusculas y sin acentos. Para buscar marcas dentro de una planilla."""
    t = unicodedata.normalize("NFKD", str(t))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip().lower()


ROLES = (
    "padron individual",
    "distribucion agregada",
    "documento original del cliente",
    "cotizacion interna posterior",
    "contexto sin datos de cartera",
)


@dataclass
class Fuente:
    """Un archivo de la carpeta, con lo que se pudo leer de el."""

    id_fuente: str
    ruta: pathlib.Path
    formato: str
    bytes: int
    sha256: str
    fecha_nombre: str | None = None
    hojas: dict = field(default_factory=dict)   # nombre -> {filas, cols, encabezado}
    texto: str = ""
    meta: dict = field(default_factory=dict)
    rol: str | None = None
    confianza: str | None = None
    origen_rol: str | None = None               # "reconocedor" | "agente" | "override"
    lectura_completa: bool = True
    incidencias: list = field(default_factory=list)

    @property
    def nombre(self) -> str:
        return self.ruta.name

    def incidencia(self, texto: str) -> None:
        self.incidencias.append(texto)


def _sha256(ruta: pathlib.Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as fh:
        for bloque in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


_FECHA = re.compile(r"^(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})-(\d{2})__")


def inventariar(carpeta) -> list:
    """Lista los archivos de una licitacion, ignorando los de bloqueo de Excel."""
    carpeta = pathlib.Path(carpeta)
    rutas = sorted(p for p in carpeta.iterdir()
                   if p.is_file() and not p.name.startswith("~$"))
    fuentes = []
    for n, ruta in enumerate(rutas, start=1):
        m = _FECHA.match(ruta.name)
        fuentes.append(Fuente(
            id_fuente=f"F{n:02d}",
            ruta=ruta,
            formato=ruta.suffix.lower().lstrip("."),
            bytes=ruta.stat().st_size,
            sha256=_sha256(ruta),
            fecha_nombre=m.group(1) if m else None,
        ))
    return fuentes


# --- Lectores -------------------------------------------------------------

# Marca de contenido de cobertura dentro de una planilla.
_MARCA_COBERTURA = "cobertura"


def _fila_de_encabezado(filas):
    """La fila con mas celdas con texto entre las primeras, la mas alta primero.

    Muchas planillas traen uno o varios titulos sueltos arriba del encabezado
    real. Tomar siempre la fila 0, o la primera con dos celdas, devuelve una
    ficha pobre y deja a la fuente sin clasificar.
    """
    if not filas:
        return 0, []
    mejor, mejor_n = 0, -1
    for i, fila in enumerate(filas):
        n = sum(1 for c in fila if c is not None and str(c).strip())
        if n > mejor_n:
            mejor, mejor_n = i, n
    return mejor, [("" if c is None else str(c).strip()) for c in filas[mejor]]


def _leer_xlsx(f: Fuente) -> None:
    import openpyxl

    wb = openpyxl.load_workbook(f.ruta, data_only=True, read_only=True)
    try:
        for hoja in wb.sheetnames:
            ws = wb[hoja]
            primeras, textos, tiene_cobertura = [], [], False
            for n, fila in enumerate(ws.iter_rows(values_only=True)):
                if n < 12:
                    primeras.append(list(fila))
                for c in fila:
                    if c is None:
                        continue
                    t = str(c).strip()
                    if not t:
                        continue
                    textos.append(t)
                    if _MARCA_COBERTURA in normalizar_texto(t):
                        tiene_cobertura = True
            i_enc, encabezado = _fila_de_encabezado(primeras)
            f.hojas[hoja] = {"filas": ws.max_row, "cols": ws.max_column,
                             "encabezado": encabezado,
                             "fila_encabezado": i_enc,
                             "tiene_cobertura": tiene_cobertura,
                             "texto": ("\n".join(textos)
                                       if tiene_cobertura else "")}
    finally:
        wb.close()


def _leer_xls(f: Fuente) -> None:
    import xlrd

    wb = xlrd.open_workbook(f.ruta, on_demand=True)
    try:
        for hoja in wb.sheet_names():
            ws = wb.sheet_by_name(hoja)
            primeras = [ws.row_values(i) for i in range(min(12, ws.nrows))]
            i_enc, encabezado = _fila_de_encabezado(primeras)
            f.hojas[hoja] = {"filas": ws.nrows, "cols": ws.ncols,
                             "encabezado": encabezado,
                             "fila_encabezado": i_enc,
                             "tiene_cobertura": False, "texto": ""}
    finally:
        wb.release_resources()


def _leer_pdf(f: Fuente) -> None:
    """Extrae texto y cuenta imagenes por pagina.

    Una pagina sin texto no se declara leida. El disparador de lectura parcial
    es la ausencia de texto, no la presencia de imagenes: un PDF con logo en
    cada pagina tiene imagenes en todas y se lee entero.
    """
    import pdfplumber

    partes, sin_texto, imagenes = [], [], 0
    with pdfplumber.open(f.ruta) as pdf:
        for n, pagina in enumerate(pdf.pages, start=1):
            texto = (pagina.extract_text() or "").strip()
            imagenes += len(pagina.images)
            if len(texto) < 50:
                sin_texto.append(n)
            partes.append(texto)
        total = len(pdf.pages)
    f.texto = "\n".join(partes)
    f.meta = {"paginas": total, "paginas_sin_texto": sin_texto,
              "imagenes": imagenes}
    if sin_texto:
        f.lectura_completa = False
        f.incidencia(
            f"PDF parcialmente leido: {len(sin_texto)} de {total} paginas sin "
            f"texto extraible ({imagenes} imagenes en el documento). "
            f"Paginas: {sin_texto}"
        )


def _leer_eml(f: Fuente) -> None:
    m = email.message_from_bytes(f.ruta.read_bytes(), policy=policy.default)
    cuerpo = ""
    for parte in m.walk():
        if parte.get_content_type() == "text/plain":
            cuerpo = parte.get_content()
            break
    if not cuerpo:
        for parte in m.walk():
            if parte.get_content_type() == "text/html":
                cuerpo = re.sub(r"<[^>]+>", " ", parte.get_content())
                break
    f.texto = re.sub(r"[ \t]+", " ", cuerpo).strip()
    f.meta = {"de": str(m.get("From") or ""), "fecha": str(m.get("Date") or ""),
              "asunto": str(m.get("Subject") or "")}


_LECTORES = {"xlsx": _leer_xlsx, "xlsm": _leer_xlsx, "xls": _leer_xls,
             "pdf": _leer_pdf, "eml": _leer_eml}


def leer(f: Fuente) -> Fuente:
    """Lee una fuente segun su formato. Registra el fallo en vez de propagarlo."""
    lector = _LECTORES.get(f.formato)
    if lector is None:
        f.lectura_completa = False
        f.incidencia(f"formato no soportado: .{f.formato}")
        return f
    try:
        lector(f)
    except Exception as exc:  # noqa: BLE001 - se registra, no se oculta
        f.lectura_completa = False
        f.incidencia(f"error de lectura: {type(exc).__name__}: {exc}")
    return f


# --- Reconocedor deterministico -------------------------------------------

def reconocer_padron_interno(f: Fuente) -> bool:
    """True si alguna hoja tiene la huella de columnas del sistema propio.

    Un padron interno es la cartera vigente de la cuenta, no la poblacion a
    cotizar. Se clasifica como antecedente sin intervencion del agente.
    """
    for hoja in f.hojas.values():
        if HUELLA_PADRON_INTERNO <= set(hoja["encabezado"]):
            return True
    return False


def clasificar_deterministico(f: Fuente) -> bool:
    """Aplica los reconocedores que no necesitan al agente. True si clasifico."""
    if reconocer_padron_interno(f):
        f.rol = "contexto sin datos de cartera"
        f.confianza = "alta"
        f.origen_rol = "reconocedor"
        f.incidencia(
            "export del sistema propio reconocido por huella de columnas: es la "
            "cartera vigente de la cuenta, no la poblacion a cotizar"
        )
        return True
    return False


def texto_de_cobertura(f: Fuente) -> tuple:
    """Devuelve (texto, hojas) con el contenido de cobertura de una fuente.

    Para un PDF o un mail es su texto. Para una planilla son las hojas cuyo
    contenido menciona cobertura: los comparativos de planes traen el detalle
    de cobertura en hojas separadas, no en la grilla de cotizacion.
    """
    if f.texto.strip():
        return f.texto, []
    partes, hojas = [], []
    for nombre, h in f.hojas.items():
        if h.get("tiene_cobertura") and h.get("texto"):
            hojas.append(nombre)
            partes.append("### HOJA: " + nombre + "\n" + h["texto"])
    return "\n\n".join(partes), hojas
