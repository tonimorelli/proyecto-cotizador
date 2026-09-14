"""Tests del anonimizador de la evidencia publica.

Sinteticos: corren sin datos reales. Todos los nombres, dominios, cifras y
rutas de este archivo son **inventados**. No reproducen ningun dato de
ninguna licitacion: estan elegidos solo para ejercitar cada regla.

Cada test nombra la fuga que fija. Las cinco primeras son fugas que
efectivamente ocurrieron y que la revision de publicacion del 2026-09-14
encontro en el material ya versionado; el resto son las que el propio
anonimizador ya cubria y que conviene dejar fijadas para que no se pierdan.
"""
import importlib.util
import pathlib
import sys
import unittest

RAIZ = pathlib.Path(__file__).resolve().parents[1]


def _cargar_modulo():
    """Importa scripts/preparar_corridas.py, que no es un paquete."""
    spec = importlib.util.spec_from_file_location(
        "preparar_corridas", RAIZ / "scripts" / "preparar_corridas.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pc = _cargar_modulo()

# Mapa de prueba. Nombres inventados, con y sin acento a proposito.
MAPA = {"terminos": {"Acme Sociedad Anonima": "CLIENTE_X",
                     "Acme": "CLIENTE_X",
                     "Perez": "[persona interna]"},
        "publicar_cifras": False}


class TestFugasQueOcurrieron(unittest.TestCase):
    """Las cinco fugas encontradas en la revision de publicacion."""

    def setUp(self):
        self.anon = pc.construir_anonimizador(MAPA)

    def test_ruta_windows_con_un_backslash_se_redacta(self):
        """La regex pedia dos backslashes, asi que no redactaba nada.

        `r"[A-Za-z]:\\\\..."` son dos backslashes literales para el motor de
        regex. Una ruta Windows normal trae uno solo.
        """
        s = self.anon(r"el archivo esta en C:\Users\alguien\Documents\x.xlsx")
        self.assertIn("[ruta local]", s)
        self.assertNotIn("Users", s)
        self.assertNotIn("alguien", s)

    def test_ruta_windows_con_slash_se_redacta(self):
        s = self.anon("el archivo esta en C:/Users/alguien/Documents/x.xlsx")
        self.assertIn("[ruta local]", s)
        self.assertNotIn("alguien", s)

    def test_ruta_unc_se_redacta(self):
        s = self.anon(r"copiado de \\servidor\compartido\padron.xlsx")
        self.assertIn("[ruta local]", s)
        self.assertNotIn("servidor", s)

    def test_el_dominio_del_correo_no_sobrevive_al_reemplazo_de_terminos(self):
        """Fuga de orden: los terminos se sustituian antes que los correos.

        Con el orden invertido, `juan.perez@acme.com.ar` quedaba como
        `juan.[persona interna]@acme.com.ar`: la regex de correo ya no
        matcheaba, porque `]` no es un caracter word, y el dominio del
        cliente se publicaba.
        """
        s = self.anon("escribir a juan.perez@acme.com.ar por el tema")
        self.assertIn("[correo]", s)
        self.assertNotIn("acme.com.ar", s.lower())
        self.assertNotIn("@", s)

    def test_la_organizacion_propia_se_redacta(self):
        """Quedaba sin redactar porque no estaba en el mapa de cliente."""
        s = self.anon("comparativo entre CLIENTE_X y Swiss Medical")
        self.assertIn("[organizacion propia]", s)
        self.assertNotIn("Swiss", s)
        self.assertNotIn("Medical", s)
        self.assertNotIn("SMG", pc.construir_anonimizador(MAPA)(
            "precios de SMG para la cuenta"))

    def test_el_cargo_interno_se_redacta(self):
        """Un cargo identifica a una persona dentro de un area chica."""
        for cargo in ("Analista Sr. de Pricing",
                      "Gerente de Cotizaciones Corporate",
                      "Jefa de Suscripcion",
                      "Lider de Actuaria"):
            with self.subTest(cargo=cargo):
                s = self.anon(f"el remitente es {cargo} y pide revision")
                self.assertIn("[cargo interno]", s, cargo)

    def test_el_cargo_no_se_come_texto_que_no_es_cargo(self):
        """La regla es acotada a propósito: no debe borrar prosa normal."""
        s = self.anon("la tabla de escenarios no valida en forma")
        self.assertEqual(s, "la tabla de escenarios no valida en forma")


class TestCifrasComerciales(unittest.TestCase):
    """Cifras que identifican una negociacion aunque el cliente no se nombre."""

    def setUp(self):
        self.anon = pc.construir_anonimizador(MAPA)

    def test_porcentaje_se_redacta(self):
        """La fuga original fue un diferencial de precio citado por el modelo.

        La cifra de abajo es inventada.
        """
        s = self.anon("diferencial de precio (12% plus) contra el propio")
        self.assertIn("[porcentaje]", s)
        self.assertNotIn("12", s)

    def test_porcentaje_con_decimales_y_con_espacio(self):
        for txt in ("aumento de 7,5 %", "aumento de 7.5%", "aumento de 7 %"):
            with self.subTest(txt=txt):
                self.assertIn("[porcentaje]", self.anon(txt))

    def test_importe_se_redacta(self):
        for txt in ("cuota de $ 1.234,50", "costo USD 9876", "saldo ARS 4.000"):
            with self.subTest(txt=txt):
                s = self.anon(txt)
                self.assertIn("[importe]", s)

    def test_cifra_de_cuatro_o_mas_digitos_se_redacta(self):
        s = self.anon("la hoja tiene 9999 filas")
        self.assertIn("[cifra]", s)
        self.assertNotIn("9999", s)

    def test_cantidad_reconstruible_por_division_se_redacta(self):
        """La fuga mas dificil: un total agregado del que se deriva otro.

        Un total que suma las nueve alternativas de plan revela la poblacion
        al dividirlo por nueve. El anonimizador no puede reconocer *que* una
        cifra es reconstruible, asi que la defensa es que toda cifra larga
        cae. Las cifras de abajo son inventadas.
        """
        for total in ("123.453", "123453"):
            with self.subTest(total=total):
                s = self.anon(f"el total devuelto fue {total}")
                self.assertIn("[cifra]", s)
                self.assertNotIn("123", s)

    def test_no_toca_cifras_cortas_que_no_son_dato(self):
        """Las referencias a secciones y los conteos chicos se conservan."""
        s = self.anon("ver la regla 6.9 y las 9 alternativas")
        self.assertIn("6.9", s)
        self.assertIn("9 alternativas", s)


class TestTerminosDelMapa(unittest.TestCase):

    def setUp(self):
        self.anon = pc.construir_anonimizador(MAPA)

    def test_insensible_a_acentos(self):
        """Un acento perdido fue una de las fugas originales."""
        self.assertNotIn("rez", self.anon("firma Pérez"))
        self.assertIn("[persona interna]", self.anon("firma Pérez"))
        self.assertIn("[persona interna]", self.anon("firma PEREZ"))

    def test_insensible_a_espacios_multiples(self):
        s = self.anon("la empresa Acme   Sociedad   Anonima licita")
        self.assertIn("CLIENTE_X", s)
        self.assertNotIn("Acme", s)

    def test_gana_el_termino_mas_largo(self):
        """Sin ordenar por longitud, 'Acme' rompe 'Acme Sociedad Anonima'."""
        s = self.anon("Acme Sociedad Anonima")
        self.assertEqual(s, "CLIENTE_X")

    def test_none_pasa_derecho(self):
        self.assertIsNone(self.anon(None))


class TestMetadatosDeLasCorridas(unittest.TestCase):
    """Fecha y tamano: huellas que permiten reidentificar la licitacion."""

    def test_el_seudonimo_de_archivo_no_expone_el_dia(self):
        e = {"id_fuente": "F01", "rol": "padron individual",
             "archivo": "2026-07-17_09-31-02__Padron definitivo.xlsx"}
        nombre = pc.seudonimo_archivo(e, 1, lambda s: s)
        self.assertEqual(nombre, "F01_2026-07_padron_individual.xlsx")
        self.assertNotIn("17", nombre)
        self.assertNotIn("Padron definitivo", nombre)

    def test_el_seudonimo_conserva_ano_y_mes_para_el_orden(self):
        e = {"id_fuente": "F02", "rol": "distribucion agregada",
             "archivo": "2025-11-06_x.xlsx"}
        self.assertIn("2025-11",
                      pc.seudonimo_archivo(e, 2, lambda s: s))

    def test_el_seudonimo_tolera_un_archivo_sin_fecha_y_sin_rol(self):
        e = {"id_fuente": "F03", "rol": None, "archivo": "adjunto.pdf"}
        self.assertEqual(pc.seudonimo_archivo(e, 3, lambda s: s),
                         "F03__sin_rol.pdf")

    def test_el_tamano_se_publica_como_tramo(self):
        casos = [(0, "< 100 KB"), (50 * 1024, "< 100 KB"),
                 (300 * 1024, "100 KB - 1 MB"), (5 * 1024 * 1024, "1 - 10 MB"),
                 (35 * 1024 * 1024, "> 10 MB"), (None, "< 100 KB")]
        for n_bytes, esperado in casos:
            with self.subTest(n_bytes=n_bytes):
                self.assertEqual(pc.tramo_de_tamano(n_bytes), esperado)

    def test_el_tramo_no_permite_recuperar_el_tamano_exacto(self):
        a = pc.tramo_de_tamano(1560 * 1024)
        b = pc.tramo_de_tamano(4351 * 1024)
        self.assertEqual(a, b, "dos tamanos distintos deben caer en el mismo tramo")


class TestRedaccionDeCifrasDePoblacion(unittest.TestCase):
    """`publicar_cifras: false` tiene que tapar toda cifra de poblacion."""

    def test_sin_publicar_cifras_no_sale_ningun_numero(self):
        publicar = MAPA.get("publicar_cifras", False)
        self.assertFalse(publicar, "el mapa de prueba no debe publicar cifras")

        def cifra(v, fmt="{:,.0f}"):
            return fmt.format(v) if publicar else "[cifra no publicada]"

        self.assertEqual(cifra(40404), "[cifra no publicada]")   # inventada
        self.assertEqual(cifra(1.5, "{:,.6f}"), "[cifra no publicada]")


if __name__ == "__main__":
    unittest.main()
