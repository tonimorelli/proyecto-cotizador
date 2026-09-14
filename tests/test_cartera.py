"""Tests del nucleo de cartera. Sinteticos: corren sin datos reales."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cotizador.cartera import (  # noqa: E402
    ALTERNATIVA_OBSERVADA, ErrorDeCierre, agregar_para_salida,
    aplicar_escenario, comparar_escenarios, controlar_cierre, expandir_planes,
    totales_por_alternativa,
)
from cotizador.catalogos import GRUPOS_ETARIOS, PLANES  # noqa: E402

# Tabla de escenarios de juguete: una proporcion distinta por grupo, para que
# un error de indexado no pase desapercibido.
TABLA = {g: {"optimista": 0.01 * (i + 1), "pesimista": 0.02 * (i + 1)}
         for i, g in enumerate(GRUPOS_ETARIOS)}


class TestExpansionDePlanes(unittest.TestCase):
    def test_sin_plan_informado_da_nueve_alternativas(self):
        filas = [("unica", 30, "AMBA", None, 100.0)]
        base = expandir_planes(filas)
        self.assertEqual({f.alternativa for f in base}, set(PLANES))
        self.assertEqual(len(base), 9)

    def test_cada_alternativa_conserva_el_total_no_lo_multiplica(self):
        filas = [("unica", 30, "AMBA", None, 100.0),
                 ("unica", 40, "CORDOBA", None, 50.0)]
        totales = totales_por_alternativa(expandir_planes(filas))
        self.assertEqual(len(totales), 9)
        for clave, v in totales.items():
            self.assertAlmostEqual(v, 150.0, delta=1e-9, msg=clave)

    def test_todo_con_plan_observado_no_expande(self):
        filas = [("unica", 30, "AMBA", "SMG30", 100.0)]
        base = expandir_planes(filas)
        self.assertEqual(len(base), 1)
        self.assertEqual(base[0].alternativa, ALTERNATIVA_OBSERVADA)
        self.assertEqual(base[0].origen_plan, "observado")

    def test_cartera_mixta_repite_lo_observado_en_cada_alternativa(self):
        # 60 con plan observado, 40 sin plan. Cada alternativa debe sumar 100.
        filas = [("unica", 30, "AMBA", "SMG30", 60.0),
                 ("unica", 30, "AMBA", None, 40.0)]
        base = expandir_planes(filas)
        totales = totales_por_alternativa(base)
        self.assertEqual(len(totales), 9)
        for clave, v in totales.items():
            self.assertAlmostEqual(v, 100.0, delta=1e-9, msg=clave)
        # La porcion observada no cambia de plan entre alternativas.
        observadas = {f.plan for f in base if f.origen_plan == "observado"}
        self.assertEqual(observadas, {"SMG30"})

    def test_las_subpoblaciones_no_se_suman_entre_si(self):
        filas = [("empresa_a", 30, "AMBA", None, 100.0),
                 ("empresa_b", 30, "AMBA", None, 25.0)]
        totales = totales_por_alternativa(expandir_planes(filas))
        self.assertEqual(len(totales), 18)
        self.assertAlmostEqual(totales[("empresa_a", "S1")], 100.0, delta=1e-9)
        self.assertAlmostEqual(totales[("empresa_b", "S1")], 25.0, delta=1e-9)


class TestEscenariosYCierre(unittest.TestCase):
    def setUp(self):
        self.base = expandir_planes([
            ("empresa_a", 0, "AMBA", None, 7.0),
            ("empresa_a", 1, "AMBA", None, 13.0),
            ("empresa_a", 37, "CORDOBA", None, 111.111),
            ("empresa_b", 80, "SALTA", "SMG50", 9.5),
        ])

    def test_ambos_escenarios_cierran(self):
        # Poblacion real de la licitacion: 7 + 13 + 111.111 de empresa_a mas
        # 9.5 de empresa_b. Es la suma de las SUBPOBLACIONES, no de las
        # alternativas.
        poblacion = 7.0 + 13.0 + 111.111 + 9.5
        for esc in ("optimista", "pesimista"):
            filas = aplicar_escenario(self.base, TABLA, esc)
            resumen = controlar_cierre(self.base, filas, esc)
            self.assertEqual(resumen["escenario"], esc)
            self.assertAlmostEqual(resumen["total_licitacion"], poblacion,
                                   delta=1e-9)

    def test_todas_las_alternativas_cubren_la_misma_poblacion(self):
        filas = aplicar_escenario(self.base, TABLA, "optimista")
        resumen = controlar_cierre(self.base, filas, "optimista")
        por_alt = resumen["total_por_alternativa"]
        self.assertEqual(len(por_alt), 9)
        for alt, v in por_alt.items():
            self.assertAlmostEqual(v, resumen["total_licitacion"], delta=1e-9,
                                   msg=alt)

    def test_situ_0_mas_situ_1_reproduce_la_cantidad(self):
        filas = aplicar_escenario(self.base, TABLA, "optimista")
        self.assertEqual(len(filas), 2 * len(self.base))
        self.assertEqual({situ for *_, situ, _ in filas}, {0, 1})

    def test_la_edad_1_usa_la_proporcion_del_grupo_01(self):
        # Opcion 2 confirmada: las edades 0 y 1 comparten proporcion.
        filas = aplicar_escenario(self.base, TABLA, "optimista")
        p = {edad: c for _, _, edad, _, _, _, situ, c in filas
             if situ == 1 and edad in (0, 1)}
        self.assertAlmostEqual(p[0] / 7.0, TABLA["01"]["optimista"], places=12)
        self.assertAlmostEqual(p[1] / 13.0, TABLA["01"]["optimista"], places=12)

    def test_un_desvio_de_cierre_falla_ruidosamente(self):
        filas = aplicar_escenario(self.base, TABLA, "optimista")
        s, a, e, pr, pl, o, si, c = filas[0]
        filas[0] = (s, a, e, pr, pl, o, si, c + 1.0)
        with self.assertRaises(ErrorDeCierre):
            controlar_cierre(self.base, filas, "optimista")

    def test_las_cantidades_no_se_redondean(self):
        filas = aplicar_escenario(self.base, TABLA, "pesimista")
        cantidades = [c for *_, c in filas]
        self.assertTrue(any(c != round(c, 6) for c in cantidades))


class TestTotalDeLicitacion(unittest.TestCase):
    """Regresion: el total nunca suma entre alternativas de plan."""

    def test_cien_personas_sin_plan_son_cien_no_novecientas(self):
        base = expandir_planes([("unica", 30, "AMBA", None, 100.0)])
        for esc in ("optimista", "pesimista"):
            resumen = controlar_cierre(
                base, aplicar_escenario(base, TABLA, esc), esc)
            self.assertEqual(resumen["alternativas_controladas"], 9)
            self.assertAlmostEqual(resumen["total_licitacion"], 100.0,
                                   delta=1e-9)
            self.assertNotAlmostEqual(resumen["total_licitacion"], 900.0,
                                      delta=1.0)
            self.assertEqual(len(resumen["total_por_alternativa"]), 9)
            for alt, v in resumen["total_por_alternativa"].items():
                self.assertAlmostEqual(v, 100.0, delta=1e-9, msg=alt)

    def test_el_total_suma_subpoblaciones_dentro_de_una_alternativa(self):
        base = expandir_planes([("empresa_a", 30, "AMBA", None, 100.0),
                                ("empresa_b", 40, "SALTA", None, 25.0)])
        resumen = controlar_cierre(
            base, aplicar_escenario(base, TABLA, "optimista"), "optimista")
        self.assertAlmostEqual(resumen["total_licitacion"], 125.0, delta=1e-9)
        self.assertEqual(
            len(resumen["totales_por_subpoblacion_y_alternativa"]), 18)


class TestSalida(unittest.TestCase):
    def test_agrega_a_las_etiquetas_de_la_plantilla(self):
        base = expandir_planes([("unica", 1, "AMBA", "SMG30", 10.0)])
        filas = aplicar_escenario(base, TABLA, "optimista")
        bloques = agregar_para_salida(filas)
        self.assertEqual(list(bloques), [("unica", ALTERNATIVA_OBSERVADA)])
        claves = set(bloques[("unica", ALTERNATIVA_OBSERVADA)])
        self.assertEqual(
            claves, {("01) 0 a 1", "AMBA", "05) SMG30", 0),
                     ("01) 0 a 1", "AMBA", "05) SMG30", 1)})

    def test_cada_alternativa_es_un_bloque_separado(self):
        base = expandir_planes([("unica", 30, "AMBA", None, 100.0)])
        bloques = agregar_para_salida(aplicar_escenario(base, TABLA, "optimista"))
        self.assertEqual(len(bloques), 9)
        for clave, celdas in bloques.items():
            self.assertAlmostEqual(sum(celdas.values()), 100.0, delta=1e-9,
                                   msg=clave)

    def test_las_edades_0_y_1_colapsan_en_la_misma_celda(self):
        base = expandir_planes([("unica", 0, "AMBA", "S1", 4.0),
                                ("unica", 1, "AMBA", "S1", 6.0)])
        bloques = agregar_para_salida(aplicar_escenario(base, TABLA, "optimista"))
        celdas = bloques[("unica", ALTERNATIVA_OBSERVADA)]
        total = sum(v for (g, _, _, _), v in celdas.items() if g == "01) 0 a 1")
        self.assertAlmostEqual(total, 10.0, delta=1e-9)


class TestComparacionEntreEscenarios(unittest.TestCase):
    """Los escenarios difieren solo en situ: al sumarlo tienen que coincidir."""

    def setUp(self):
        self.base = expandir_planes([("unica", 0, "AMBA", None, 7.0),
                                     ("unica", 1, "AMBA", None, 13.0),
                                     ("unica", 70, "SALTA", None, 5.5)])
        self.opt = agregar_para_salida(
            aplicar_escenario(self.base, TABLA, "optimista"))
        self.pes = agregar_para_salida(
            aplicar_escenario(self.base, TABLA, "pesimista"))

    def test_coinciden_combinacion_por_combinacion(self):
        r = comparar_escenarios(self.opt, self.pes)
        self.assertGreater(r["combinaciones_comparadas"], 0)
        self.assertLess(r["maxima_diferencia_absoluta"], 1e-9)

    def test_detecta_una_combinacion_que_falta(self):
        clave = next(iter(self.pes))
        celda = next(iter(self.pes[clave]))
        del self.pes[clave][celda]
        with self.assertRaises(ErrorDeCierre):
            comparar_escenarios(self.opt, self.pes)

    def test_mover_cantidad_entre_situ_no_es_una_diferencia(self):
        # Los escenarios difieren justamente en como reparten situ. Mover
        # cantidad entre situ 0 y situ 1 de la MISMA combinacion es lo
        # esperado y no debe reportarse como discrepancia.
        clave = next(iter(self.pes))
        celdas = self.pes[clave]
        g, prov, plan, _ = next(iter(celdas))
        celdas[(g, prov, plan, 0)] += 1.0
        celdas[(g, prov, plan, 1)] -= 1.0
        comparar_escenarios(self.opt, self.pes)  # no levanta

    def test_detecta_cantidad_movida_entre_combinaciones_distintas(self):
        # Total general igual, combinaciones distintas: esto si es un error y
        # el control por total general no lo veria.
        clave = next(iter(self.pes))
        celdas = self.pes[clave]
        grupos = sorted({k[0] for k in celdas})
        self.assertGreater(len(grupos), 1, "el fixture necesita dos grupos")
        a = next(k for k in celdas if k[0] == grupos[0])
        b = next(k for k in celdas if k[0] == grupos[-1])
        celdas[a] += 1.0
        celdas[b] -= 1.0
        self.assertAlmostEqual(sum(celdas.values()),
                               sum(self.opt[clave].values()), delta=1e-9)
        with self.assertRaises(ErrorDeCierre):
            comparar_escenarios(self.opt, self.pes)


if __name__ == "__main__":
    unittest.main()
