"""US7 (A4): vista previa protegida, solo PDF, sin servicios externos ni /media/ directo."""
import importlib
import os

from django.test import override_settings
from django.urls import clear_url_caches

from apps.auditoria.models import RegistroAuditoria
from tests.factories import (MediaTestCase, cerrar_archivo, crear_documento,
                             crear_programa, crear_usuario)


class VistaPreviaTest(MediaTestCase):
    @classmethod
    def setUpTestData(cls):
        prog = crear_programa()
        cls.autor = crear_usuario('DOCENTE_PLANTA', programa=prog)
        cls.ajeno = crear_usuario('DOCENTE_PLANTA', programa=prog)

    def setUp(self):
        super().setUp()
        self.pdf = crear_documento(self.autor, estado='APROBADO')
        self.docx = crear_documento(self.autor, estado='APROBADO', nombre='informe.docx',
                                    contenido=b'PK\x03\x04 docx')

    def url(self, doc):
        return f'/documentos/{doc.id}/vista-previa/'

    def test_pdf_permitido_se_muestra_en_linea_y_se_audita(self):
        self.login(self.autor)
        resp = self.client.get(self.url(self.pdf))
        cerrar_archivo(resp)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        self.assertTrue(resp['Content-Disposition'].startswith('inline'))
        self.assertEqual(resp['X-Content-Type-Options'], 'nosniff')
        self.assertTrue(RegistroAuditoria.objects.filter(
            accion='VISUALIZO', usuario=self.autor, documento=self.pdf).exists())

    def test_sin_acceso_se_niega_y_se_audita(self):
        self.login(self.ajeno)
        resp = self.client.get(self.url(self.pdf))
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(RegistroAuditoria.objects.filter(
            accion='ACCESO_DENEGADO', usuario=self.ajeno, documento=self.pdf).exists())

    def test_office_no_tiene_vista_previa(self):
        self.login(self.autor)
        self.assertEqual(self.client.get(self.url(self.docx)).status_code, 404)

    def test_archivo_faltante_responde_404_generico(self):
        os.remove(self.pdf.archivo.path)
        self.login(self.autor)
        resp = self.client.get(self.url(self.pdf))
        self.assertEqual(resp.status_code, 404)
        self.assertNotIn(self.pdf.archivo.name, resp.content.decode(errors='ignore'))

    def test_detalle_no_expone_media_ni_google(self):
        self.login(self.autor)
        for doc in (self.pdf, self.docx):
            html = self.client.get(f'/documentos/{doc.id}/').content.decode()
            with self.subTest(doc=doc.archivo.name):
                self.assertNotIn('/media/', html)
                self.assertNotIn('docs.google.com', html)
                self.assertIn(f'/documentos/{doc.id}/', html)

    def test_historial_de_versiones_no_expone_media(self):
        from apps.versiones.services import VersionService
        from django.core.files.uploadedfile import SimpleUploadedFile
        VersionService.crear_version(self.pdf.id, SimpleUploadedFile('v.pdf', b'%PDF v'), 'v', self.autor)
        self.login(self.autor)
        html = self.client.get(f'/versiones/{self.pdf.id}/').content.decode()
        self.assertNotIn('/media/', html)

    def test_media_no_se_sirve_ni_en_debug(self):
        import config.urls
        try:
            with override_settings(DEBUG=True):
                importlib.reload(config.urls)
                clear_url_caches()
                resp = self.client.get('/media/' + self.pdf.archivo.name)
                self.assertEqual(resp.status_code, 404)
        finally:
            importlib.reload(config.urls)
            clear_url_caches()
