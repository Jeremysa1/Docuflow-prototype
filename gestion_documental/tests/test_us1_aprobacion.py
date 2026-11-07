"""US1 (C1): la bandeja de aprobación carga para directivas con todos los filtros."""
from datetime import timedelta

from django.utils import timezone

from apps.documentos.models import Documento
from tests.factories import MediaTestCase, crear_documento, crear_programa, crear_usuario


class BandejaAprobacionTest(MediaTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.programa = crear_programa()
        cls.decana = crear_usuario('DECANA')
        cls.coordinadora = crear_usuario('COORDINADOR')
        cls.docente = crear_usuario('DOCENTE_PLANTA', programa=cls.programa)

    def setUp(self):
        super().setUp()
        self.reciente = crear_documento(self.docente, estado='PENDIENTE')
        self.viejo = crear_documento(self.docente, estado='PENDIENTE')
        hace_5 = timezone.now() - timedelta(days=5)
        Documento.objects.filter(pk=self.viejo.pk).update(fecha_modificacion=hace_5)

    def test_directivas_cargan_bandeja_con_todos_los_filtros(self):
        for usuario in (self.decana, self.coordinadora):
            self.login(usuario)
            for url in ('/documentos/aprobar/', '/documentos/aprobar/?estado=APROBADO',
                        '/documentos/aprobar/?urgente=1'):
                with self.subTest(rol=usuario.rol, url=url):
                    self.assertEqual(self.client.get(url).status_code, 200)

    def test_contador_de_urgentes_coincide_con_la_lista(self):
        self.login(self.decana)
        resp = self.client.get('/documentos/aprobar/?urgente=1')
        self.assertEqual(resp.context['docs_urgentes_count'], 1)
        self.assertTrue(resp.context['hay_urgentes'])
        ids = [d.id for d in resp.context['page_obj']]
        self.assertEqual(ids, [self.viejo.id])

    def test_docente_no_entra(self):
        self.login(self.docente)
        self.assertEqual(self.client.get('/documentos/aprobar/').status_code, 403)
