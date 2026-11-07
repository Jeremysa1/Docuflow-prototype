"""Spec 004: cierre de los riesgos medios (M2–M9) y bajos de la auditoría."""
import io
import re
import zipfile

from django.core import mail
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.documentos.models import Documento
from apps.documentos.services import DocumentoService
from apps.usuarios.models import Usuario
from core.utils.helpers import ReglaNegocioError, validar_archivo_subido
from tests.factories import MediaTestCase, crear_documento, crear_programa, crear_usuario

CLAVE = 'Clave-Segura-123!'


def _ooxml(carpeta):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('[Content_Types].xml', '<Types/>')
        z.writestr(f'{carpeta}document.xml', '<x/>')
    return buf.getvalue()


class LoginLimitesTest(TestCase):
    """M2: nadie bloquea a otra persona; los límites son por IP y por cuenta+IP."""

    def setUp(self):
        cache.clear()
        self.decana = crear_usuario('DECANA', password=CLAVE)

    def intentar(self, clave, ip):
        return self.client.post('/login/', {'email': self.decana.email, 'password': clave}, REMOTE_ADDR=ip)

    def test_fallos_desde_otra_ip_no_bloquean_a_la_decana(self):
        for _ in range(6):
            self.intentar('mala', '10.0.0.66')
        resp = self.intentar(CLAVE, '10.0.0.7')
        self.assertRedirects(resp, '/documentos/dashboard/', fetch_redirect_response=False)

    def test_la_ip_que_abusa_queda_frenada_aun_con_la_clave_correcta(self):
        for _ in range(5):
            self.intentar('mala', '10.0.0.66')
        resp = self.intentar(CLAVE, '10.0.0.66')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'No pudimos verificar tu identidad')

    def test_limite_por_ip_cubre_muchas_cuentas(self):
        for n in range(10):
            self.client.post('/login/', {'email': f'nadie{n}@test.co', 'password': 'x'}, REMOTE_ADDR='10.0.0.99')
        resp = self.intentar(CLAVE, '10.0.0.99')
        self.assertEqual(resp.status_code, 200)


class RecuperacionSinEnumeracionTest(TestCase):
    """M3: la recuperación responde igual exista o no el correo."""

    def setUp(self):
        cache.clear()
        self.usuario = crear_usuario(email='real@test.co')

    def flujo(self, email):
        c = self.client_class()
        c.post('/login/recuperar/', {'email': email})
        confirmar = c.get('/login/recuperar/confirmar/').content.decode()
        token = c.post('/login/recuperar/token/', {'token': '999999'}).content.decode()
        limpiar = lambda h: re.sub(r'name="csrfmiddlewaretoken" value="[^"]+"', '', h)
        return limpiar(confirmar).replace(email[:2], '??'), limpiar(token)

    def test_pantallas_identicas(self):
        real = self.flujo('real@test.co')
        falso = self.flujo('nadie@test.co')
        self.assertEqual(real[1], falso[1])
        self.assertIn('El código no es válido o ya expiró', real[1])
        self.assertIn('Lo mandaremos a', falso[0])


class PoliticaUnicaTest(TestCase):
    """M4: recuperación usa la misma política que el resto."""

    def test_cambiar_contrasena_usa_validate_password(self):
        from apps.usuarios.services import UsuarioService
        u = crear_usuario()
        for mala in ('corta1!', 'sinmayuscula123!', 'SinSimbolo1234', '12345678'):
            with self.subTest(clave=mala):
                self.assertFalse(UsuarioService.cambiar_contrasena(u.email, mala)['exito'])
        self.assertTrue(UsuarioService.cambiar_contrasena(u.email, 'Evidencia-CNA-2026!')['exito'])


class InvitacionTest(TestCase):
    """M8: los usuarios creados por la Decana reciben invitación y pueden entrar."""

    def setUp(self):
        cache.clear()
        self.decana = crear_usuario('DECANA')
        self.client.force_login(self.decana)

    def test_crear_envia_invitacion_y_el_enlace_es_de_un_solo_uso(self):
        prog = crear_programa()
        self.client.post('/usuarios/gestion/agregar/', {
            'nombre': 'Ana', 'apellido': 'Ríos', 'email': 'ana@test.co',
            'rol': 'DOCENTE_PLANTA', 'programa_id': prog.pk,
        })
        nuevo = Usuario.objects.get(email='ana@test.co')
        self.assertTrue(nuevo.esta_habilitado)
        self.assertEqual(len(mail.outbox), 1)
        enlace = re.search(r'http://testserver(/login/invitacion/[^\s]+)', mail.outbox[0].body).group(1)

        self.client.logout()
        self.assertEqual(self.client.get(enlace).status_code, 200)
        resp = self.client.post(enlace, {'nueva_contrasena': 'Evidencia-CNA-2026!',
                                         'confirmar_contrasena': 'Evidencia-CNA-2026!'})
        self.assertRedirects(resp, '/login/', fetch_redirect_response=False)
        nuevo.refresh_from_db()
        self.assertTrue(nuevo.check_password('Evidencia-CNA-2026!'))
        self.assertEqual(self.client.get(enlace).status_code, 400)

    def test_enlace_alterado(self):
        self.client.logout()
        self.assertEqual(self.client.get('/login/invitacion/MQ/abc-123/').status_code, 400)


class RegistroTest(TestCase):
    """M9: correo válido y límite por IP."""

    def setUp(self):
        cache.clear()

    def registrar(self, email, ip='10.1.1.1'):
        return self.client.post('/login/registro/', {
            'nombre_completo': 'Docente Nuevo', 'email': email,
            'password': 'Evidencia-CNA-2026!', 'password_confirm': 'Evidencia-CNA-2026!',
        }, REMOTE_ADDR=ip)

    def test_correo_vacio_o_invalido(self):
        for email in ('', 'no-es-correo'):
            with self.subTest(email=email):
                resp = self.registrar(email)
                self.assertContains(resp, 'Escribe un correo válido')
        self.assertFalse(Usuario.objects.exists())

    def test_limite_por_ip(self):
        for n in range(5):
            self.registrar(f'docente{n}@test.co')
        resp = self.registrar('otro@test.co')
        self.assertContains(resp, 'demasiados registros')
        self.assertEqual(Usuario.objects.count(), 5)


class RevisionConControlesTest(MediaTestCase):
    """M6: solo evidencias en revisión y nunca las propias."""

    @classmethod
    def setUpTestData(cls):
        cls.decana = crear_usuario('DECANA')
        cls.coord = crear_usuario('COORDINADOR')

    def test_no_se_aprueba_lo_propio(self):
        propio = crear_documento(self.coord, estado='PENDIENTE')
        with self.assertRaises(ReglaNegocioError):
            DocumentoService.aprobar_documento(propio.pk, self.coord)
        DocumentoService.aprobar_documento(propio.pk, self.decana)
        propio.refresh_from_db()
        self.assertEqual(propio.estado, 'APROBADO')

    def test_no_se_decide_sobre_lo_ya_decidido(self):
        rechazado = crear_documento(self.decana, estado='RECHAZADO')
        with self.assertRaises(ReglaNegocioError):
            DocumentoService.aprobar_documento(rechazado.pk, self.coord)
        aprobado = crear_documento(self.decana, estado='APROBADO')
        with self.assertRaises(ReglaNegocioError):
            DocumentoService.rechazar_documento(aprobado.pk, self.coord, 'motivo')

    def test_la_vista_muestra_el_motivo(self):
        propio = crear_documento(self.coord, estado='PENDIENTE')
        self.login(self.coord)
        resp = self.client.post(f'/documentos/{propio.pk}/aprobar/', follow=True)
        self.assertContains(resp, 'debe revisarla otra persona')


class EdicionYProgramaTest(MediaTestCase):
    """M7: la edición de un docente devuelve a revisión; el docente sube solo a su programa."""

    def setUp(self):
        super().setUp()
        self.prog = crear_programa()
        self.otro = crear_programa()
        self.docente = crear_usuario('DOCENTE_PLANTA', programa=self.prog)

    def test_editar_aprobada_vuelve_a_revision(self):
        doc = crear_documento(self.docente, estado='APROBADO')
        self.login(self.docente)
        self.client.post(f'/documentos/{doc.pk}/editar/', {
            'titulo': 'Título nuevo', 'descripcion': '', 'programa': self.prog.pk,
            'categoria': doc.categoria_id, 'visibilidad': 'PROGRAMA',
        })
        doc.refresh_from_db()
        self.assertEqual(doc.titulo, 'Título nuevo')
        self.assertEqual(doc.estado, 'PENDIENTE')

    def test_docente_no_elige_otro_programa(self):
        from apps.documentos.forms import DocumentoForm
        form = DocumentoForm(usuario=self.docente)
        self.assertEqual(list(form.fields['programa'].queryset), [self.prog])


class SensiblesDiscretosTest(MediaTestCase):
    """M5: sin acceso, un sensible no muestra autor ni aparece por descripción o autor."""

    def setUp(self):
        super().setUp()
        self.prog = crear_programa()
        self.autor = crear_usuario('DOCENTE_PLANTA', programa=self.prog, first_name='Zoraida')
        self.lector = crear_usuario('DOCENTE_PLANTA', programa=self.prog)
        self.doc = crear_documento(self.autor, es_sensible=True, estado='APROBADO',
                                   titulo='Acta reservada', descripcion='salarios confidenciales')

    def test_busquedas(self):
        self.login(self.lector)
        por_descripcion = self.client.get('/documentos/busqueda/?q=salarios').content.decode()
        self.assertNotIn('Acta reservada', por_descripcion)
        por_autor = self.client.get('/documentos/busqueda/?autor=Zoraida').content.decode()
        self.assertNotIn('Acta reservada', por_autor)
        por_titulo = self.client.get('/documentos/busqueda/?q=Acta').content.decode()
        self.assertIn('Acta reservada', por_titulo)
        self.assertNotIn('Zoraida', por_titulo)
        self.assertIn('Reservado', por_titulo)


class DefensaEnProfundidadTest(MediaTestCase):
    """Bajos: firma de archivos, CSP y redirección."""

    def test_firma_de_contenido(self):
        buenos = {'a.pdf': b'%PDF-1.7 x', 'a.docx': _ooxml('word/'),
                  'a.xlsx': _ooxml('xl/'), 'a.pptx': _ooxml('ppt/')}
        for nombre, contenido in buenos.items():
            with self.subTest(nombre=nombre):
                self.assertTrue(validar_archivo_subido(SimpleUploadedFile(nombre, contenido)))
        malos = {'a.pdf': b'MZ\x90\x00 ejecutable', 'a.docx': _ooxml('xl/'), 'b.xlsx': b'PK\x03\x04roto'}
        for nombre, contenido in malos.items():
            with self.subTest(nombre=nombre):
                with self.assertRaises(ValidationError):
                    validar_archivo_subido(SimpleUploadedFile(nombre, contenido))

    def test_csp_en_la_app_y_no_en_admin(self):
        resp = self.client.get('/login/')
        politica = resp.headers.get('Content-Security-Policy', '')
        self.assertIn("script-src 'self'", politica)
        self.assertNotIn('unsafe-inline', politica.split('script-src')[1].split(';')[0])
        self.assertNotIn('Content-Security-Policy', self.client.get('/admin/login/').headers)

    def test_sin_scripts_en_linea_en_plantillas_propias(self):
        from pathlib import Path
        base = Path(__file__).resolve().parent.parent
        for p in list(base.glob('apps/*/templates/**/*.html')) + list(base.glob('templates/**/*.html')):
            with self.subTest(plantilla=str(p)):
                self.assertNotRegex(p.read_text(encoding='utf-8'), r'<script(?![^>]*\bsrc=)[^>]*>')

    def test_redireccion_por_defecto_existe(self):
        from django.conf import settings
        from django.urls import reverse
        self.assertEqual(reverse(settings.LOGIN_REDIRECT_URL), '/documentos/dashboard/')
