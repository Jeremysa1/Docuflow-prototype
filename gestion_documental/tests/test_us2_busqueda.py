"""US2 (C2): el resaltado de búsqueda nunca interpreta HTML de los títulos."""
import re

from tests.factories import MediaTestCase, crear_documento, crear_programa, crear_usuario

PAYLOAD = '<img src=x onerror=alert(1)>'


class BusquedaSeguraTest(MediaTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.programa = crear_programa()
        cls.decana = crear_usuario('DECANA')
        cls.docente = crear_usuario('DOCENTE_PLANTA', programa=cls.programa)

    def setUp(self):
        super().setUp()
        crear_documento(self.docente, estado='APROBADO', titulo=PAYLOAD)

    def test_titulo_malicioso_se_muestra_escapado(self):
        self.login(self.decana)
        html = self.client.get('/documentos/busqueda/', {'q': 'img'}).content.decode()
        self.assertIn('&lt;img src=x onerror=alert(1)&gt;', html)
        self.assertNotIn(PAYLOAD, html)

    def test_script_de_resaltado_no_usa_innerhtml(self):
        self.login(self.decana)
        html = self.client.get('/documentos/busqueda/', {'q': 'img'}).content.decode()
        self.assertIn('sa-highlight-target', html)
        # Spec 004: el resaltado vive en sigea.js (CSP sin scripts en línea)
        from django.contrib.staticfiles import finders
        js = open(finders.find('js/sigea.js'), encoding='utf-8').read()
        bloque = re.search(r"function iniciarResaltado\(\).*?\n  \}\n", js, re.S)
        self.assertIsNotNone(bloque, 'no se encontró el script de resaltado')
        self.assertNotIn('innerHTML', bloque.group(0))
