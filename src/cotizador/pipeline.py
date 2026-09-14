"""Orquestacion de una licitacion, de la carpeta al Excel.

Referencia: docs/handoff_v0.md, seccion 5.

Los pasos 1, 3 y 5 usan al agente. Los pasos 8 a 13 son deterministicos.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import time

from . import (agente, escenarios, fuentes, normalizacion,
               pipeline_agregado, salida)
from .cartera import (agregar_para_salida, aplicar_escenario, comparar_escenarios,
                      controlar_cierre, expandir_planes)
from .catalogos import (SIN_DATO, fuente_distingue_amba, homologar_plan,
                        homologar_provincia)

# Encabezados que identifican un padron individual en una hoja.
_COL_EDAD = ("EDAD", "EDADES", "AÑOS")
_COL_GRUPO = ("LEGAJO", "ID GRUPO", "GRUPO", "NRO GRUPO", "NUMERO DE GRUPO",
              "ID_GRUPO", "GRUPO FAMILIAR", "ID TITULAR")
_COL_PROV = ("PROVINCIA", "JURISDICCION", "UBICACION")
_COL_TIPO = ("TIPO", "PARENTESCO", "VINCULO")
_COL_CAP = ("CAPITAS", "CANTIDAD DE CAPITAS", "INTEGRANTES")
_COL_PLAN = ("PLAN", "CLASIFICACION", "CATEGORIA", "NIVEL")


def _norm(t):
    import re
    import unicodedata
    t = unicodedata.normalize("NFKD", str(t))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def _buscar(encabezado, candidatos):
    """Busca por nombre normalizado: ignora mayusculas, acentos y separadores."""
    normalizados = [_norm(c) for c in encabezado]
    for cand in candidatos:
        n = _norm(cand)
        if n in normalizados:
            return normalizados.index(n)
    return None


def detectar_hoja_de_poblacion(f):
    """Devuelve (hoja, indices) de la hoja con una fila por persona."""
    mejor = None
    for nombre, h in f.hojas.items():
        enc = h["encabezado"]
        i_edad = _buscar(enc, _COL_EDAD)
        i_grupo = _buscar(enc, _COL_GRUPO)
        if i_edad is None or i_grupo is None:
            continue
        idx = {
            "edad": i_edad, "grupo": i_grupo,
            "provincia": _buscar(enc, _COL_PROV),
            "tipo": _buscar(enc, _COL_TIPO),
            "capitas": _buscar(enc, _COL_CAP),
            "plan": _buscar(enc, _COL_PLAN),
        }
        if mejor is None or h["filas"] > mejor[2]:
            mejor = (nombre, idx, h["filas"])
    return (mejor[0], mejor[1]) if mejor else (None, None)


def extraer_personas(f, hoja, idx) -> list:
    """Lee la hoja de poblacion. Una fila por persona, sin datos personales."""
    import openpyxl

    wb = openpyxl.load_workbook(f.ruta, data_only=True, read_only=True)
    ws = wb[hoja]
    it = ws.iter_rows(values_only=True)
    next(it)
    registros = []
    for fila in it:
        if not any(c is not None for c in fila):
            continue
        def val(clave):
            i = idx.get(clave)
            if i is None or i >= len(fila) or fila[i] is None:
                return ""
            return str(fila[i]).strip()
        registros.append({
            "id_fuente": f.id_fuente,
            "grupo": val("grupo"),
            "tipo": val("tipo"),
            "edad_original": val("edad"),
            "provincia": val("provincia"),
            "plan": val("plan"),
            "capitas": val("capitas"),
        })
    wb.close()
    return registros


VERSION_CODIGO = "v2"


def _git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                              text=True, timeout=10).stdout.strip() or "(sin git)"
    except Exception:  # noqa: BLE001
        return "(sin git)"


def _git_limpio() -> bool:
    try:
        r = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                           text=True, timeout=20)
        return not r.stdout.strip()
    except Exception:  # noqa: BLE001
        return False


def huella_codigo() -> dict:
    """Hash de los archivos de codigo y de prompt realmente usados.

    El SHA de git no representa la corrida cuando hay cambios sin commitear.
    Esta huella si: es el sha256 de cada archivo tal como estaba al correr,
    mas un digest agregado. Permite decir despues que dos corridas usaron el
    mismo codigo, sin atribuirlas a un commit que no las contiene.
    """
    import hashlib

    raiz = pathlib.Path(__file__).resolve().parents[2]
    archivos = sorted(
        [*(raiz / "src" / "cotizador").glob("*.py"),
         *(raiz / "scripts").glob("*.py"),
         *(raiz / "prompts").glob("*.md")])
    detalle, agregado = {}, hashlib.sha256()
    for ruta in archivos:
        h = hashlib.sha256(ruta.read_bytes()).hexdigest()
        rel = ruta.relative_to(raiz).as_posix()
        detalle[rel] = h
        agregado.update(rel.encode() + h.encode())
    sha = _git_sha()
    limpio = _git_limpio()
    return {
        "version_codigo": VERSION_CODIGO,
        "digest_codigo": agregado.hexdigest(),
        "archivos": detalle,
        "git_sha": sha,
        "git_arbol_limpio": limpio,
        "nota": (
            "El git_sha identifica el ultimo commit, no el codigo de esta "
            "corrida: el arbol tiene cambios sin commitear."
            if not limpio else
            "El arbol de trabajo estaba limpio: git_sha identifica el codigo."),
    }


def procesar(carpeta, *, nombre_caso, destino_excel, destino_corrida,
             path_tabla_st, path_cache, cliente=None) -> dict:
    """Corre una licitacion completa y devuelve el resumen de la corrida."""
    t0 = time.time()
    carpeta = pathlib.Path(carpeta)
    destino_corrida = pathlib.Path(destino_corrida)
    destino_corrida.mkdir(parents=True, exist_ok=True)

    diagnostico, supuestos, coberturas = [], [], []
    bitacora = agente.Bitacora()

    # --- Pasos 1 y 3: inventario, lectura y clasificacion -----------------
    inventario = fuentes.inventariar(carpeta)
    for f in inventario:
        fuentes.leer(f)
        fuentes.clasificar_deterministico(f)

    if cliente is not None:
        agente.clasificar_fuentes(cliente, bitacora, inventario)
    else:
        for f in inventario:
            if f.rol is None:
                f.confianza = "baja"
                f.origen_rol = "sin agente"
                f.incidencia("corrida sin backend de modelo: rol no propuesto")

    for f in inventario:
        diagnostico.append([
            f.id_fuente, f.nombre, f.formato, f.fecha_nombre or "",
            f.rol or SIN_DATO, f.confianza or SIN_DATO, f.origen_rol or "",
            "si" if f.lectura_completa else "NO",
            " | ".join(f.incidencias),
        ])

    parciales = [f for f in inventario if not f.lectura_completa]
    for f in parciales:
        supuestos.append(["fuente parcialmente leida", f.id_fuente, f.nombre,
                          " | ".join(f.incidencias)])

    # --- Paso 4: elegir la fuente de poblacion ----------------------------
    candidatas = [f for f in inventario if f.rol == "padron individual"]
    if not candidatas:
        candidatas = [f for f in inventario
                      if f.rol == "distribucion agregada"]
    poblacion = None
    origen_mapeo = None
    for f in sorted(candidatas, key=lambda x: -x.bytes):
        hoja, idx = detectar_hoja_de_poblacion(f)
        if hoja:
            poblacion, origen_mapeo = (f, hoja, idx), "codigo"
            break

    # Rama agregada: sin padron individual, la poblacion puede venir como
    # tabla cruzada de rango etario por plan, con la provincia en otra hoja.
    # Es deterministica, asi que se prueba ANTES de gastar una llamada al
    # modelo mapeando columnas.
    agregada = None
    if poblacion is None:
        for f in sorted(inventario, key=lambda x: -x.bytes):
            if f.rol not in ("distribucion agregada", "padron individual"):
                continue
            agregada = pipeline_agregado.intentar(f, path_cache)
            if agregada:
                break

    # Ultimo recurso: los encabezados varian entre clientes y ningun
    # reconocedor deterministico sirvio. Ahi si el agente mapea las columnas.
    if poblacion is None and agregada is None and cliente is not None:
        for f in sorted(candidatas, key=lambda x: -x.bytes):
            hoja, idx, _ = agente.mapear_columnas(cliente, bitacora, f)
            if hoja:
                poblacion, origen_mapeo = (f, hoja, idx), "agente"
                break

    if poblacion is None and agregada is None:
        diagnostico.append(["", "", "", "", "", "", "", "",
                            "NO SE IDENTIFICO NINGUNA FUENTE DE POBLACION: "
                            "no se emiten carteras"])
        conteo = salida.escribir(
            destino_excel, bloques_optimista={}, bloques_pesimista={},
            diagnostico=(_ENC_DIAG, diagnostico),
            supuestos=(_ENC_SUP, supuestos))
        return {"caso": nombre_caso, "sin_poblacion": True, "hojas": conteo}

    if agregada is not None:
        return pipeline_agregado.procesar(
            agregada, inventario, bitacora, cliente, diagnostico, supuestos,
            coberturas, (_ENC_INFO, _ENC_DIST, _ENC_DIAG, _ENC_SUP, _ENC_COB),
            nombre_caso=nombre_caso, carpeta=carpeta,
            destino_excel=destino_excel, destino_corrida=destino_corrida,
            path_tabla_st=path_tabla_st, path_cache=path_cache,
            codigo=huella_codigo(), t0=t0)

    f_pob, hoja, idx = poblacion
    registros = extraer_personas(f_pob, hoja, idx)
    supuestos.append(["fuente de poblacion", f_pob.id_fuente,
                      f"{f_pob.nombre} / hoja {hoja}",
                      f"{len(registros)} filas leidas. Columnas mapeadas por: "
                      f"{origen_mapeo}."])

    # Fuentes de poblacion no utilizadas y resumenes clinicos.
    for f in inventario:
        if f.rol == "distribucion agregada" and f is not f_pob:
            supuestos.append([
                "fuente agregada no utilizada como poblacion", f.id_fuente,
                f.nombre,
                "Se eligio otra fuente por prioridad de granularidad (6.2). "
                "Si es un resumen clinico o de enfermedades, NO se convierte "
                "en situacion terapeutica: situ solo sale de un dato "
                "observado por persona o de la tabla de escenarios."])
    for f in inventario:
        if f.rol is None:
            diagnostico.append([
                f.id_fuente, f.nombre, f.formato, f.fecha_nombre or "", "",
                "baja", "", "si" if f.lectura_completa else "NO",
                "SIN ROL ASIGNADO: requiere revision humana. No se uso como "
                "fuente de poblacion."])

    # --- Paso 4b: doble conteo --------------------------------------------
    if idx.get("capitas") is not None:
        dc = normalizacion.verificar_doble_conteo(registros, "capitas")
        supuestos.append(["control de doble conteo", f_pob.id_fuente,
                          f"suma columna={dc['suma_columna_capitas']:.0f} vs "
                          f"filas={dc['conteo_de_filas']}",
                          ("coinciden" if dc["coinciden"] else
                           "NO COINCIDEN - revision humana") + ". " + dc["nota"]])
        if not dc["coinciden"]:
            diagnostico.append(["", f_pob.nombre, "", "", "", "", "", "",
                                "doble conteo: la columna de capitas no "
                                "coincide con el conteo de filas"])

    # --- Paso 5: propagacion dentro del grupo familiar --------------------
    rep = normalizacion.propagar_en_grupo(registros, ("provincia", "plan"))
    for campo, r in rep.items():
        supuestos.append([
            "propagacion en grupo familiar", f_pob.id_fuente, campo,
            f"{r['filas_completadas']} filas completadas desde la fila del "
            f"titular; {r['grupos_sin_valor']} grupos sin ningun valor; "
            f"{r['grupos_en_conflicto']} grupos con valores en conflicto "
            f"(no se propago en esos)"])
        if r["grupos_en_conflicto"]:
            diagnostico.append(["", f_pob.nombre, "", "", "", "", "", "",
                                f"conflicto de {campo} dentro del grupo "
                                f"familiar en {r['grupos_en_conflicto']} grupos"])

    # --- Paso 5b: homologacion y edad -------------------------------------
    distingue_amba = any(
        homologar_provincia(r["provincia"]) == "AMBA"
        and "gba" not in r["provincia"].lower() for r in registros) and any(
        r["provincia"].strip().lower() in ("buenos aires",) for r in registros)

    conteo_base, no_homologadas, edades_fuera, sin_edad = {}, {}, 0, 0
    edades_transformadas = []
    planes_originales = {}
    for r in registros:
        try:
            edad = int(float(r["edad_original"]))
        except (TypeError, ValueError):
            sin_edad += 1
            continue
        if edad < 0:
            sin_edad += 1
            continue
        # Edad mayor a 100 en la POBLACION RECIBIDA: el valor original queda
        # en Informacion recibida, el calculo y la asignacion de escenario
        # usan 100, y la salida agrupa en '21) +'. No se descarta a nadie.
        # No toca el tratamiento de la referencia corporativa, que sigue
        # excluyendo las edades mayores a 100 de la distribucion etaria.
        if edad > 100:
            edades_fuera += 1
            edades_transformadas.append((r["edad_original"], 100))
            edad = 100

        prov = homologar_provincia(r["provincia"],
                                   fuente_distingue_amba=distingue_amba)
        if prov == SIN_DATO and r["provincia"]:
            no_homologadas[r["provincia"]] = no_homologadas.get(r["provincia"], 0) + 1

        plan = homologar_plan(r["plan"]) if r["plan"] else SIN_DATO
        if plan == SIN_DATO and r["plan"]:
            planes_originales[r["plan"]] = planes_originales.get(r["plan"], 0) + 1

        clave = ("unica", edad, prov, None if plan == SIN_DATO else plan)
        conteo_base[clave] = conteo_base.get(clave, 0.0) + 1.0

    if sin_edad:
        diagnostico.append(["", f_pob.nombre, "", "", "", "", "", "",
                            f"{sin_edad} filas descartadas por edad ilegible"])
        supuestos.append(["descarte", f_pob.id_fuente, "edad ilegible",
                          f"{sin_edad} filas"])
    if edades_fuera:
        muestra = ", ".join(f"{o}->{d}" for o, d in edades_transformadas[:10])
        supuestos.append([
            "edad mayor a 100 en la poblacion recibida", f_pob.id_fuente,
            f"{edades_fuera} personas transformadas ({muestra})",
            "La edad original se conserva en Informacion recibida. Para "
            "calculo y asignacion de escenario se usa 100. La salida agrupa "
            "en '21) +'. No se descarta ninguna persona. Aplica solo a la "
            "poblacion recibida: la referencia corporativa sigue excluyendo "
            "las edades mayores a 100 de la distribucion etaria."])
    for valor, n in sorted(no_homologadas.items(), key=lambda x: -x[1]):
        supuestos.append(["provincia no homologable", f_pob.id_fuente,
                          valor, f"{n} filas quedaron en 'sin dato'"])
    for valor, n in sorted(planes_originales.items(), key=lambda x: -x[1]):
        supuestos.append([
            "plan no homologable", f_pob.id_fuente, valor,
            f"{n} filas. Valor original conservado; la cartera se expande a "
            f"las nueve alternativas de cotizacion."])

    # Una fila por combinacion, con la cantidad de personas.
    filas_base = [(sub, edad, prov, plan, n)
                  for (sub, edad, prov, plan), n in sorted(
                      conteo_base.items(), key=lambda x: (x[0][0], x[0][1],
                                                          x[0][2], x[0][3] or ""))]

    # --- Paso 8: verificacion previa a cruzar o reescalar -----------------
    chequeo = normalizacion.verificar_antes_de_cruzar([
        {"id_fuente": f_pob.id_fuente, "subpoblacion": "unica",
         "periodo": f_pob.fecha_nombre, "cobertura": "poblacion completa",
         "total": sum(conteo_base.values())}])
    supuestos.append([
        "verificacion previa al cruce", f_pob.id_fuente,
        f"distribuciones={chequeo['distribuciones']}, "
        f"apto_para_reescalar={chequeo['apto_para_reescalar']}",
        ("una sola fuente de poblacion: no hay cruce inferido ni reescalado "
         "de totales en esta licitacion")
        if chequeo["distribuciones"] == 1 else " | ".join(chequeo["hallazgos"])])

    # --- Pasos 9 a 13: cartera, escenarios y controles --------------------
    base = expandir_planes(filas_base)
    tabla = escenarios.cargar(path_tabla_st)

    controles, bloques = {}, {}
    for esc in ("optimista", "pesimista"):
        filas_esc = aplicar_escenario(base, tabla, esc)
        controles[esc] = controlar_cierre(base, filas_esc, esc)
        bloques[esc] = agregar_para_salida(filas_esc)

    # Igualdad entre escenarios antes de separar situ.
    t_opt = controles["optimista"]["total_por_alternativa"]
    t_pes = controles["pesimista"]["total_por_alternativa"]
    if set(t_opt) != set(t_pes) or any(
            abs(t_opt[k] - t_pes[k]) > 1e-9 for k in t_opt):
        raise RuntimeError(
            f"los escenarios no cubren la misma poblacion: {t_opt} vs {t_pes}")

    # Combinacion por combinacion, sumando situ. Un total general igual puede
    # esconder combinaciones distintas que se compensan entre si.
    comparacion = comparar_escenarios(bloques["optimista"], bloques["pesimista"])
    controles["comparacion_entre_escenarios"] = comparacion
    supuestos.append([
        "comparacion entre escenarios", f_pob.id_fuente,
        f"{comparacion['combinaciones_comparadas']} combinaciones comparadas, "
        f"maxima diferencia {comparacion['maxima_diferencia_absoluta']:.2e}",
        comparacion["nota"]])

    # Nadie se pierde por la transformacion de edad.
    personas = sum(conteo_base.values())
    esperado = len(registros) - sin_edad
    if abs(personas - esperado) > 1e-9:
        raise RuntimeError(
            f"se perdieron personas entre la lectura y la cartera: "
            f"{personas} vs {esperado}")
    supuestos.append([
        "control de personas", f_pob.id_fuente,
        f"{len(registros)} filas leidas, {sin_edad} descartadas por edad "
        f"ilegible, {edades_fuera} con edad transformada a 100, "
        f"{personas:.0f} en cartera",
        "La transformacion de edad no descarta personas: se verifica que la "
        "cartera contenga todas las filas leidas menos las ilegibles."])

    supuestos.append([
        "control de cantidades", f_pob.id_fuente,
        f"total_licitacion={controles['optimista']['total_licitacion']:.6f}",
        f"{controles['optimista']['alternativas_controladas']} pares "
        f"(subpoblacion, alternativa) controlados por escenario, tolerancia "
        f"1e-6. Optimista y pesimista cubren la misma poblacion. Las "
        f"alternativas no se suman entre si."])

    # Cartera recibida: solo con situ observado. Caso A no informa situ.
    nota_recibida = ("Ninguna fuente informa situacion terapeutica. La hoja se "
                     "emite vacia para que el esquema del Excel sea estable.")

    coberturas.extend(
        agente.recolectar_coberturas(cliente, bitacora, inventario))

    info = [[r["id_fuente"], r["grupo"], r["tipo"], r["edad_original"],
             r["provincia"], r["plan"]] for r in registros]

    conteo = salida.escribir(
        destino_excel,
        bloques_optimista=bloques["optimista"],
        bloques_pesimista=bloques["pesimista"],
        bloques_recibida={},
        informacion_recibida=(_ENC_INFO, info),
        distribuciones=(_ENC_DIST, []),
        diagnostico=(_ENC_DIAG, diagnostico),
        supuestos=(_ENC_SUP, supuestos),
        coberturas=(_ENC_COB, coberturas),
        nota_recibida=nota_recibida)

    # --- Manifiesto de la corrida -----------------------------------------
    manifiesto = {
        "caso": nombre_caso,
        "carpeta": str(carpeta),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "codigo": huella_codigo(),
        "duracion_s": round(time.time() - t0, 1),
        "entradas": [{"id_fuente": f.id_fuente, "archivo": f.nombre,
                      "bytes": f.bytes, "sha256": f.sha256,
                      "rol": f.rol, "confianza": f.confianza,
                      "origen_rol": f.origen_rol,
                      "lectura_completa": f.lectura_completa}
                     for f in inventario],
        "referencia": {
            "tabla_escenarios": str(path_tabla_st),
            "cache_distribucion": str(path_cache),
        },
        "poblacion": {
            "fuente": f_pob.id_fuente, "hoja": hoja,
            "filas_leidas": len(registros),
            "origen_mapeo_columnas": origen_mapeo,
            "personas_en_cartera": sum(conteo_base.values()),
            "combinaciones_edad_provincia_plan": len(filas_base),
            "descartadas_sin_edad": sin_edad,
        },
        "controles": controles,
        "modelo": bitacora.resumen(),
        "salida": {"excel": str(destino_excel), "hojas": conteo},
    }
    (destino_corrida / "manifiesto.json").write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8")
    (destino_corrida / "llamadas_modelo.json").write_text(
        json.dumps([l.como_dict() for l in bitacora.llamadas],
                   ensure_ascii=False, indent=2),
        encoding="utf-8")
    return manifiesto


_ENC_INFO = ("id_fuente", "grupo_familiar", "parentesco", "edad_original",
             "provincia_original", "plan_original")
_ENC_DIST = ("id_fuente", "dimension", "valor", "cantidad", "observado")
_ENC_DIAG = ("id_fuente", "archivo", "formato", "fecha", "rol", "confianza",
             "origen", "lectura_completa", "observaciones")
_ENC_SUP = ("tipo", "id_fuente", "detalle", "nota")
_ENC_COB = ("id_fuente", "archivo", "rol_fuente", "ubicacion", "lectura",
            "tema", "detalle", "cita_textual", "confianza")
