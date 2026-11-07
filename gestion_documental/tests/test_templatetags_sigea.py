"""Spec 002: template tags del sistema de diseño."""
from types import SimpleNamespace

from django.template import Context, Template
from django.test import SimpleTestCase

from apps.documentos.metricas import MetricasService, CeldaFactor
from core.templatetags.sigea import iniciales, plural


class FiltrosTest(SimpleTestCase):
    def test_plural(self):
        self.assertEqual(plural(1, 'evidencia,evidencias'), '1 evidencia')
        self.assertEqual(plural(2, 'evidencia,evidencias'), '2 evidencias')
        self.assertEqual(plural(0, 'día,días'), '0 días')

    def test_iniciales_nunca_vacias(self):
        self.assertEqual(iniciales(SimpleNamespace(first_name='Andrea', last_name='Decana', email='')), 'AD')
        self.assertEqual(iniciales(SimpleNamespace(first_name='Test', last_name='', email='')), 'T')
        self.assertEqual(iniciales(SimpleNamespace(first_name='', last_name='', email='zoe@x.co')), 'Z')
        self.assertEqual(iniciales(SimpleNamespace(first_name='', last_name='', email='')), '?')
        self.assertEqual(iniciales(None), '?')


class EtiquetasTest(SimpleTestCase):
    def render(self, texto, **ctx):
        return Template('{% load sigea %}' + texto).render(Context(ctx))

    def test_icono_decorativo_y_con_etiqueta(self):
        self.assertIn('aria-hidden="true"', self.render('{% icono "search" %}'))
        html = self.render('{% icono "trash-2" etiqueta="Eliminar" %}')
        self.assertIn('aria-label="Eliminar"', html)
        self.assertIn('lucide.svg?v=2#trash-2', html)

    def test_chip_factor_usa_su_gradacion(self):
        celda = CeldaFactor('F3', 'Profesores', 4, 0, 20, MetricasService.gradacion(4, 20))
        html = self.render('{% chip_factor celda %}', celda=celda)
        self.assertIn('sg-grad-1', html)
        self.assertIn('4 / 20', html)
