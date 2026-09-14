"""Capa agentica: clasificacion del rol de cada fuente.

Referencia: docs/handoff_v0.md, secciones 5 y 6.1.

El agente interviene solo donde hace falta criterio: proponer el rol de un
archivo y su nivel de confianza. No calcula, no aplica reglas y no toma
decisiones actuariales. Lo que puede resolverse por huella de columnas se
resuelve antes, sin el.

Toda llamada queda registrada con su prompt, su respuesta literal, el modelo,
los tokens y el costo, para que la corrida sea reconstruible.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import time
from dataclasses import asdict, dataclass, field

from .fuentes import ROLES

MODELO_POR_DEFECTO = "claude-haiku-4-5"

RUTA_PROMPTS = pathlib.Path(__file__).resolve().parents[2] / "prompts"


@dataclass
class Llamada:
    """Registro literal de una llamada al modelo."""

    tarea: str
    modelo: str
    system_prompt: str
    user_prompt: str
    respuesta: str
    tokens_entrada: int = 0
    tokens_entrada_nuevos: int = 0
    tokens_cache_creacion: int = 0
    tokens_cache_lectura: int = 0
    tokens_salida: int = 0
    costo_usd: float = 0.0
    duracion_ms: int = 0
    timestamp: str = ""
    error: str | None = None

    def como_dict(self) -> dict:
        return asdict(self)


class ClienteCLI:
    """Backend de modelo sobre el binario de Claude Code.

    Se usa porque en este entorno no hay ANTHROPIC_API_KEY. La interfaz es la
    misma que tendria un cliente de API, asi que cambiar de backend no toca al
    resto del sistema.
    """

    def __init__(self, modelo: str = MODELO_POR_DEFECTO, timeout: int = 300):
        self.modelo = modelo
        self.timeout = timeout
        self.binario = os.environ.get("CLAUDE_CODE_EXECPATH")
        if not self.binario or not pathlib.Path(self.binario).exists():
            raise RuntimeError(
                "no hay backend de modelo disponible: falta CLAUDE_CODE_EXECPATH"
            )

    def __call__(self, tarea: str, system_prompt: str, user_prompt: str) -> Llamada:
        inicio = time.time()
        llamada = Llamada(
            tarea=tarea, modelo=self.modelo, system_prompt=system_prompt,
            user_prompt=user_prompt, respuesta="",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
        )
        # El prompt va por stdin, no como argumento: un pliego completo
        # supera el limite de linea de comandos de Windows (WinError 206).
        cmd = [self.binario, "-p", "--output-format", "json",
               "--model", self.modelo, "--append-system-prompt", system_prompt]
        try:
            proc = subprocess.run(cmd, input=user_prompt, capture_output=True,
                                  text=True, encoding="utf-8",
                                  timeout=self.timeout)
            if not proc.stdout.strip():
                raise RuntimeError(
                    f"el CLI no devolvio salida (codigo {proc.returncode}): "
                    f"{proc.stderr[:300]}")
            datos = json.loads(proc.stdout)
            llamada.respuesta = datos.get("result", "")
            uso = datos.get("usage", {})
            llamada.tokens_entrada_nuevos = uso.get("input_tokens", 0)
            llamada.tokens_cache_creacion = uso.get(
                "cache_creation_input_tokens", 0)
            llamada.tokens_cache_lectura = uso.get(
                "cache_read_input_tokens", 0)
            llamada.tokens_entrada = (
                llamada.tokens_entrada_nuevos
                + llamada.tokens_cache_creacion
                + llamada.tokens_cache_lectura
            )
            llamada.tokens_salida = uso.get("output_tokens", 0)
            llamada.costo_usd = datos.get("total_cost_usd", 0.0)
        except Exception as exc:  # noqa: BLE001 - se registra, no se oculta
            llamada.error = f"{type(exc).__name__}: {exc}"
        llamada.duracion_ms = int((time.time() - inicio) * 1000)
        return llamada


class Bitacora:
    """Acumula las llamadas de una corrida."""

    def __init__(self):
        self.llamadas: list[Llamada] = []

    def registrar(self, llamada: Llamada) -> Llamada:
        self.llamadas.append(llamada)
        return llamada

    @property
    def tokens_entrada(self) -> int:
        return sum(l.tokens_entrada for l in self.llamadas)

    @property
    def tokens_salida(self) -> int:
        return sum(l.tokens_salida for l in self.llamadas)

    @property
    def costo_usd(self) -> float:
        return sum(l.costo_usd for l in self.llamadas)

    def resumen(self) -> dict:
        return {
            "llamadas": len(self.llamadas),
            "tokens_entrada": self.tokens_entrada,
            "tokens_entrada_nuevos": sum(
                l.tokens_entrada_nuevos for l in self.llamadas),
            "tokens_cache_creacion": sum(
                l.tokens_cache_creacion for l in self.llamadas),
            "tokens_cache_lectura": sum(
                l.tokens_cache_lectura for l in self.llamadas),
            "tokens_salida": self.tokens_salida,
            "costo_usd": self.costo_usd,
            "con_error": sum(1 for l in self.llamadas if l.error),
        }


def _cargar_prompt(nombre: str) -> str:
    ruta = RUTA_PROMPTS / nombre
    if not ruta.exists():
        raise FileNotFoundError(f"falta el contrato del agente: {ruta}")
    return ruta.read_text(encoding="utf-8")


def _ficha(f) -> dict:
    """Lo que se le manda al modelo de un archivo. Sin datos personales.

    Se envian nombre, fecha, formato, tamano, nombres de hoja, encabezados de
    columna y un recorte de texto. Nunca filas de datos.
    """
    ficha = {
        "id_fuente": f.id_fuente,
        "nombre_archivo": f.nombre,
        "fecha_en_el_nombre": f.fecha_nombre,
        "formato": f.formato,
        "kb": f.bytes // 1024,
        "hojas": {
            nombre: {"filas": h["filas"], "cols": h["cols"],
                     "encabezado": h["encabezado"][:40]}
            for nombre, h in list(f.hojas.items())[:12]
        },
    }
    if f.formato == "eml":
        ficha["asunto"] = f.meta.get("asunto", "")
        ficha["de"] = f.meta.get("de", "")
        ficha["cuerpo_recortado"] = f.texto[:600]
    elif f.formato == "pdf":
        ficha["paginas"] = f.meta.get("paginas")
        ficha["paginas_sin_texto"] = len(f.meta.get("paginas_sin_texto", []))
        ficha["texto_recortado"] = f.texto[:600]
    return ficha


def _extraer_json(texto: str):
    """Saca el JSON de la respuesta, tolerando cercos de markdown."""
    texto = texto.strip()
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto, flags=re.MULTILINE)
    inicio = texto.find("[")
    if inicio == -1:
        inicio = texto.find("{")
    fin = max(texto.rfind("]"), texto.rfind("}"))
    if inicio == -1 or fin == -1:
        raise ValueError(f"la respuesta no trae JSON: {texto[:200]!r}")
    return json.loads(texto[inicio:fin + 1])


def clasificar_fuentes(cliente, bitacora: Bitacora, fuentes: list) -> list:
    """Pide al modelo el rol y la confianza de las fuentes sin clasificar.

    Las fuentes ya resueltas por el reconocedor deterministico no se le mandan.
    Una respuesta invalida no detiene el proceso: las fuentes quedan sin rol,
    con confianza baja, y eso se declara en Diagnostico.
    """
    pendientes = [f for f in fuentes if f.rol is None]
    if not pendientes:
        return []

    system_prompt = _cargar_prompt("system_prompt.md")
    plantilla = _cargar_prompt("user_prompt.md")
    user_prompt = plantilla.replace(
        "{{ARCHIVOS}}",
        json.dumps([_ficha(f) for f in pendientes], ensure_ascii=False, indent=2),
    ).replace("{{ROLES}}", "\n".join(f"- {r}" for r in ROLES))

    llamada = bitacora.registrar(
        cliente("clasificacion de fuentes", system_prompt, user_prompt))

    if llamada.error:
        for f in pendientes:
            f.confianza = "baja"
            f.origen_rol = "agente"
            f.incidencia(f"el agente no respondio: {llamada.error}")
        return [llamada]

    try:
        propuesto = _extraer_json(llamada.respuesta)
    except Exception as exc:  # noqa: BLE001
        for f in pendientes:
            f.confianza = "baja"
            f.origen_rol = "agente"
            f.incidencia(f"respuesta del agente ilegible: {exc}")
        return [llamada]

    por_id = {f.id_fuente: f for f in pendientes}
    for item in propuesto if isinstance(propuesto, list) else []:
        f = por_id.get(item.get("id_fuente"))
        if f is None:
            continue
        rol = item.get("rol")
        if rol not in ROLES:
            f.confianza = "baja"
            f.origen_rol = "agente"
            f.incidencia(f"el agente propuso un rol fuera del catalogo: {rol!r}")
            continue
        f.rol = rol
        f.confianza = item.get("confianza", "baja")
        f.origen_rol = "agente"
        if item.get("motivo"):
            f.incidencia(f"agente: {item['motivo']}")

    for f in pendientes:
        if f.rol is None:
            f.confianza = "baja"
            f.origen_rol = "agente"
            f.incidencia("el agente no devolvio rol para esta fuente")
    return [llamada]


# Recorte del texto que se le manda al modelo para extraer coberturas.
# Los pliegos rondan las 20 paginas; se manda entero salvo que sea enorme.
MAX_TEXTO_COBERTURAS = 60000


# Roles cuyos documentos pueden traer detalles de cobertura. La cotizacion
# interna posterior no aporta poblacion pero si describe coberturas, y en
# varias licitaciones es donde vive el comparativo de planes.
ROLES_CON_COBERTURA = ("documento original del cliente",
                       "cotizacion interna posterior")


def recolectar_coberturas(cliente, bitacora: Bitacora, inventario) -> list:
    """Arma las filas de la hoja Coberturas recorriendo todas las fuentes.

    Declara la procedencia: no es lo mismo un requisito del pliego del cliente
    que un detalle tomado de una cotizacion interna.
    """
    from .fuentes import texto_de_cobertura

    filas = []
    for f in inventario:
        if f.rol not in ROLES_CON_COBERTURA:
            continue
        lectura = ("completa" if f.lectura_completa else "PARCIAL")
        texto, hojas = texto_de_cobertura(f)
        ubicacion = (f"hojas: {', '.join(hojas)}" if hojas
                     else f"{f.meta.get('paginas', '')} paginas")
        if not texto.strip():
            filas.append([f.id_fuente, f.nombre, f.rol, ubicacion, lectura,
                          "(sin texto extraible)",
                          "No se encontro texto de cobertura en esta fuente.",
                          "", "baja"])
            continue
        if cliente is None:
            filas.append([f.id_fuente, f.nombre, f.rol, ubicacion, lectura,
                          "(sin agente)",
                          "Corrida sin backend de modelo: no se extrajeron "
                          "detalles.", "", "baja"])
            continue
        items, _ = extraer_coberturas(cliente, bitacora, f, texto=texto)
        if not items:
            filas.append([f.id_fuente, f.nombre, f.rol, ubicacion, lectura,
                          "(sin detalles extraidos)",
                          "El agente no devolvio detalles legibles.", "",
                          "baja"])
            continue
        for it in items:
            filas.append([f.id_fuente, f.nombre, f.rol, ubicacion, lectura,
                          it["tema"], it["detalle"], it["cita"],
                          it["confianza"]])
    return filas


def extraer_coberturas(cliente, bitacora: Bitacora, fuente, texto=None) -> tuple:
    """Extrae detalles de cobertura de un documento original del cliente.

    Aca el agente si aporta: la estructura de un pliego varia entre clientes y
    no hay columnas que mapear. Devuelve (items, llamada).

    Un fallo no detiene el proceso: se devuelve lista vacia y queda declarado.
    """
    completo = fuente.texto if texto is None else texto
    if not completo.strip():
        return [], None

    system_prompt = _cargar_prompt("system_prompt.md")
    plantilla = _cargar_prompt("user_prompt_coberturas.md")
    texto = completo[:MAX_TEXTO_COBERTURAS]
    user_prompt = (plantilla
                   .replace("{{ARCHIVO}}", fuente.nombre)
                   .replace("{{PAGINAS}}", str(fuente.meta.get("paginas", "")))
                   .replace("{{TEXTO}}", texto))

    llamada = bitacora.registrar(
        cliente(f"coberturas {fuente.id_fuente}", system_prompt, user_prompt))

    if llamada.error:
        fuente.incidencia(f"extraccion de coberturas fallida: {llamada.error}")
        return [], llamada
    try:
        items = _extraer_json(llamada.respuesta)
    except Exception as exc:  # noqa: BLE001
        fuente.incidencia(f"coberturas: respuesta ilegible: {exc}")
        return [], llamada

    if not isinstance(items, list):
        fuente.incidencia("coberturas: la respuesta no es una lista")
        return [], llamada

    limpios = []
    for it in items:
        if not isinstance(it, dict) or not it.get("detalle"):
            continue
        limpios.append({
            "tema": str(it.get("tema", ""))[:60],
            "detalle": str(it.get("detalle", ""))[:400],
            "cita": str(it.get("cita", ""))[:220],
            "confianza": it.get("confianza", "baja"),
        })
    if len(texto) < len(completo):
        fuente.incidencia(
            f"coberturas: se envio al modelo {len(texto)} de "
            f"{len(completo)} caracteres del documento")
    return limpios, llamada


def mapear_columnas(cliente, bitacora: Bitacora, fuente) -> tuple:
    """Pide al modelo que identifique la hoja de poblacion y sus columnas.

    Se usa solo cuando el reconocimiento por nombre de columna fallo. Los
    encabezados varian entre clientes ('LEGAJO' en uno, 'ID Grupo' en otro) y
    ahi el criterio del modelo aporta. Devuelve (hoja, indices, llamada).
    """
    hojas = {
        nombre: {"filas": h["filas"], "cols": h["cols"],
                 "encabezado": h["encabezado"][:40]}
        for nombre, h in fuente.hojas.items()
    }
    if not hojas:
        return None, None, None

    system_prompt = _cargar_prompt("system_prompt.md")
    plantilla = _cargar_prompt("user_prompt_columnas.md")
    user_prompt = (plantilla
                   .replace("{{ARCHIVO}}", fuente.nombre)
                   .replace("{{HOJAS}}",
                            json.dumps(hojas, ensure_ascii=False, indent=2)))

    llamada = bitacora.registrar(
        cliente(f"mapeo de columnas {fuente.id_fuente}", system_prompt,
                user_prompt))
    if llamada.error:
        fuente.incidencia(f"mapeo de columnas fallido: {llamada.error}")
        return None, None, llamada
    try:
        r = _extraer_json(llamada.respuesta)
    except Exception as exc:  # noqa: BLE001
        fuente.incidencia(f"mapeo de columnas ilegible: {exc}")
        return None, None, llamada

    hoja = r.get("hoja")
    if not hoja or hoja not in fuente.hojas:
        fuente.incidencia(
            f"el agente no identifico una hoja de poblacion valida: {hoja!r}")
        return None, None, llamada

    encabezado = fuente.hojas[hoja]["encabezado"]
    idx, no_encontradas = {}, []
    for rol in ("edad", "grupo", "provincia", "tipo", "capitas", "plan"):
        col = r.get(rol)
        if col is None:
            idx[rol] = None
            continue
        if col in encabezado:
            idx[rol] = encabezado.index(col)
        else:
            idx[rol] = None
            no_encontradas.append(f"{rol}={col!r}")

    if idx.get("edad") is None:
        fuente.incidencia(
            f"el agente no identifico columna de edad en la hoja {hoja!r}")
        return None, None, llamada

    fuente.incidencia(
        f"columnas mapeadas por el agente (confianza {r.get('confianza','baja')}): "
        f"hoja {hoja!r}, " +
        ", ".join(f"{k}={encabezado[v]!r}" for k, v in idx.items()
                  if v is not None) +
        (f". Columnas propuestas que no existen: {no_encontradas}"
         if no_encontradas else ""))
    return hoja, idx, llamada
