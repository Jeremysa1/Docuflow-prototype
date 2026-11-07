"""US5 (A3): la Coordinadora de facultad recibe los avisos aunque no tenga programa."""
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.documentos.services import DocumentoService
from apps.notificaciones.models import Notificacion
from apps.permisos.services import PermisoService
from apps.versiones.models import Version
from apps.versiones.services import VersionService
from tests.factories import (MediaTestCase, archivo, crear_categoria, crear_documento,
                             crear_programa, crear_usuario)


def subir(autor, programa):
    return DocumentoService.crear_documento(
        titulo='Evidencia', descripcion='', archivo=archivo(), programa=programa,
        categoria=crear_categoria(), autor=autor,
    )


class NotificacionesRevisoresTest(MediaTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.programa_a = crear_programa()
        cls.programa_b = crear_programa()
        cls.docente_b = crear_usuario('DOCENTE_PLANTA', programa=cls.programa_b)
        cls.decana = crear_usuario('DECANA')

    def test_coordinadora_sin_programa_recibe_aviso_de_cualquier_programa(self):
        coordinadora = crear_usuario('COORDINADOR', programa=None)
        doc = subir(self.docente_b, self.programa_b)
        self.assertTrue(Notificacion.objects.filter(usuario=coordinadora, documento=doc).exists())
        self.assertFalse(Notificacion.objects.filter(usuario=self.decana, documento=doc).exists())

    def test_sin_coordinadora_activa_avisa_a_la_decana(self):
        crear_usuario('COORDINADOR', habilitado=False)
        doc = subir(self.docente_b, self.programa_b)
        self.assertTrue(Notificacion.objects.filter(usuario=self.decana, documento=doc).exists())

    def test_documento_de_la_coordinadora_avisa_a_la_decana(self):
        coordinadora = crear_usuario('COORDINADOR')
        doc = DocumentoService.crear_documento(
            titulo='Plan', descripcion='', archivo=archivo(), programa=self.programa_a,
            categoria=crear_categoria(), autor=coordinadora, requiere_aprobacion=True,
        )
        self.assertTrue(Notificacion.objects.filter(usuario=self.decana, documento=doc).exists())
        self.assertFalse(Notificacion.objects.filter(usuario=coordinadora, documento=doc).exists())

    def test_solicitud_sensible_avisa_a_autor_coordinadora_y_decana_una_vez(self):
        coordinadora = crear_usuario('COORDINADOR')
        doc = crear_documento(self.docente_b, estado='APROBADO', es_sensible=True)
        solicitante = crear_usuario('DOCENTE_PLANTA', programa=self.programa_a)
        PermisoService.solicitar_acceso(solicitante, doc.id, 'Revisión')
        for usuario in (self.docente_b, coordinadora, self.decana):
            with self.subTest(usuario=usuario.rol):
                self.assertEqual(Notificacion.objects.filter(usuario=usuario, documento=doc).count(), 1)
        self.assertFalse(Notificacion.objects.filter(usuario=solicitante, documento=doc).exists())

    def test_restaurar_version_que_queda_pendiente_avisa_a_la_coordinadora(self):
        coordinadora = crear_usuario('COORDINADOR', programa=None)
        doc = crear_documento(self.docente_b, estado='APROBADO')
        VersionService.crear_version(doc.id, SimpleUploadedFile('n.pdf', b'%PDF n'), 'n', self.docente_b)
        doc.refresh_from_db()
        doc.estado = 'APROBADO'
        doc.save(update_fields=['estado'])
        Notificacion.objects.all().delete()
        v1 = Version.objects.get(documento=doc, numero_version=1)
        VersionService.restaurar_version(v1.id, self.docente_b)
        self.assertTrue(Notificacion.objects.filter(usuario=coordinadora, documento=doc).exists())
