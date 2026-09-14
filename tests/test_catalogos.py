"""Tests de catalogos y homologacion. No dependen de datos reales."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cotizador.catalogos import (  # noqa: E402
    EDAD_MAX, ETIQUETA_GRUPO, ETIQUETA_PLAN, GRUPOS_ETARIOS, PLANES, PROVINCIAS,
    SIN_DATO, codigo_de_etiqueta, grupo_etario, grupo_referencia, homologar_plan,
    homologar_provincia, normalizar,
)


class TestCatalogos(unittest.TestCase):
    def test_tamanos_de_catalogo(self):
        self.assertEqual(len(PROVINCIAS), 24)
        self.assertEqual(len(PLANES), 9)
        self.assertEqual(len(GRUPOS_ETARIOS), 21)

    def test_grupo_de_salida_sigue_la_etiqueta_literal(self):
        # Opcion 2, confirmada: "01) 0 a 1" contiene las edades 0 y 1.
        self.assertEqual(grupo_etario(0), "01")
        self.assertEqual(grupo_etario(1), "01")
        self.assertEqual(grupo_etario(2), "02")
        self.assertEqual(grupo_etario(5), "02")
        self.assertEqual(grupo_etario(6), "03")

    def test_grupo_de_referencia_sigue_el_agrupamiento_del_archivo(self):
        # La referencia agrupa al reves de su propia etiqueta.
        self.assertEqual(grupo_referencia(0), "01")
        self.assertEqual(grupo_referencia(1), "02")
        self.assertEqual(grupo_referencia(5), "02")
        self.assertEqual(grupo_referencia(6), "03")

    def test_los_dos_agrupamientos_difieren_solo_en_la_edad_1(self):
        distintas = [e for e in range(0, EDAD_MAX + 1)
                     if grupo_etario(e) != grupo_referencia(e)]
        self.assertEqual(distintas, [1])

    def test_las_etiquetas_cubren_el_catalogo(self):
        self.assertEqual(set(ETIQUETA_GRUPO), set(GRUPOS_ETARIOS))
        self.assertEqual(set(ETIQUETA_PLAN), set(PLANES))
        self.assertEqual(ETIQUETA_GRUPO["01"], "01) 0 a 1")
        self.assertEqual(ETIQUETA_PLAN["S1"], "01) S1")

    def test_toda_edad_valida_tiene_grupo(self):
        for edad in range(0, EDAD_MAX + 1):
            self.assertIn(grupo_etario(edad), GRUPOS_ETARIOS)

    def test_tramo_abierto(self):
        for edad in (96, 100, 106):
            self.assertEqual(grupo_etario(edad), "21")

    def test_codigo_tolera_relleno_y_espacios_multiples(self):
        self.assertEqual(codigo_de_etiqueta("01)   0 a 1    "), "01")
        self.assertEqual(codigo_de_etiqueta("01) 0 a 1"), "01")
        self.assertEqual(codigo_de_etiqueta("21) +"), "21")

    def test_normalizar_saca_acentos_y_espacios(self):
        self.assertEqual(normalizar("  Santa   Fé "), "santa fe")
        self.assertEqual(normalizar("Río Negro"), "rio negro")
        self.assertEqual(normalizar(None), "")


class TestHomologarProvincia(unittest.TestCase):
    def test_area_metropolitana(self):
        for v in ("Capital Federal", "CABA", "Buenos Aires-GBA", "AMBA"):
            self.assertEqual(homologar_provincia(v), "AMBA", v)

    def test_buenos_aires_sin_distinguir_va_a_amba(self):
        self.assertEqual(homologar_provincia("Buenos Aires"), "AMBA")

    def test_buenos_aires_cuando_la_fuente_distingue(self):
        self.assertEqual(
            homologar_provincia("Buenos Aires", fuente_distingue_amba=True),
            "BUENOS AIRES",
        )

    def test_la_localidad_tiene_prioridad(self):
        self.assertEqual(
            homologar_provincia("Buenos Aires", fuente_distingue_amba=True,
                                localidad_es_amba=True),
            "AMBA",
        )
        self.assertEqual(
            homologar_provincia("Buenos Aires", localidad_es_amba=False),
            "BUENOS AIRES",
        )

    def test_insensible_a_acentos(self):
        self.assertEqual(homologar_provincia("Santa Fé"), "SANTA FE")
        self.assertEqual(homologar_provincia("Entre Ríos"), "ENTRE RIOS")
        self.assertEqual(homologar_provincia("Córdoba"), "CORDOBA")

    def test_no_inventa_mapeos(self):
        self.assertEqual(homologar_provincia("Provincia X"), SIN_DATO)
        self.assertEqual(homologar_provincia(""), SIN_DATO)
        self.assertEqual(homologar_provincia(None), SIN_DATO)


class TestHomologarPlan(unittest.TestCase):
    def test_planes_propios(self):
        for p in PLANES:
            self.assertEqual(homologar_plan(p), p)
        self.assertEqual(homologar_plan(" smg20 "), "SMG20")

    def test_planes_ajenos_quedan_sin_dato(self):
        # Planes de otro financiador. No son homologables y no se inventan.
        for v in ("A", "B", "XX99", "MS2", ""):
            self.assertEqual(homologar_plan(v), SIN_DATO, v)


if __name__ == "__main__":
    unittest.main()
