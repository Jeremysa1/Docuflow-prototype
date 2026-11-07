"""Spec 002: métricas de los paneles (gradación, huellas, matriz, cola, tiempos, pulso)."""
from datetime import timedelta

from django.utils import timezone

from apps.auditoria.models import RegistroAuditoria
from apps.documentos.metricas import METAS_POR_FACTOR, MetricasService
from apps.documentos.models import Documento
from apps.permisos.models import SolicitudAcceso
from tests.factories import MediaTestCase, crear_documento, crear_programa, crear_usuario


class GradacionTest(MediaTestCase):
    def test_umbrales_escala_cna(self):
        casos = [
            (0, 20, 0), (1, 100, 1), (59, 100, 1), (60, 100, 2), (69, 100, 2),
            (70, 100, 3), (79, 100, 3), (80, 100, 4), (89, 100, 4), (90, 100, 5), (120, 100, 5),
        ]
        for aprobados, meta, nivel in casos:
            with self.subTest(aprobados=aprobados, meta=meta):
                self.assertEqual(MetricasService.gradacion(aprobados, meta).nivel, nivel)

    def test_meta_cero_es_sin_evidencia(self):
        self.assertEqual(MetricasService.gradacion(5, 0).nivel, 0)

    def test_porcentaje_sin_tope(self):
        self.assertEqual(MetricasService.gradacion(23, 20).porcentaje, 115)


class HuellaMatrizTest(MediaTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.prog_a = crear_programa('A')
        cls.prog_b = crear_programa('B')
        cls.docente = crear_usuario('DOCENTE_PLANTA', programa=cls.prog_a)

    def setUp(self):
        super().setUp()
        for _ in range(4):
            crear_documento(self.docente, programa=self.prog_a, estado='APROBADO', factor_cna='F3')
        crear_documento(self.docente, programa=self.prog_b, estado='APROBADO', factor_cna='F3')
        viejo = crear_documento(self.docente, estado='PENDIENTE', factor_cna='F7')
        Documento.objects.filter(pk=viejo.pk).update(fecha_modificacion=timezone.now() - timedelta(days=5))
        crear_documento(self.docente, estado='PENDIENTE', factor_cna='F7')

    def test_huella_facultad(self):
        h = MetricasService.huella_facultad()
        self.assertEqual(len(h['celdas']), 12)
        f3 = next(c for c in h['celdas'] if c.codigo == 'F3')
        self.assertEqual((f3.aprobados, f3.meta), (5, METAS_POR_FACTOR['F3']))
        self.assertEqual(h['total_aprobados'], 5)
        self.assertEqual(h['total_meta'], sum(METAS_POR_FACTOR.values()))
        self.assertEqual(h['pendientes'], 2)
        self.assertEqual(h['pendientes_envejecidos'], 1)

    def test_factor_que_supera_la_meta(self):
        for _ in range(23):
            crear_documento(self.docente, estado='APROBADO', factor_cna='F4')
        f4 = next(c for c in MetricasService.huella_facultad()['celdas'] if c.codigo == 'F4')
        self.assertEqual(f4.gradacion.nivel, 5)
        self.assertEqual(f4.aprobados, 23)
        self.assertEqual(f4.altura, 100)

    def test_matriz_por_programa_con_consultas_fijas(self):
        with self.assertNumQueries(2):
            m = MetricasService.matriz_factor_programa()
        fila = next(f for f in m['filas'] if f['codigo'] == 'F3')
        por_programa = {p['nombre']: c.aprobados for p, c in fila['celdas']}
        self.assertEqual(por_programa, {'A': 4, 'B': 1})
        self.assertEqual(fila['facultad'].aprobados, 5)


class ColaTiemposTest(MediaTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.docente = crear_usuario('DOCENTE_PLANTA', programa=crear_programa())
        cls.coord = crear_usuario('COORDINADOR')

    def test_cola_ordenada_por_antiguedad(self):
        ahora = timezone.now()
        docs = []
        for dias in (1, 7, 4):
            d = crear_documento(self.docente, estado='PENDIENTE')
            Documento.objects.filter(pk=d.pk).update(fecha_modificacion=ahora - timedelta(days=dias))
            docs.append(d)
        cola = MetricasService.cola_revision()
        self.assertEqual([d.dias_esperando for d in cola], [7, 4, 1])
        self.assertEqual([d.envejecido for d in cola], [True, True, False])

    def test_tiempos_desde_la_auditoria(self):
        doc = crear_documento(self.docente, estado='APROBADO')
        Documento.objects.filter(pk=doc.pk).update(fecha_creacion=timezone.now() - timedelta(hours=10))
        RegistroAuditoria.objects.create(usuario=self.coord, accion='APROBO', documento=doc)
        t = MetricasService.tiempos_revision()
        self.assertEqual(len(t['puntos']), 4)
        self.assertEqual(t['revisados'], 1)
        self.assertAlmostEqual(t['puntos'][-1]['media_horas'], 10, delta=0.2)


class PulsoTest(MediaTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.docente = crear_usuario('DOCENTE_PLANTA', programa=crear_programa())
        cls.otro = crear_usuario('DOCENTE_PLANTA', programa=cls.docente.programa_academico)

    def test_series_y_solicitudes_historicas(self):
        doc = crear_documento(self.docente, estado='APROBADO')
        for _ in range(3):
            RegistroAuditoria.objects.create(usuario=self.otro, accion='ACCESO_DENEGADO', documento=doc)
        RegistroAuditoria.objects.create(usuario=self.otro, accion='DESCARGO', documento=doc)
        SolicitudAcceso.objects.create(solicitante=self.otro, documento=doc, motivo='m', estado='PENDIENTE')
        p = MetricasService.pulso_30_dias()
        totales = {s['clave']: s['total'] for s in p['series']}
        self.assertEqual(totales, {'DESCARGO': 1, 'ACCESO_DENEGADO': 3, 'SOLICITUDES': 1})
        denegados = next(s for s in p['series'] if s['clave'] == 'ACCESO_DENEGADO')
        self.assertEqual(len(denegados['valores']), 30)
        self.assertEqual(denegados['ultimo'], 3)


class HuellaPersonalTest(MediaTestCase):
    @classmethod
    def setUpTestData(cls):
        prog = crear_programa()
        cls.docente = crear_usuario('DOCENTE_PLANTA', programa=prog)
        cls.otro = crear_usuario('DOCENTE_PLANTA', programa=prog)

    def test_solo_documentos_propios_por_estado(self):
        crear_documento(self.docente, estado='APROBADO')
        crear_documento(self.docente, estado='APROBADO')
        crear_documento(self.docente, estado='PENDIENTE')
        crear_documento(self.otro, estado='APROBADO')
        h = MetricasService.huella_personal(self.docente)
        self.assertEqual(len(h['columnas']), 12)
        self.assertEqual(h['totales']['total'], 3)
        actual = h['columnas'][-1]
        self.assertEqual((actual['aprobadas'], actual['pendientes'], actual['rechazadas']), (2, 1, 0))
