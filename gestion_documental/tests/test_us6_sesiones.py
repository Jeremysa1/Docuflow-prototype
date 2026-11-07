"""US6 (A2): un usuario deshabilitado o inactivo pierde el acceso en su siguiente petición."""
from apps.usuarios.models import Usuario
from tests.factories import MediaTestCase, crear_programa, crear_usuario

PAGINA = '/documentos/dashboard/'


class SesionesCortadasTest(MediaTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.docente = crear_usuario('DOCENTE_PLANTA', programa=crear_programa())

    def test_habilitado_conserva_el_acceso(self):
        self.login(self.docente)
        self.assertEqual(self.client.get(PAGINA).status_code, 200)

    def test_deshabilitado_es_expulsado(self):
        self.login(self.docente)
        Usuario.objects.filter(pk=self.docente.pk).update(esta_habilitado=False)
        resp = self.client.get(PAGINA)
        self.assertRedirects(resp, '/login/', fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_inactivo_es_expulsado(self):
        self.login(self.docente)
        Usuario.objects.filter(pk=self.docente.pk).update(is_active=False)
        resp = self.client.get(PAGINA)
        self.assertEqual(resp.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_superusuario_no_habilitado_conserva_el_admin(self):
        admin = crear_usuario('DECANA', habilitado=False)
        self.login(admin)
        self.assertEqual(self.client.get('/admin/').status_code, 200)
