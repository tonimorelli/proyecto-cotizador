"""Camino de la licitacion que llega como distribuciones agregadas.

Referencia: docs/handoff_v0.md, secciones 6.8, 6.9 y 6.10.

Sin padron individual: cantidades por rango etario y plan en una tabla, y la
provincia en otra que cubre solo a los titulares. El cruce se construye
condicionado al plan y la distribucion de titulares se extiende al resto por
la regla 6.9.
"""
from __future__ import annotations

import json
import time

from . import agente, agregados, escenarios, normalizacion, referencia, salida
from .cartera import (agregar_para_salida, aplicar_escenario,
                      comparar_escenarios, controlar_cierre, expandir_planes)
from .catalogos import (SIN_DATO, fuente_distingue_amba, homologar_plan,
                        homologar_provincia)


def intentar(f, path_cache):
    """Busca en una planilla una tabla cruzada de rango etario por plan."""
    import openpyxl

    if f.formato not in ("xlsx", "xlsm"):
        return None
    try:
        wb = openpyxl.load_workbook(f.ruta, data_only=True)
    except Exception:  # noqa: BLE001
        return None
    try:
        edad_plan = rep_edad = hoja_edad = None
        for hoja in wb.sheetnames:
            datos, rep = agregados.leer_cruzada_edad_plan(wb[hoja])
            if datos and rep.get("subpoblaciones"):
                edad_plan, rep_edad, hoja_edad = datos, rep, hoja
                break
        if not edad_plan:
            return None

        provincia_plan, rep_prov, hoja_prov = {}, {"bloques": []}, None
        for hoja in wb.sheetnames:
            if hoja == hoja_edad:
                continue
            datos, rep = agregados.leer_cruzada_provincia_plan(
                wb[hoja], rep_edad["subpoblaciones"])
            if datos:
                provincia_plan, rep_prov, hoja_prov = datos, rep, hoja
                break
    finally:
        wb.close()

    return {"fuente": f, "hoja_edad": hoja_edad, "hoja_prov": hoja_prov,
            "edad_plan": edad_plan, "rep_edad": rep_edad,
            "provincia_plan": provincia_plan, "rep_prov": rep_prov}


def procesar(ag, inventario, bitacora, cliente, diagnostico, supuestos,
             coberturas, encabezados, *, nombre_caso, carpeta, destino_excel,
             destino_corrida, path_tabla_st, path_cache, codigo, t0) -> dict:
    """Corre la licitacion agregada de punta a punta."""
    enc_info, enc_dist, enc_diag, enc_sup, enc_cob = encabezados
    f_pob = ag["fuente"]
    rep_edad = ag["rep_edad"]

    supuestos.append([
        "fuente de poblacion (agregada)", f_pob.id_fuente,
        f"{f_pob.nombre} / hoja {ag['hoja_edad']}",
        f"Tabla cruzada de rango etario por plan. Subpoblaciones: "
        f"{rep_edad['subpoblaciones']}. Segmentos: {rep_edad['segmentos']}. "
        f"Planes: {rep_edad['planes']}. Rangos: {rep_edad['rangos']}. "
        f"Total {rep_edad['total']:.0f}. Filas de subtotal ignoradas para no "
        f"duplicar: {rep_edad['filas_de_total_ignoradas']}."])

    # Las dos tablas cubren poblaciones distintas: una la poblacion completa,
    # la otra solo titulares. Eso descarta el reescalado de 6.10.
    total_titulares = sum(
        v for (_s, seg, _r, _p), v in ag["edad_plan"].items()
        if seg.strip().upper().startswith("TITULAR"))
    total_prov = sum(ag["provincia_plan"].values())

    chequeo = normalizacion.verificar_antes_de_cruzar([
        {"id_fuente": f_pob.id_fuente, "subpoblacion": "varias",
         "periodo": f_pob.fecha_nombre, "cobertura": "poblacion completa",
         "total": rep_edad["total"]},
        {"id_fuente": f_pob.id_fuente, "subpoblacion": "varias",
         "periodo": f_pob.fecha_nombre, "cobertura": "solo titulares",
         "total": total_prov}])
    supuestos.append([
        "verificacion previa al cruce", f_pob.id_fuente,
        f"apto_para_reescalar={chequeo['apto_para_reescalar']}, "
        f"requiere_revision_humana={chequeo['requiere_revision_humana']}",
        " | ".join(chequeo["hallazgos"]) + ". No se reescala: al diferir la "
        "cobertura corresponde la regla 6.9, no el total maestro de 6.10."])

    coinciden = abs(total_titulares - total_prov) < 1e-9
    supuestos.append([
        "control de cobertura de la tabla provincial", f_pob.id_fuente,
        f"titulares en la tabla etaria={total_titulares:.0f} vs total de la "
        f"tabla provincial={total_prov:.0f}",
        "coinciden" if coinciden else "NO COINCIDEN - revision humana"])
    if not coinciden:
        diagnostico.append(["", f_pob.nombre, "", "", "", "", "", "",
                            "la tabla provincial no cubre exactamente a los "
                            "titulares de la tabla etaria"])

    pesos = referencia.pesos_por_edad(path_cache)
    filas_crudas, rep_cruce = agregados.construir_cartera(
        ag["edad_plan"], ag["provincia_plan"], pesos, homologar_provincia,
        fuente_distingue_amba)

    supuestos.append([
        "cruce inferido", f_pob.id_fuente,
        f"{rep_cruce['cruces_condicionados']} cruces condicionados al plan, "
        f"{rep_cruce['cruces_por_marginal']} por marginal de subpoblacion",
        "La provincia no se observo cruzada con la edad. Se infiere "
        "CONDICIONADA AL PLAN, que es la dimension que ambas tablas comparten "
        "(6.8), no por independencia total. El supuesto de independencia "
        "queda restringido a edad contra provincia dentro de cada plan."])

    if rep_cruce["segmentos_por_regla_6_9"]:
        supuestos.append([
            "regla 6.9 - distribucion aplicada a un segmento no cubierto",
            f_pob.id_fuente, f"segmentos: {rep_cruce['segmentos_por_regla_6_9']}",
            "La distribucion provincial se observo solo sobre titulares y se "
            "aplica a los demas segmentos. Supuesto declarado: el grupo "
            "familiar reside donde reside el titular."])

    for clave, destino in rep_cruce["homologacion"].items():
        supuestos.append(["homologacion de provincia", f_pob.id_fuente,
                          clave, f"-> {destino}"])
    supuestos.append([
        "desambiguacion AMBA", f_pob.id_fuente,
        str(rep_cruce["distingue_amba"]),
        "La fuente nombra explicitamente el AMBA, la CABA o el GBA, asi que "
        "'Buenos Aires' a secas se interpreta como el interior de la "
        "provincia (6.5)."])
    if rep_cruce["sin_provincia"]:
        diagnostico.append(["", f_pob.nombre, "", "", "", "", "", "",
                            f"{rep_cruce['sin_provincia']:.0f} capitas sin "
                            f"distribucion provincial disponible"])

    # Plan observado pero no homologable: se conserva como dimension de
    # condicionamiento y la cartera se expande a las nueve alternativas.
    planes_originales, filas_base = {}, []
    for sub, edad, prov, plan_orig, cantidad in filas_crudas:
        homologado = homologar_plan(plan_orig)
        if homologado == SIN_DATO:
            planes_originales[plan_orig] = (
                planes_originales.get(plan_orig, 0.0) + cantidad)
        filas_base.append((sub, edad, prov,
                           None if homologado == SIN_DATO else homologado,
                           cantidad))
    for valor, n in sorted(planes_originales.items(), key=lambda x: -x[1]):
        supuestos.append([
            "plan no homologable", f_pob.id_fuente, valor,
            f"{n:.0f} capitas. Valor original conservado. Se uso como "
            f"dimension de condicionamiento del cruce y la cartera se expande "
            f"a las nueve alternativas de cotizacion."])

    base = expandir_planes(filas_base)
    tabla = escenarios.cargar(path_tabla_st)
    controles, bloques = {}, {}
    for esc in ("optimista", "pesimista"):
        filas_esc = aplicar_escenario(base, tabla, esc)
        controles[esc] = controlar_cierre(base, filas_esc, esc)
        bloques[esc] = agregar_para_salida(filas_esc)
    controles["comparacion_entre_escenarios"] = comparar_escenarios(
        bloques["optimista"], bloques["pesimista"])
    comparacion = controles["comparacion_entre_escenarios"]

    poblacion_total = sum(c for *_, c in filas_base)
    if abs(poblacion_total - rep_edad["total"]) > 1e-6 * rep_edad["total"]:
        raise RuntimeError(
            f"la cartera no conserva el total leido: {poblacion_total} vs "
            f"{rep_edad['total']}")
    supuestos.append([
        "control de cantidades", f_pob.id_fuente,
        f"leido={rep_edad['total']:.0f}, en cartera={poblacion_total:.6f}",
        f"{controles['optimista']['alternativas_controladas']} pares "
        f"(subpoblacion, alternativa) por escenario, tolerancia 1e-6. "
        f"{comparacion['combinaciones_comparadas']} combinaciones comparadas "
        f"entre escenarios sumando situ. Las alternativas no se suman."])

    dist_filas = []
    for (sub, seg, rango, plan), v in sorted(ag["edad_plan"].items()):
        etiqueta = (f"{rango[0]} a {rango[1]}" if rango[1] is not None
                    else f"{rango[0]} y mas")
        dist_filas.append([f_pob.id_fuente, f"{sub} | {seg}",
                           f"rango etario {etiqueta} | {plan}", v, "observado"])
    for (sub, prov, plan), v in sorted(ag["provincia_plan"].items()):
        dist_filas.append([f_pob.id_fuente, f"{sub} | TITULAR",
                           f"provincia {prov} | {plan}", v, "observado"])

    coberturas.extend(
        agente.recolectar_coberturas(cliente, bitacora, inventario))

    conteo = salida.escribir(
        destino_excel,
        bloques_optimista=bloques["optimista"],
        bloques_pesimista=bloques["pesimista"],
        bloques_recibida={},
        informacion_recibida=(enc_info, []),
        distribuciones=(enc_dist, dist_filas),
        diagnostico=(enc_diag, diagnostico),
        supuestos=(enc_sup, supuestos),
        coberturas=(enc_cob, coberturas),
        nota_recibida=("Ninguna fuente informa situacion terapeutica. La hoja "
                       "se emite vacia para que el esquema sea estable."))

    manifiesto = {
        "caso": nombre_caso, "carpeta": str(carpeta), "camino": "agregado",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "codigo": codigo, "duracion_s": round(time.time() - t0, 1),
        "entradas": [{"id_fuente": f.id_fuente, "archivo": f.nombre,
                      "bytes": f.bytes, "sha256": f.sha256, "rol": f.rol,
                      "confianza": f.confianza, "origen_rol": f.origen_rol,
                      "lectura_completa": f.lectura_completa}
                     for f in inventario],
        "referencia": {"tabla_escenarios": str(path_tabla_st),
                       "cache_distribucion": str(path_cache)},
        "poblacion": {
            "fuente": f_pob.id_fuente, "hoja_edad": ag["hoja_edad"],
            "hoja_provincia": ag["hoja_prov"],
            "subpoblaciones": rep_edad["subpoblaciones"],
            "segmentos": rep_edad["segmentos"],
            "personas_en_cartera": poblacion_total,
            "filas_leidas": len(ag["edad_plan"]) + len(ag["provincia_plan"]),
            "origen_mapeo_columnas": "codigo (tabla cruzada)",
            "combinaciones_edad_provincia_plan": len(filas_base)},
        "cruce": {k: v for k, v in rep_cruce.items() if k != "homologacion"},
        "controles": controles,
        "modelo": bitacora.resumen(),
        "salida": {"excel": str(destino_excel), "hojas": conteo},
    }
    (destino_corrida / "manifiesto.json").write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8")
    (destino_corrida / "llamadas_modelo.json").write_text(
        json.dumps([l.como_dict() for l in bitacora.llamadas],
                   ensure_ascii=False, indent=2), encoding="utf-8")
    return manifiesto
