"""Genera la evidencia publica anonimizada de las corridas, en corridas/.

Uso:
    python scripts/preparar_corridas.py

Lee la ultima corrida de cada caso en runs/ y produce corridas/<caso>/ con una
version revisada y anonimizada. Los originales en runs/ y output/ no se tocan.

El mapa de anonimizacion contiene los nombres reales de cliente, asi que NO
vive en el repositorio: se lee de `anonimizacion.local.json`, que esta
ignorado por git. Sin ese archivo el script no produce nada.

Politica de redaccion, deliberadamente conservadora:

- Los nombres de cliente, de empresa y de persona se reemplazan por
  pseudonimos estables.
- Los nombres de la organizacion propia y los cargos internos se reemplazan
  por marcadores genericos. Un cargo identifica a una persona concreta dentro
  de un area chica, asi que se trata como dato de persona.
- Los nombres de archivo se reemplazan por un identificador derivado del rol
  y del formato. De la fecha se conserva solo el ano y el mes: el dia exacto,
  cruzado con el buzon del equipo, identifica la licitacion.
- Del tamano se publica un tramo de magnitud, no el valor exacto. El tamano
  exacto de un archivo es una huella tan buena como su nombre.
- El sha256 del original se publica y NO anonimiza: es un identificador
  univoco. Permite verificar el archivo a quien lo tiene, y permite a un
  tercero confirmar o descartar una sospecha sobre un archivo concreto. Se
  publica igual porque es el unico mecanismo de verificacion que queda, pero
  no debe presentarse como anonimizacion.
- Las rutas absolutas se recortan, tanto con separador `\\` como `/`.
- El texto literal del pliego del cliente NO se publica en ninguna forma:
  ni las citas textuales de la hoja Coberturas, ni los prompts que lo
  contienen, ni los detalles que lo parafrasean. Se publican el tema, la
  confianza y el conteo.
- Los cuerpos de mail no se publican.
- Los prompts enviados al modelo se publican como plantilla mas un resumen
  del payload, no con el payload literal.
- Las cifras agregadas de poblacion se publican o se omiten segun
  `publicar_cifras` en el mapa local.
"""
import hashlib
import json
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
MAPA = RAIZ / "anonimizacion.local.json"
DESTINO = RAIZ / "corridas"
CASOS = ("caso_a", "caso_b", "caso_c")

REDACTADO = "[REDACTADO: contenido del cliente, no publicable]"


def cargar_mapa():
    if not MAPA.exists():
        print(f"ERROR: falta {MAPA.name}. Sin el mapa de anonimizacion no se "
              f"genera evidencia publica.", file=sys.stderr)
        return None
    return json.loads(MAPA.read_text(encoding="utf-8"))


# Cada vocal matchea sus variantes acentuadas: el mapa no puede depender de
# como venga escrito el nombre en cada archivo. Un solo acento perdido es una
# fuga: un nombre cargado sin acento no capturaba su version acentuada.
_EQUIV = {"a": "aáàäâ", "e": "eéèëê", "i": "iíìïî", "o": "oóòöô",
          "u": "uúùüû", "n": "nñ", "c": "cç"}


def _patron_flexible(termino: str) -> str:
    partes = []
    for ch in termino:
        base = ch.lower()
        if base in _EQUIV:
            partes.append(f"[{_EQUIV[base]}{_EQUIV[base].upper()}]")
        elif ch.isspace():
            partes.append(r"\s+")
        else:
            partes.append(re.escape(ch))
    return "".join(partes)


# Alias de la organizacion propia. No son un secreto —el catalogo de planes
# de `catalogos.py` ya la identifica— pero nombrarla al lado de un cliente
# seudonimizado y de un comparativo de precios convierte la evidencia en
# documentacion comercial atribuible. Se redactan por eso, no por secreto.
TERMINOS_ORGANIZACION = ("Swiss Medical Group", "Swiss Medical", "SwissMedical",
                         "SMG", "S.M.G.")

# Cargo + area. Dentro de un area chica un cargo identifica a una persona,
# asi que se trata igual que un nombre. Deliberadamente acotado a la forma
# "<cargo> [seniority] de <Area>" para no comerse texto que no es un cargo.
_CARGOS = (r"\b(?:Analista|Gerente|Director|Directora|Jefe|Jefa|Responsable|"
           r"Coordinador|Coordinadora|Supervisor|Supervisora|L[ií]der)"
           r"(?:\s+(?:Sr\.?|Ssr\.?|Jr\.?|Senior|Junior))?"
           r"\s+de\s+[A-Z][\wáéíóúñÁÉÍÓÚÑ]*(?:\s+[A-Z][\wáéíóúñÁÉÍÓÚÑ]*)?")


def construir_anonimizador(mapa):
    """Devuelve una funcion que reemplaza todo termino sensible en un texto."""
    pares = sorted(mapa.get("terminos", {}).items(),
                   key=lambda kv: -len(kv[0]))
    patrones = [(re.compile(_patron_flexible(k), re.IGNORECASE), v)
                for k, v in pares]
    org = [(re.compile(_patron_flexible(t)), "[organizacion propia]")
           for t in sorted(TERMINOS_ORGANIZACION, key=len, reverse=True)]

    def anonimizar(texto):
        if texto is None:
            return None
        s = str(texto)
        # Correos y rutas absolutas PRIMERO. Si se sustituyen los terminos
        # antes, un correo cuyo usuario contiene un termino del mapa queda
        # como "[persona]@cliente.com.ar" y el dominio del cliente sobrevive:
        # la regex de correo ya no matchea porque "]" no es un caracter word.
        s = re.sub(r"[\w.+-]+@[\w.-]+", "[correo]", s)
        # Un solo backslash. La version anterior pedia dos (`\\\\` en un raw
        # string son dos backslashes literales para el motor de regex), asi
        # que una ruta Windows normal `C:\Users\...` no se anonimizaba.
        s = re.sub(r"\\\\[^\s\"']+", "[ruta local]", s)      # UNC: \\host\...
        s = re.sub(r"[A-Za-z]:\\[^\s\"']+", "[ruta local]", s)
        s = re.sub(r"[A-Za-z]:/[^\s\"']+", "[ruta local]", s)
        for patron, reemplazo in patrones:
            s = patron.sub(reemplazo, s)
        for patron, reemplazo in org:
            s = patron.sub(reemplazo, s)
        s = re.sub(_CARGOS, "[cargo interno]", s)
        # Cifras comerciales. Anonimizar nombres no alcanza: el modelo cita
        # porcentajes e importes en sus motivos, y un diferencial de precio
        # identifica una negociacion aunque el cliente este seudonimizado.
        # Paso con un motivo de la forma "diferencial de precio (NN% plus)".
        # La cifra real no se reproduce aca: el ejemplo es sintetico.
        s = re.sub(r"\d+(?:[.,]\d+)?\s*%", "[porcentaje]", s)
        s = re.sub(r"(?:\$|USD|ARS)\s*[\d.,]+", "[importe]", s)
        s = re.sub(r"\b\d[\d.,]{3,}\b", "[cifra]", s)
        return s

    return anonimizar


def tramo_de_tamano(n_bytes) -> str:
    """Tramo de magnitud de un archivo. El tamano exacto es una huella."""
    kb = (n_bytes or 0) / 1024
    if kb < 100:
        return "< 100 KB"
    if kb < 1024:
        return "100 KB - 1 MB"
    if kb < 10 * 1024:
        return "1 - 10 MB"
    return "> 10 MB"


def seudonimo_archivo(entrada, n, anonimizar):
    """Identificador no revelador: ano-mes + rol + formato.

    Del dia exacto se prescinde a proposito: la fecha completa, cruzada con
    el buzon del equipo, alcanza para identificar la licitacion. El ano y el
    mes conservan el orden cronologico, que es lo que la evidencia necesita.
    """
    rol = (entrada.get("rol") or "sin rol").replace(" ", "_")
    fecha = ""
    m = re.match(r"^(\d{4}-\d{2})-\d{2}", entrada["archivo"])
    if m:
        fecha = m.group(1)
    ext = entrada["archivo"].rsplit(".", 1)[-1].lower()
    return f"{entrada['id_fuente']}_{fecha}_{rol}.{ext}"


def preparar_caso(caso, mapa, anonimizar):
    dir_runs = RAIZ / "runs" / caso
    if not dir_runs.is_dir():
        return None
    corridas = sorted(d for d in dir_runs.iterdir() if d.is_dir())
    if not corridas:
        return None
    ult = corridas[-1]
    m = json.loads((ult / "manifiesto.json").read_text(encoding="utf-8"))
    llamadas = json.loads((ult / "llamadas_modelo.json").read_text(encoding="utf-8"))

    publicar_cifras = mapa.get("publicar_cifras", False)
    destino = DESTINO / caso
    destino.mkdir(parents=True, exist_ok=True)

    def cifra(v, fmt="{:,.0f}"):
        return fmt.format(v) if publicar_cifras else "[cifra no publicada]"

    # --- entrada.md ---
    lineas = [f"# {caso} — entrada", "",
              f"Corrida: `{ult.name}`  ·  Version de codigo: "
              f"`{m['codigo']['version_codigo']}`", "",
              "Los archivos originales no se publican. Se listan con su rol, "
              "su formato y el sha256 del archivo real, que permite verificar "
              "que la corrida uso exactamente esos insumos si alguien tiene "
              "acceso autorizado a ellos.", "",
              "De la fecha se publica el ano y el mes, y del tamano un tramo "
              "de magnitud: el dia exacto y el tamano exacto son huellas que, "
              "cruzadas con el buzon del equipo, identifican la licitacion.", "",
              "**El sha256 no anonimiza.** Es un identificador univoco del "
              "archivo original. Sirve para que quien tenga acceso autorizado "
              "al archivo verifique que la corrida uso exactamente ese "
              "archivo, y tambien permite a un tercero que sospeche de un "
              "archivo concreto confirmar o descartar la sospecha comparando "
              "el hash. Expone menos que el nombre, la fecha exacta y el "
              "tamano exacto; no es anonimato.", "",
              "| id | archivo (seudonimo) | formato | tamano | rol | "
              "confianza | origen | lectura | sha256 del original |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for n, e in enumerate(m["entradas"], 1):
        lineas.append(
            f"| {e['id_fuente']} | `{seudonimo_archivo(e, n, anonimizar)}` | "
            f"{e['archivo'].rsplit('.',1)[-1]} | {tramo_de_tamano(e['bytes'])} | "
            f"{e['rol'] or 'sin rol'} | {e['confianza'] or '-'} | "
            f"{e['origen_rol'] or '-'} | "
            f"{'completa' if e['lectura_completa'] else '**PARCIAL**'} | "
            f"`{e['sha256'][:16]}…` |")
    lineas += ["", "## Insumos de referencia", "",
               "- Tabla de escenarios de situacion terapeutica (no publicable: "
               "insumo interno del area).",
               "- Distribucion etaria precomputada desde la referencia "
               "corporativa (no publicable: deriva de la cartera real)."]
    (destino / "entrada.md").write_text("\n".join(lineas) + "\n",
                                        encoding="utf-8")

    # --- salida.md ---
    c = m["controles"]
    pob = m["poblacion"]
    lineas = [f"# {caso} — salida", "",
              f"Fecha de corrida: `{m['timestamp']}`", "",
              "## Que produjo", "",
              f"Un Excel de ocho hojas. **El archivo no se publica**: las "
              f"hojas Informacion recibida, Diagnostico, Supuestos y "
              f"Coberturas contienen datos personales seudonimizados, nombres "
              f"de cliente y texto literal del pliego. Existe localmente en "
              f"`output/` y esta fuera del control de versiones.", "",
              "Este documento describe la corrida; **no reemplaza a esa "
              "salida**.", "",
              "| Hoja | Filas |", "| --- | --- |"]
    # El conteo de filas de Informacion recibida es una fila por persona: ES
    # la poblacion. Gatearlo detras del mismo flag que las cifras, porque
    # publicarlo equivale a publicar el tamano de la cartera del cliente.
    HOJAS_PERSONALES = {"Informacion recibida"}
    for hoja, n in m["salida"]["hojas"].items():
        valor = (cifra(n) if hoja in HOJAS_PERSONALES and n else str(n))
        lineas.append(f"| {hoja} | {valor} |")

    lineas += ["", "## Poblacion", "",
               f"- Camino: {m.get('camino', 'padron individual')}",
               f"- Personas en cartera: {cifra(pob['personas_en_cartera'])}",
               f"- Combinaciones (grupo etario × provincia × plan): "
               f"{pob['combinaciones_edad_provincia_plan']}",
               f"- Mapeo de columnas resuelto por: "
               f"{pob.get('origen_mapeo_columnas', '-')}"]
    if pob.get("subpoblaciones"):
        lineas.append(f"- Subpoblaciones: {len(pob['subpoblaciones'])}")

    lineas += ["", "## Controles", ""]
    for esc in ("optimista", "pesimista"):
        lineas.append(
            f"- **{esc}**: total de licitacion "
            f"{cifra(c[esc]['total_licitacion'], '{:,.6f}')}, "
            f"{c[esc]['alternativas_controladas']} pares "
            f"(subpoblacion, alternativa) controlados, tolerancia 1e-6.")
    comp = c.get("comparacion_entre_escenarios", {})
    if comp:
        lineas.append(
            f"- **comparacion entre escenarios**: "
            f"{comp['combinaciones_comparadas']} combinaciones comparadas "
            f"sumando situ, maxima diferencia "
            f"{comp['maxima_diferencia_absoluta']:.2e}.")
    lineas += ["",
               "El total de licitacion es la suma de las subpoblaciones "
               "**dentro de una alternativa**. Las alternativas de plan no se "
               "suman entre si.", ""]

    if m.get("cruce"):
        cr = m["cruce"]
        lineas += ["## Cruces inferidos", "",
                   f"- Condicionados al plan: {cr['cruces_condicionados']}",
                   f"- Por marginal de subpoblacion: "
                   f"{cr['cruces_por_marginal']}",
                   f"- Segmentos resueltos por la regla 6.9: "
                   f"{cr['segmentos_por_regla_6_9']}", ""]

    parciales = [e for e in m["entradas"] if not e["lectura_completa"]]
    lineas += ["## Limitaciones declaradas de esta corrida", ""]
    if parciales:
        for e in parciales:
            lineas.append(
                f"- `{e['id_fuente']}` quedo **parcialmente leida**: es un PDF "
                f"con paginas sin texto extraible. Su contenido embebido en "
                f"imagenes no se leyo. V0 no hace OCR.")
    else:
        lineas.append("- Ninguna fuente quedo parcialmente leida.")
    lineas.append("- Ninguna fuente informa situacion terapeutica observada, "
                  "asi que la hoja Cartera recibida sale vacia con nota.")
    (destino / "salida.md").write_text("\n".join(lineas) + "\n",
                                       encoding="utf-8")

    # --- llamadas_modelo.json (anonimizado y redactado) ---
    publicas = []
    for l in llamadas:
        respuesta = l["respuesta"]
        if l["tarea"].startswith("coberturas"):
            respuesta_publica = REDACTADO
            nota = ("La respuesta lista requisitos de cobertura con cita "
                    "textual del documento del cliente. No se publica.")
        else:
            respuesta_publica = anonimizar(respuesta)
            nota = "Respuesta publicada con nombres anonimizados."
        publicas.append({
            "tarea": anonimizar(l["tarea"]),
            "modelo": l["modelo"],
            "timestamp": l["timestamp"],
            "system_prompt": "ver prompts/system_prompt.md (identico)",
            "user_prompt": (
                "ver prompts/ (plantilla). El payload interpolado contiene "
                "nombres de archivo, asuntos de mail y texto del cliente, y "
                "no se publica."),
            "sha256_user_prompt": hashlib.sha256(
                l["user_prompt"].encode("utf-8")).hexdigest(),
            "largo_user_prompt": len(l["user_prompt"]),
            "respuesta": respuesta_publica,
            "sha256_respuesta": hashlib.sha256(
                respuesta.encode("utf-8")).hexdigest(),
            "largo_respuesta": len(respuesta),
            "nota_de_redaccion": nota,
            "tokens_entrada": l["tokens_entrada"],
            "tokens_entrada_nuevos": l.get("tokens_entrada_nuevos"),
            "tokens_cache_creacion": l.get("tokens_cache_creacion"),
            "tokens_cache_lectura": l.get("tokens_cache_lectura"),
            "tokens_salida": l["tokens_salida"],
            "costo_usd_estimado_lista": l["costo_usd"],
            "duracion_ms": l["duracion_ms"],
            "error": l["error"],
        })
    (destino / "llamadas_modelo.json").write_text(
        json.dumps(publicas, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- manifiesto_codigo.json ---
    (destino / "huella_codigo.json").write_text(
        json.dumps(m["codigo"], ensure_ascii=False, indent=2),
        encoding="utf-8")

    return {"caso": caso, "corrida": ult.name,
            "llamadas": len(publicas),
            "redactadas": sum(1 for p in publicas
                              if p["respuesta"] == REDACTADO)}


def main() -> int:
    mapa = cargar_mapa()
    if mapa is None:
        return 1
    anonimizar = construir_anonimizador(mapa)
    DESTINO.mkdir(exist_ok=True)
    resultados = []
    for caso in CASOS:
        r = preparar_caso(caso, mapa, anonimizar)
        if r:
            resultados.append(r)
            print(f"  {r['caso']}: corrida {r['corrida']}, "
                  f"{r['llamadas']} llamadas ({r['redactadas']} redactadas)")
        else:
            print(f"  {caso}: sin corridas en runs/", file=sys.stderr)
    return 0 if resultados else 1


if __name__ == "__main__":
    raise SystemExit(main())
