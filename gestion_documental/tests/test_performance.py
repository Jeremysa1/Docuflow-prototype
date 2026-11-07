"""Guards de regresión: performance (N+1) y UX simplificada del admin.

Se ejecutan con: ./venv/Scripts/python.exe manage.py test tests.test_performance
Usan BD de prueba aislada (no tocan datos reales).
"""
import shutil
import tempfile

from django.core.cache import cache
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.test import override_settings
from django.urls import reverse

from apps.documentos.models import Categoria, Documento
from apps.documentos.services import DocumentoService
from apps.notificaciones.services import NotificacionService
from apps.permisos.models import PermisoDocumento
from apps.permisos.services import PermisoService
from apps.usuarios.models import ProgramaAcademico, Usuario
from core.cache_stats import bump_stats, version_stats


def _archivo(nombre="doc.pdf"):
    return SimpleUploadedFile(nombre, b"%PDF-1.4 fake", content_type="application/pdf")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="sigea-test-media-"))
class PerformanceGuardsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.programa = ProgramaAcademico.objects.create(nombre="Prog Test", codigo="PT1")
        cls.programa2 = ProgramaAcademico.objects.create(nombre="Prog Otro", codigo="PT2")
        cls.categoria = Categoria.objects.create(nombre="Cat Test")
        cls.docente = Usuario.objects.create_user(
            username="docente", email="d@t.co", password="x",
            rol="DOCENTE_PLANTA", programa_academico=cls.programa, esta_habilitado=True,
        )
        cls.visitante = Usuario.objects.create_user(
            username="visita", email="v@t.co", password="x",
            rol="DOCENTE_PLANTA", programa_academico=cls.programa2, esta_habilitado=True,
        )
        cls.decana = Usuario.objects.create_user(
            username="decana", email="ad@t.co", password="x",
            rol="DECANA", is_staff=True, is_superuser=True, esta_habilitado=True,
        )
        for i in range(6):
            Documento.objects.create(
                titulo=f"Doc {i}", archivo=_archivo(f"d{i}.pdf"),
                programa=cls.programa, categoria=cls.categoria,
                autor=cls.docente, estado="APROBADO", visibilidad="PROGRAMA",
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Aislamiento total: LocMem sobrevive entre tests del mismo proceso.
        cache.clear()

    def test_stats_docente_un_solo_agregado(self):
        """4 counts -> 1 aggregate (+2 slices): techo exacto de 3 queries."""
        with self.assertNumQueries(3):
            c = DocumentoService.stats_docente(self.docente)
            _ = (c["mis_docs_count"], c["pendientes_count"],
                 c["aprobados_count"], c["rechazados_count"])
            list(c["actividad_reciente"])
            list(c["notificaciones"])

    def test_mis_documentos_sin_n_mas_1(self):
        """Página de 6 docs con FKs: 2 queries fijas (count + select con joins)."""
        from django.core.paginator import Paginator
        qs = Documento.objects.filter(autor=self.docente).select_related(
            "programa", "categoria", "autor").order_by("-fecha_creacion")
        with self.assertNumQueries(2):
            for d in Paginator(qs, 15).get_page(1):
                _ = (d.programa.nombre, d.categoria.nombre, d.autor.username)

    def test_busqueda_precarga_fija_y_correcta(self):
        """precargar = 2 queries; el loop posterior = 0; valores correctos."""
        # Igual que la vista real: select_related para programa/categoria/autor.
        docs = list(Documento.objects.select_related(
            "programa", "categoria", "autor")[:3])
        for d in docs:
            PermisoDocumento.objects.create(
                usuario=self.visitante, documento=d, puede_ver=True)
        with self.assertNumQueries(2):
            permisos, solicitudes = PermisoService.precargar_accesos(
                self.visitante, [d.id for d in docs])
        self.assertEqual(permisos, {d.id for d in docs})
        self.assertEqual(solicitudes, set())
        with self.assertNumQueries(0):
            for d in docs:
                self.assertTrue(PermisoService.usuario_tiene_acceso(
                    self.visitante, d, _permisos_ids=permisos))

    def test_admin_sin_continuar_ni_orden(self):
        """El change form no ofrece 'continuar editando' ni ordenación."""
        doc = Documento.objects.first()
        from django.contrib import admin as djadmin
        model_admin = djadmin.site._registry[Documento]
        self.assertEqual(tuple(model_admin.get_sortable_by(None)), ())
        self.client.force_login(self.decana)
        url = reverse("admin:documentos_documento_change", args=[doc.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'name="_continue"')

    def test_cache_notif_se_invalida(self):
        """contar usa caché; crear notif la invalida con valor fresco."""
        n0 = NotificacionService.contar_no_leidas(self.docente)
        with CaptureQueriesContext(connection) as ctx:
            self.assertEqual(NotificacionService.contar_no_leidas(self.docente), n0)
        self.assertEqual(len(ctx), 0)
        NotificacionService.crear_notificacion(
            usuario=self.docente, mensaje="hola", tipo="INFO")
        self.assertEqual(NotificacionService.contar_no_leidas(self.docente), n0 + 1)

    def test_bump_invalida_dashboard(self):
        """Crear documento sube la versión y el dashboard recomputa."""
        v0 = version_stats()
        DocumentoService.crear_documento(
            titulo="Nuevo", descripcion="d", archivo=_archivo("n.pdf"),
            programa=self.programa, categoria=self.categoria, autor=self.docente,
        )
        self.assertEqual(version_stats(), v0 + 1)
        c = DocumentoService.stats_docente(self.docente)
        self.assertEqual(c["mis_docs_count"], 7)

    def test_throttle_buscador(self):
        """60 búsquedas/min OK; la 61 recibe 429."""
        self.client.force_login(self.visitante)
        url = reverse("documentos:buscar_ajax")
        for _ in range(60):
            r = self.client.get(url, {"q": "Doc"})
            self.assertEqual(r.status_code, 200)
        r = self.client.get(url, {"q": "Doc"})
        self.assertEqual(r.status_code, 429)

    def test_sesion_cached_db_configurada(self):
        """La sesión lee de caché (H-07): verifica el backend configurado."""
        from django.conf import settings
        self.assertEqual(
            settings.SESSION_ENGINE,
            "django.contrib.sessions.backends.cached_db",
        )
        self.assertIn("whitenoise.middleware.WhiteNoiseMiddleware", settings.MIDDLEWARE)
        cache.set("sigea:ping", 1, 10)
        self.assertEqual(cache.get("sigea:ping"), 1)
