"""Helpers compartidos por las pruebas de las correcciones de auditoría (spec 001)."""
import itertools
import shutil
import tempfile

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.documentos.models import Categoria, Documento
from apps.usuarios.models import ProgramaAcademico, Usuario

_seq = itertools.count(1)

PDF = b"%PDF-1.4 contenido de prueba"


def archivo(nombre="doc.pdf", contenido=PDF):
    tipo = "application/pdf" if nombre.endswith(".pdf") else "application/octet-stream"
    return SimpleUploadedFile(nombre, contenido, content_type=tipo)


def crear_programa(nombre=None):
    n = next(_seq)
    return ProgramaAcademico.objects.create(nombre=nombre or f"Programa {n}", codigo=f"P{n}")


def crear_categoria(nombre=None):
    return Categoria.objects.create(nombre=nombre or f"Categoria {next(_seq)}")


def crear_usuario(rol="DOCENTE_PLANTA", programa=None, habilitado=True, password="Clave-Segura-123!", **extra):
    n = next(_seq)
    es_decana = rol == "DECANA"
    return Usuario.objects.create_user(
        username=f"u{n}", email=extra.pop("email", f"usuario{n}@test.co"), password=password,
        rol=rol, programa_academico=programa, esta_habilitado=habilitado,
        is_staff=es_decana, is_superuser=es_decana,
        first_name=extra.pop("first_name", f"Nombre{n}"), last_name=extra.pop("last_name", "Prueba"),
        **extra,
    )


def crear_documento(autor, programa=None, categoria=None, estado="PENDIENTE",
                    es_sensible=False, nombre="doc.pdf", contenido=PDF, **extra):
    return Documento.objects.create(
        titulo=extra.pop("titulo", f"Documento {next(_seq)}"),
        archivo=archivo(nombre, contenido),
        programa=programa or autor.programa_academico or crear_programa(),
        categoria=categoria or crear_categoria(),
        autor=autor, estado=estado, es_sensible=es_sensible,
        visibilidad=extra.pop("visibilidad", "PROGRAMA"),
        **extra,
    )


def cerrar_archivo(resp):
    """Consume y cierra el archivo de un FileResponse.

    No se usa resp.close(): dispara request_finished, que cierra la conexión a la
    BD en mitad del TestCase.
    """
    if not getattr(resp, 'streaming', False):
        return resp.content
    contenido = b''.join(resp.streaming_content)
    for cerrar in list(getattr(resp, '_resource_closers', [])):
        cerrar()
    return contenido


class MediaTestCase(TestCase):
    """TestCase con MEDIA_ROOT temporal y caché limpia en cada prueba."""

    @classmethod
    def setUpClass(cls):
        cls._media = tempfile.mkdtemp(prefix="sigea-test-media-")
        cls._media_override = override_settings(MEDIA_ROOT=cls._media)
        cls._media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._media_override.disable()
        shutil.rmtree(cls._media, ignore_errors=True)

    def setUp(self):
        cache.clear()

    def login(self, usuario):
        self.client.force_login(usuario)
        return self.client
