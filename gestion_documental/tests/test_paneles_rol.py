"""Spec 002: panel por rol con su banner, y visibilidad de datos por rol (Zero-Trust)."""
from datetime import timedelta

from django.utils import timezone

from apps.documentos.models import Documento
from tests.factories import MediaTestCase, crear_documento, crear_programa, crear_usuario

PANEL = '/documentos/dashboard/'


class PanelesPorRolTest(MediaTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.prog = crear_programa('Ingeniería de Software')
        cls.decana = crear_usuario('DECANA', first_name='Andrea')
        cls.coord = crear_usuario('COORDINADOR')
        cls.docente = crear_usuario('DOCENTE_PLANTA', programa=cls.prog)

    def setUp(self):
        super().setUp()
        for _ in range(4):
            crear_documento(self.docente, programa=self.prog, estado='APROBADO', factor_cna='F3')
        self.viejo = crear_documento(self.docente, estado='PENDIENTE', factor_cna='F10', titulo='Informe viejo')
        Documento.objects.filter(pk=self.viejo.pk).update(fecha_modificacion=timezone.now() - timedelta(days=7))
        self.rechazado = crear_documento(self.docente, estado='RECHAZADO', titulo='Acta rechazada',
                                         comentario_rechazo='Falta la firma')

    def html(self, usuario):
        self.login(usuario)
        resp = self.client.get(PANEL)
        self.assertEqual(resp.status_code, 200)
        return resp.content.decode()

    def test_decana_ve_huella_matriz_cola_y_pulso(self):
        html = self.html(self.decana)
        self.assertEqual(html.count('class="sg-huella__col"'), 12)
        self.assertIn('4 / 205', html)
        self.assertIn('sg-matriz', html)
        self.assertIn('Informe viejo', html)
        self.assertIn('1 con más de 3 días', html)
        self.assertIn('Accesos denegados', html)
        self.assertIn('?factor=F3&amp;programa=', html)

    def test_coordinadora_ve_su_cola_y_tiempos(self):
        html = self.html(self.coord)
        self.assertIn('tu cola de revisión', html)
        self.assertIn('Informe viejo', html)
        self.assertIn('7 días', html)
        self.assertIn('Tiempo de revisión', html)
        self.assertIn('sg-matriz', html)

    def test_docente_solo_ve_lo_suyo(self):
        html = self.html(self.docente)
        self.assertIn('tus evidencias del último año', html)
        self.assertIn('sg-huella--personal', html)
        self.assertIn('Falta la firma', html)
        self.assertIn('Subir evidencia', html)
        self.assertIn('sg-chip--codigo', html)
        for dato_de_facultad in ('/ 205', 'sg-matriz', 'Accesos denegados', 'Por revisar', 'aprobadas en la facultad'):
            with self.subTest(dato=dato_de_facultad):
                self.assertNotIn(dato_de_facultad, html)

    def test_facultad_vacia(self):
        Documento.all_objects.all().delete()
        html = self.html(self.decana)
        self.assertIn('0 / 205', html)
        self.assertIn('No hay evidencias por revisar', html)

    def test_navegacion_respeta_el_rol(self):
        html = self.html(self.docente)
        for destino in ('/documentos/factores-cna/', '/auditoria/', '/usuarios/gestion/', '/documentos/aprobar/'):
            with self.subTest(destino=destino):
                self.assertNotIn(f'href="{destino}"', html)
        html = self.html(self.decana)
        for destino in ('/documentos/factores-cna/', '/auditoria/', '/usuarios/gestion/', '/documentos/aprobar/'):
            with self.subTest(destino=destino):
                self.assertIn(f'href="{destino}"', html)
