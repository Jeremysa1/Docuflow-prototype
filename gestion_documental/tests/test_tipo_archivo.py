"""Spec 003: icono de tipo de archivo (PDF, Word, Excel, PowerPoint) y opciones vacías en español."""
from django.template import Context, Template
from django.test import SimpleTestCase, TestCase

from apps.documentos.forms import DocumentoForm
from core.templatetags.sigea import datos_tipo_archivo


class TipoArchivoTest(SimpleTestCase):
    def test_extensiones_conocidas(self):
        casos = {
            'docs/informe.PDF': ('pdf', 'PDF'),
            'docs/acta.docx': ('word', 'DOC'),
            'docs/datos.xlsx': ('excel', 'XLS'),
            'docs/charla.pptx': ('ppt', 'PPT'),
        }
        for nombre, (clase, sigla) in casos.items():
            with self.subTest(nombre=nombre):
                self.assertEqual(datos_tipo_archivo(nombre)[:2], (clase, sigla))

    def test_extension_desconocida_y_vacia(self):
        self.assertEqual(datos_tipo_archivo('docs/foto.png')[:2], ('otro', 'PNG'))
        self.assertEqual(datos_tipo_archivo('')[:2], ('otro', 'ARC'))

    def test_render_accesible(self):
        html = Template('{% load sigea %}{% tipo_archivo nombre %}').render(Context({'nombre': 'a.pdf'}))
        self.assertIn('sg-tipo--pdf', html)
        self.assertIn('aria-label="Documento PDF"', html)
        self.assertIn('>PDF<', html)


class OpcionesVaciasTest(TestCase):
    def test_selects_en_espanol(self):
        form = DocumentoForm()
        html = str(form['factor_cna']) + str(form['categoria']) + str(form['programa'])
        self.assertNotIn('Select an option', html)
        self.assertNotIn('---------', html)
        self.assertIn('Elige el factor CNA', html)
