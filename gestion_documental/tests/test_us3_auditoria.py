"""US3 (C3, A6): auditoría con IP confiable y catálogo completo de eventos."""
from django.test import override_settings

from apps.auditoria.models import RegistroAuditoria as R
from apps.permisos.models import PermisoDocumento, SolicitudAcceso
from apps.usuarios.models import Usuario
from tests.factories import (MediaTestCase, cerrar_archivo, crear_documento,
                             crear_programa, crear_usuario)


def ultimo(accion, **filtros):
    return R.objects.filter(accion=accion, **filtros).order_by('-id').first()


class IpConfiableTest(MediaTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.autor = crear_usuario('DOCENTE_PLANTA', programa=crear_programa())

    def setUp(self):
        super().setUp()
        self.doc = crear_documento(self.autor, estado='APROBADO')
        self.login(self.autor)

    def descargar(self, xff):
        resp = self.client.get(f'/documentos/{self.doc.id}/descargar/', HTTP_X_FORWARDED_FOR=xff)
        cerrar_archivo(resp)
        return resp

    def test_cabecera_falsa_se_ignora_sin_proxy(self):
        resp = self.descargar('8.8.8.8')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(ultimo('DESCARGO').ip_address, '127.0.0.1')

    def test_cabecera_invalida_no_bloquea_la_accion(self):
        resp = self.descargar('no-es-una-ip')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(ultimo('DESCARGO').ip_address, '127.0.0.1')

    @override_settings(TRUSTED_PROXY_COUNT=1)
    def test_con_un_proxy_de_confianza_se_toma_la_entrada_del_proxy(self):
        self.descargar('1.1.1.1, 9.9.9.9')
        self.assertEqual(ultimo('DESCARGO').ip_address, '9.9.9.9')

    @override_settings(TRUSTED_PROXY_COUNT=1)
    def test_con_proxy_y_valor_invalido_queda_vacia(self):
        resp = self.descargar('basura')
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(ultimo('DESCARGO').ip_address)


class EventosSesionTest(MediaTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = crear_usuario('DOCENTE_PLANTA', email='docente.login@test.co',
                                    password='Clave-Segura-123!')

    def test_login_exitoso(self):
        self.client.post('/login/', {'email': 'docente.login@test.co', 'password': 'Clave-Segura-123!'})
        self.assertIsNotNone(ultimo('LOGIN', usuario=self.usuario))

    def test_login_fallido_con_correo_existente(self):
        self.client.post('/login/', {'email': 'docente.login@test.co', 'password': 'mala'})
        self.assertIsNotNone(ultimo('LOGIN_FALLIDO', usuario=self.usuario))

    def test_login_fallido_con_correo_inexistente_se_enmascara(self):
        self.client.post('/login/', {'email': 'abcdef@dominio.co', 'password': 'x'})
        reg = ultimo('LOGIN_FALLIDO')
        self.assertIsNone(reg.usuario)
        self.assertIn('ab***@dominio.co', reg.detalle)
        self.assertNotIn('abcdef', reg.detalle)

    def test_logout(self):
        self.client.force_login(self.usuario)
        self.client.post('/login/logout/')
        self.assertIsNotNone(ultimo('LOGOUT', usuario=self.usuario))


class EventosAccesoTest(MediaTestCase):
    @classmethod
    def setUpTestData(cls):
        prog = crear_programa()
        cls.autor = crear_usuario('DOCENTE_PLANTA', programa=prog)
        cls.solicitante = crear_usuario('DOCENTE_PLANTA', programa=prog)
        cls.coordinadora = crear_usuario('COORDINADOR')
        cls.decana = crear_usuario('DECANA')

    def setUp(self):
        super().setUp()
        self.doc = crear_documento(self.autor, estado='APROBADO')
        self.sensible = crear_documento(self.autor, estado='APROBADO', es_sensible=True)

    def solicitar(self, doc):
        self.login(self.solicitante)
        self.client.post(f'/permisos/{doc.id}/solicitar/', {'motivo': 'Necesito revisarlo'})
        return SolicitudAcceso.objects.get(solicitante=self.solicitante, documento=doc)

    def responder(self, usuario, solicitud, decision, motivo=''):
        self.login(usuario)
        self.client.post(f'/permisos/solicitud/{solicitud.id}/responder/',
                         {'decision': decision, 'motivo_rechazo': motivo})

    def test_solicitud_y_aprobacion_normal(self):
        sol = self.solicitar(self.doc)
        self.assertIsNotNone(ultimo('SOLICITO_ACCESO', usuario=self.solicitante, documento=self.doc))
        self.responder(self.autor, sol, 'APROBADA')
        self.assertIsNotNone(ultimo('APROBO_ACCESO', usuario=self.autor, documento=self.doc))

    def test_rechazo_normal(self):
        sol = self.solicitar(self.doc)
        self.responder(self.autor, sol, 'RECHAZADA', 'No corresponde')
        self.assertIsNotNone(ultimo('RECHAZO_ACCESO', usuario=self.autor, documento=self.doc))

    def test_votos_sensibles_y_resolucion(self):
        sol = self.solicitar(self.sensible)
        self.responder(self.coordinadora, sol, 'APROBADA')
        self.assertIsNotNone(ultimo('VOTO_ACCESO', usuario=self.coordinadora))
        self.assertIsNone(ultimo('APROBO_ACCESO', documento=self.sensible))
        self.responder(self.decana, sol, 'APROBADA')
        self.assertIsNotNone(ultimo('VOTO_ACCESO', usuario=self.decana))
        self.assertIsNotNone(ultimo('APROBO_ACCESO', documento=self.sensible))

    def test_revocacion(self):
        PermisoDocumento.objects.create(usuario=self.solicitante, documento=self.doc,
                                        puede_ver=True, puede_descargar=True)
        self.login(self.autor)
        self.client.post(f'/permisos/{self.doc.id}/usuario/{self.solicitante.id}/revocar/')
        self.assertIsNotNone(ultimo('REVOCO_ACCESO', usuario=self.autor, documento=self.doc))

    def test_regla_de_negocio_se_muestra_y_errores_internos_no(self):
        self.solicitar(self.doc)
        resp = self.client.post(f'/permisos/{self.doc.id}/solicitar/', {'motivo': 'otra vez'}, follow=True)
        textos = [str(m) for m in resp.context['messages']]
        self.assertTrue(any('pendiente' in t for t in textos), textos)

    def test_acceso_denegado_en_detalle_y_descarga(self):
        self.login(self.solicitante)
        self.client.get(f'/documentos/{self.doc.id}/')
        self.client.get(f'/documentos/{self.doc.id}/descargar/')
        self.assertEqual(R.objects.filter(accion='ACCESO_DENEGADO', usuario=self.solicitante,
                                          documento=self.doc).count(), 2)


class EventosUsuariosTest(MediaTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.decana = crear_usuario('DECANA')
        cls.programa = crear_programa()

    def setUp(self):
        super().setUp()
        self.login(self.decana)

    def test_ciclo_de_gestion_de_usuarios(self):
        self.client.post('/usuarios/gestion/agregar/', {
            'nombre': 'Ana', 'apellido': 'Gómez', 'email': 'ana.gomez@test.co',
            'rol': 'DOCENTE_PLANTA', 'programa_id': self.programa.id,
        })
        nuevo = Usuario.objects.get(email='ana.gomez@test.co')
        self.assertIn('ana.gomez@test.co', ultimo('CREO_USUARIO', usuario=self.decana).detalle)

        self.client.post(f'/usuarios/gestion/{nuevo.id}/habilitar/')
        self.client.post(f'/usuarios/gestion/{nuevo.id}/deshabilitar/')
        self.client.post(f'/usuarios/gestion/{nuevo.id}/editar/', {'rol': 'DOCENTE_PLANTA', 'programa_id': ''})
        self.client.post(f'/usuarios/gestion/{nuevo.id}/eliminar/')
        for accion in ('HABILITO_USUARIO', 'DESHABILITO_USUARIO', 'ACTUALIZO_USUARIO', 'ELIMINO_USUARIO'):
            with self.subTest(accion=accion):
                reg = ultimo(accion, usuario=self.decana)
                self.assertIsNotNone(reg)
                self.assertIn('ana.gomez@test.co', reg.detalle)


class EtiquetasTest(MediaTestCase):
    def test_acciones_heredadas_tienen_etiqueta_legible(self):
        self.assertEqual(R(accion='EDITO_METADATOS').get_accion_display(), 'Editó metadatos')
        self.assertEqual(R(accion='ACTUALIZO').get_accion_display(), 'Restauró documento')

    def test_filtro_de_la_lista_ofrece_todas_las_acciones(self):
        self.login(crear_usuario('DECANA'))
        html = self.client.get('/auditoria/').content.decode()
        for valor, _ in R.Accion.choices:
            self.assertIn(f'value="{valor}"', html)
