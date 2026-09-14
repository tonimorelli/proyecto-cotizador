"""Tests de los insumos reales. Se saltean si los datos no estan presentes.

Los datos no se commitean, asi que estos tests solo corren en una maquina que
tenga la carpeta Referencia/ local. Ver docs/decisiones_proyecto.md, entrada
"Politica de datos y de documentacion".
"""
import pathlib
import sys
import unittest

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from cotizador import escenarios, referencia  # noqa: E402
from cotizador.catalogos import (  # noqa: E402
    GRUPOS_ETARIOS, grupo_etario, grupo_referencia,
)

TABLA_ST = RAIZ / "Referencia" / "Escenarios_proporcion_ST.xlsx"
CACHE = RAIZ / "cache" / "distribucion_edad.csv"


@unittest.skipUnless(TABLA_ST.exists(), "falta la tabla de escenarios local")
class TestTablaEscenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tabla = escenarios.cargar(TABLA_ST)

    def test_estan_los_21_grupos(self):
        self.assertEqual(set(self.tabla), set(GRUPOS_ETARIOS))

    def test_proporciones_validas_y_ordenadas(self):
        for grupo, v in self.tabla.items():
            self.assertGreaterEqual(v["optimista"], 0.0, grupo)
            self.assertLessEqual(v["pesimista"], 1.0, grupo)
            self.assertLessEqual(v["optimista"], v["pesimista"], grupo)

    def test_el_tramo_abierto_repite_el_grupo_anterior(self):
        # Decision del 2026-09-13: para 96 y mas se respeta el tope de la tabla.
        self.assertEqual(self.tabla["21"], self.tabla["20"])

    def test_la_proporcion_tiene_forma_de_u(self):
        # La proporcion de ST no crece con la edad de punta a punta.
        # Arranca muy baja en la edad 0, sube hasta un maximo local en el
        # tramo de 6 a 10, cae hasta un minimo local en el de 26 a 30, y de
        # ahi crece de forma sostenida hasta el tramo abierto.
        for esc in ("optimista", "pesimista"):
            serie = {g: self.tabla[g][esc] for g in GRUPOS_ETARIOS}
            self.assertEqual(min(serie, key=serie.get), "01", esc)
            self.assertEqual(max(serie.values()), serie["21"], esc)
            intermedios = {g: v for g, v in serie.items() if g >= "02"}
            self.assertEqual(max(("02", "03", "04"), key=serie.get), "03", esc)
            self.assertEqual(min(intermedios, key=intermedios.get), "07", esc)
            creciente = [serie[g] for g in GRUPOS_ETARIOS if g >= "07"]
            self.assertEqual(creciente, sorted(creciente), esc)
            decreciente = [serie[g] for g in ("03", "04", "05", "06", "07")]
            self.assertEqual(decreciente, sorted(decreciente, reverse=True), esc)

    def test_proporcion_por_edad(self):
        self.assertEqual(
            escenarios.proporcion(self.tabla, 98, "optimista"),
            self.tabla[grupo_etario(98)]["optimista"],
        )
        with self.assertRaises(ValueError):
            escenarios.proporcion(self.tabla, 40, "medio")


@unittest.skipUnless(CACHE.exists(), "falta el precomputo: correr scripts/precomputar_referencia.py")
class TestDistribucionEtaria(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dist = referencia.cargar_distribucion(CACHE)

    def test_estan_los_21_grupos(self):
        self.assertEqual(set(self.dist), set(GRUPOS_ETARIOS))

    def test_cada_grupo_cierra_en_uno(self):
        for grupo, edades in self.dist.items():
            self.assertAlmostEqual(sum(edades.values()), 1.0, delta=1e-9, msg=grupo)

    def test_toda_edad_de_0_a_100_tiene_soporte(self):
        cubiertas = {e for edades in self.dist.values() for e in edades}
        self.assertEqual(cubiertas, set(range(0, 101)))

    def test_ninguna_edad_supera_el_tope(self):
        self.assertLessEqual(max(e for ed in self.dist.values() for e in ed), 100)

    def test_cada_edad_cae_en_el_grupo_de_la_referencia(self):
        # El CSV guarda el grupo tal como lo trae la referencia, que no es
        # nuestro agrupamiento de salida. Difieren en la edad 1.
        for grupo, edades in self.dist.items():
            for edad in edades:
                self.assertEqual(grupo_referencia(edad), grupo)


@unittest.skipUnless(CACHE.exists(), "falta el precomputo")
class TestDistribucionDeRangos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pesos = referencia.pesos_por_edad(CACHE)

    def test_hay_peso_para_toda_edad_de_0_a_100(self):
        self.assertEqual(set(self.pesos), set(range(0, 101)))

    def test_un_rango_que_cruza_grupos_cierra_en_la_cantidad_original(self):
        # 18 a 34 cruza cuatro grupos de la referencia: 05, 06, 07 y 08.
        reparto = referencia.distribuir_rango(self.pesos, 18, 34, 1000.0)
        self.assertEqual(set(reparto), set(range(18, 35)))
        self.assertAlmostEqual(sum(reparto.values()), 1000.0, delta=1e-9)

    def test_usa_pesos_absolutos_no_normalizados_por_grupo(self):
        # Si se normalizara dentro de cada grupo, dos edades con el mismo peso
        # absoluto en grupos distintos recibirian cantidades distintas.
        reparto = referencia.distribuir_rango(self.pesos, 18, 34, 1000.0)
        for a, b in ((20, 21), (25, 26), (30, 31)):  # pares a ambos lados de un limite
            esperado = self.pesos[a] / self.pesos[b]
            self.assertAlmostEqual(reparto[a] / reparto[b], esperado, places=9)

    def test_tramo_abierto_se_topea_en_100(self):
        reparto = referencia.distribuir_rango(self.pesos, 65, None, 500.0)
        self.assertEqual(max(reparto), 100)
        self.assertAlmostEqual(sum(reparto.values()), 500.0, delta=1e-9)

    def test_rango_que_excede_el_soporte_se_recorta(self):
        reparto = referencia.distribuir_rango(self.pesos, 98, 130, 7.0)
        self.assertEqual(max(reparto), 100)
        self.assertAlmostEqual(sum(reparto.values()), 7.0, delta=1e-9)

    def test_rango_de_una_sola_edad(self):
        self.assertEqual(referencia.distribuir_rango(self.pesos, 40, 40, 3.0), {40: 3.0})

    def test_rango_invalido(self):
        with self.assertRaises(ValueError):
            referencia.distribuir_rango(self.pesos, 50, 40, 1.0)


if __name__ == "__main__":
    unittest.main()
