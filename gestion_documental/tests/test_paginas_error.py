"""Spec 002: páginas 403, 404 y 500 propias, con camino de vuelta."""
from django.template.loader import render_to_string
from django.test import override_settings

from tests.factories import MediaTestCase, crear_programa, crear_usuario


class PaginasErrorTest(MediaTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.docente = crear_usuario('DOCENTE_PLANTA', programa=crear_programa())

    def test_403_del_sistema_para_docente_en_auditoria(self):
        self.login(self.docente)
        resp = self.client.get('/auditoria/')
        self.assertEqual(resp.status_code, 403)
        html = resp.content.decode()
        self.assertIn('No tienes acceso a esta sección', html)
        self.assertIn('Ir a tu panel', html)

    @override_settings(DEBUG=False)
    def test_404_propia(self):
        self.login(self.docente)
        resp = self.client.get('/documentos/999999/editar-inexistente/')
        self.assertEqual(resp.status_code, 404)
        self.assertIn('No encontramos esta página', resp.content.decode())

    def test_500_se_renderiza_sin_contexto_de_peticion(self):
        html = render_to_string('500.html')
        self.assertIn('Algo falló de nuestro lado', html)
        self.assertIn('Iniciar sesión', html)
