"""US4 (A1): la versión nueva reemplaza la evidencia vigente, con revisión y auditoría."""
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.auditoria.models import RegistroAuditoria
from apps.documentos.models import Documento
from apps.notificaciones.models import Notificacion
from apps.versiones.models import Version
from apps.versiones.services import VersionService
from tests.factories import (MediaTestCase, cerrar_archivo, crear_documento,
                             crear_programa, crear_usuario)

V1 = b'%PDF-1.4 version original'
V2 = b'%PDF-1.4 version corregida'


def pdf(contenido, nombre='corregido.pdf'):
    return SimpleUploadedFile(nombre, contenido, content_type='application/pdf')


class VersionesTest(MediaTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.docente = crear_usuario('DOCENTE_PLANTA', programa=crear_programa())
        cls.coordinadora = crear_usuario('COORDINADOR')
        cls.decana = crear_usuario('DECANA')

    def subir(self, documento, usuario, contenido=V2):
        self.login(usuario)
        return self.client.post(f'/versiones/{documento.id}/crear/', {
            'archivo': pdf(contenido), 'descripcion_cambio': 'Corrección',
        })

    def descargar(self, documento):
        return cerrar_archivo(self.client.get(f'/documentos/{documento.id}/descargar/'))

    def test_docente_sube_version_de_aprobado_vuelve_a_revision_y_se_descarga_la_nueva(self):
        doc = crear_documento(self.docente, estado='APROBADO', contenido=V1)
        self.subir(doc, self.docente)
        doc.refresh_from_db()
        self.assertEqual(doc.estado, 'PENDIENTE')
        self.assertEqual(self.descargar(doc), V2)
        self.assertTrue(Notificacion.objects.filter(usuario=self.coordinadora, documento=doc).exists())
        self.assertTrue(RegistroAuditoria.objects.filter(accion='NUEVA_VERSION', documento=doc).exists())

    def test_original_se_conserva_como_v1(self):
        doc = crear_documento(self.docente, estado='APROBADO', contenido=V1)
        self.subir(doc, self.docente)
        numeros = list(Version.objects.filter(documento=doc).order_by('numero_version')
                       .values_list('numero_version', flat=True))
        self.assertEqual(numeros, [1, 2])
        v1 = Version.objects.get(documento=doc, numero_version=1)
        contenido = cerrar_archivo(self.client.get(f'/documentos/version/{v1.id}/descargar/'))
        self.assertEqual(contenido, V1)

    def test_rechazado_por_docente_vuelve_a_pendiente(self):
        doc = crear_documento(self.docente, estado='RECHAZADO')
        self.subir(doc, self.docente)
        doc.refresh_from_db()
        self.assertEqual(doc.estado, 'PENDIENTE')

    def test_directiva_mantiene_el_estado(self):
        doc = crear_documento(self.coordinadora, programa=crear_programa(), estado='APROBADO')
        self.subir(doc, self.coordinadora)
        doc.refresh_from_db()
        self.assertEqual(doc.estado, 'APROBADO')
        self.assertEqual(self.descargar(doc), V2)

    def test_numeracion_consecutiva_sin_repetir(self):
        doc = crear_documento(self.docente, estado='PENDIENTE')
        VersionService.crear_version(doc.id, pdf(b'%PDF a', 'a.pdf'), 'a', self.docente)
        VersionService.crear_version(doc.id, pdf(b'%PDF b', 'b.pdf'), 'b', self.docente)
        numeros = sorted(Version.objects.filter(documento=doc).values_list('numero_version', flat=True))
        self.assertEqual(numeros, [1, 2, 3])

    def test_restaurar_actualiza_el_vigente_y_audita(self):
        doc = crear_documento(self.docente, estado='APROBADO', contenido=V1)
        self.subir(doc, self.docente)
        v1 = Version.objects.get(documento=doc, numero_version=1)
        self.login(self.docente)
        self.client.post(f'/versiones/{v1.id}/restaurar/')
        self.assertEqual(self.descargar(doc), V1)
        self.assertTrue(RegistroAuditoria.objects.filter(
            accion='MODIFICO', documento=doc, detalle__contains='Restauró').exists())

    def test_docente_ajeno_no_puede_versionar(self):
        doc = crear_documento(self.docente, estado='APROBADO')
        otro = crear_usuario('DOCENTE_PLANTA', programa=self.docente.programa_academico)
        resp = self.subir(doc, otro)
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(RegistroAuditoria.objects.filter(accion='ACCESO_DENEGADO', usuario=otro).exists())
        self.assertFalse(Version.objects.filter(documento=doc).exists())
