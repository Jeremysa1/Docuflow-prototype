"""Spec 002: cada pantalla se renderiza con el shell nuevo para los roles que pueden abrirla."""
from apps.documentos.models import Documento
from apps.permisos.models import SolicitudAcceso
from apps.notificaciones.services import NotificacionService
from tests.factories import MediaTestCase, crear_documento, crear_programa, crear_usuario


class PantallasTest(MediaTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.prog = crear_programa()
        cls.decana = crear_usuario('DECANA')
        cls.coord = crear_usuario('COORDINADOR')
        cls.docente = crear_usuario('DOCENTE_PLANTA', programa=cls.prog)
        cls.otro = crear_usuario('DOCENTE_PLANTA', programa=cls.prog)

    def setUp(self):
        super().setUp()
        self.doc = crear_documento(self.docente, programa=self.prog, estado='PENDIENTE', factor_cna='F3',
                                   titulo='Plan docente')
        self.sensible = crear_documento(self.docente, programa=self.prog, estado='APROBADO',
                                        es_sensible=True, titulo='Acta reservada')
        borrado = crear_documento(self.docente, programa=self.prog, titulo='En papelera')
        Documento.all_objects.filter(pk=borrado.pk).update(is_deleted=True)
        SolicitudAcceso.objects.create(solicitante=self.otro, documento=self.doc, motivo='Revisión', estado='PENDIENTE')
        NotificacionService.crear_notificacion(self.docente, 'Tu evidencia fue revisada', documento=self.doc)

    def abrir(self, usuario, url, esperado=200):
        self.login(usuario)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, esperado, f'{usuario.rol} {url}')
        if esperado == 200:
            html = resp.content.decode()
            self.assertIn('sg-app', html, f'{url} no usa el shell nuevo')
        return resp

    def test_pantallas_de_evidencias(self):
        d = self.doc.id
        for usuario in (self.decana, self.coord, self.docente):
            for url in (
                '/documentos/dashboard/', '/documentos/busqueda/?q=plan', '/documentos/busqueda/',
                '/documentos/mis-documentos/', f'/documentos/{d}/', '/documentos/subir/',
                f'/documentos/{d}/editar/', f'/versiones/{d}/', f'/versiones/{d}/crear/',
                '/documentos/papelera/', '/notificaciones/', '/usuarios/perfil/',
            ):
                with self.subTest(rol=usuario.rol, url=url):
                    self.abrir(usuario, url)

    def test_pantallas_de_directivas(self):
        for usuario in (self.decana, self.coord):
            for url in ('/documentos/aprobar/', '/documentos/aprobar/?estado=APROBADO', '/auditoria/',
                        '/permisos/solicitudes/', f'/permisos/{self.doc.id}/accesos/'):
                with self.subTest(rol=usuario.rol, url=url):
                    self.abrir(usuario, url)
        self.abrir(self.decana, '/documentos/factores-cna/')
        self.abrir(self.decana, '/usuarios/gestion/')

    def test_detalle_bloqueado_para_docente_sin_permiso(self):
        html = self.abrir(self.otro, f'/documentos/{self.sensible.id}/').content.decode()
        self.assertIn('Esta evidencia necesita permiso', html)
        self.assertIn('dos de estas personas', html)

    def test_acceso_sin_sesion(self):
        for url in ('/login/', '/login/registro/', '/login/recuperar/'):
            with self.subTest(url=url):
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 200)
