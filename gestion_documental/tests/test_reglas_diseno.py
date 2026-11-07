"""Spec 002 (research R11): vigilancia del sistema de diseño.

Falla si una plantilla migrada usa estilos en línea que no sean variables de datos,
colores hex, emojis o iconos del CDN; o si el CSS del sistema usa colores fuera de
tokens, tamaños por debajo de 12 px o !important fuera de los casos permitidos.
"""
import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

BASE = Path(settings.BASE_DIR)
CSS_SISTEMA = BASE / 'static' / 'css' / 'sigea'

PLANTILLAS_MIGRADAS = [
    'templates/base.html',
    'templates/403.html',
    'templates/404.html',
    'templates/500.html',
    'templates/errores/base_error.html',
    'templates/componentes/banner_huella.html',
    'templates/componentes/matriz.html',
    'templates/componentes/cola_revision.html',
    'templates/componentes/pulso.html',
    'templates/componentes/tiempos.html',
    'templates/componentes/estado_vacio.html',
    'templates/componentes/chip_factor.html',
    'templates/componentes/estado_documento.html',
    'apps/documentos/templates/documentos/dashboard.html',
    'templates/partials/paginacion.html',
    'apps/documentos/templates/documentos/busqueda_avanzada.html',
    'apps/documentos/templates/documentos/mis_documentos.html',
    'apps/documentos/templates/documentos/detalle.html',
    'apps/documentos/templates/documentos/_campos_documento.html',
    'apps/documentos/templates/documentos/subir.html',
    'apps/documentos/templates/documentos/editar.html',
    'apps/documentos/templates/documentos/papelera.html',
    'apps/documentos/templates/documentos/aprobar_documentos.html',
    'apps/documentos/templates/documentos/factores_cna.html',
    'apps/versiones/templates/versiones/lista.html',
    'apps/versiones/templates/versiones/crear.html',
    'apps/permisos/templates/permisos/gestionar_accesos.html',
    'apps/permisos/templates/permisos/solicitudes.html',
    'apps/auditoria/templates/auditoria/lista.html',
    'apps/usuarios/templates/usuarios/gestion.html',
    'apps/usuarios/templates/usuarios/perfil.html',
    'apps/notificaciones/templates/notificaciones/lista.html',
    'apps/usuarios/templates/usuarios/_acceso.html',
    'apps/usuarios/templates/usuarios/login.html',
    'apps/usuarios/templates/usuarios/registro.html',
    'apps/usuarios/templates/usuarios/recuperar_contrasena.html',
    'apps/usuarios/templates/usuarios/confirmar_email.html',
    'apps/usuarios/templates/usuarios/validar_token.html',
    'apps/usuarios/templates/usuarios/cambiar_contrasena.html',
    'templates/componentes/tipo_archivo.html',
    'apps/usuarios/templates/usuarios/invitacion.html',
]


class TodasLasPlantillasTest(SimpleTestCase):
    def test_no_quedan_plantillas_sin_migrar(self):
        todas = {p.relative_to(BASE).as_posix() for p in BASE.glob('apps/*/templates/**/*.html')}
        todas |= {p.relative_to(BASE).as_posix() for p in BASE.glob('templates/**/*.html')}
        self.assertEqual(sorted(todas - set(PLANTILLAS_MIGRADAS)), [])


ESTILO_DE_DATOS = re.compile(r'^\s*(--[a-z-]+\s*:\s*[^;]+;?\s*)+$')
EMOJI = re.compile('[\U0001F300-\U0001FAFF☀-➿⭐✅]')
HEX = re.compile(r'#[0-9a-fA-F]{3,8}\b')


class PlantillasMigradasTest(SimpleTestCase):
    def test_reglas_de_plantilla(self):
        for ruta in PLANTILLAS_MIGRADAS:
            texto = (BASE / ruta).read_text(encoding='utf-8')
            with self.subTest(plantilla=ruta):
                for estilo in re.findall(r'style="([^"]*)"', texto):
                    self.assertRegex(estilo, ESTILO_DE_DATOS, f'estilo en línea no permitido: {estilo}')
                sin_meta = re.sub(r'<meta name="theme-color"[^>]*>', '', texto)
                self.assertFalse(HEX.search(sin_meta), 'color hex en plantilla')
                self.assertFalse(EMOJI.search(texto), 'emoji en plantilla')
                if 'base.html' not in ruta:
                    self.assertNotIn('data-lucide', texto)


class CssSistemaTest(SimpleTestCase):
    def leer(self):
        return {p.name: p.read_text(encoding='utf-8') for p in CSS_SISTEMA.glob('*.css')}

    def test_hex_solo_en_tokens(self):
        for nombre, texto in self.leer().items():
            if nombre == 'tokens.css':
                continue
            with self.subTest(css=nombre):
                self.assertFalse(HEX.search(texto), f'color hex fuera de tokens en {nombre}')

    def test_sin_tamanos_menores_de_12px(self):
        for nombre, texto in self.leer().items():
            for valor in re.findall(r'font-size:\s*([0-9.]+)(px|rem)', texto):
                px = float(valor[0]) * (16 if valor[1] == 'rem' else 1)
                with self.subTest(css=nombre, valor=valor):
                    self.assertGreaterEqual(px, 12)

    def test_important_solo_en_base(self):
        for nombre, texto in self.leer().items():
            if nombre == 'base.css':
                continue
            with self.subTest(css=nombre):
                self.assertNotIn('!important', texto)
