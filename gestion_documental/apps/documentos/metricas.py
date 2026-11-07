"""
Métricas de acreditación para los paneles (spec 002).

Todas las cifras son "cantidad frente a meta" y se clasifican con la gradación CNA
(research R3). Los resultados se cachean con `conteo_cacheado` y se invalidan con
`bump_stats()`, que ya llaman todas las escrituras de documentos.

Visibilidad (data-model): la huella de facultad, la matriz, la cola y el pulso son
solo para DECANA y COORDINADORA; el docente recibe únicamente su huella personal.
"""
from dataclasses import dataclass
from datetime import timedelta
from statistics import median
from zoneinfo import ZoneInfo

from django.db.models import Count, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone

from core.cache_stats import conteo_cacheado

from .models import Documento

ZONA = ZoneInfo('America/Bogota')

METAS_POR_FACTOR = {
    'F1': 15, 'F2': 25, 'F3': 20, 'F4': 10, 'F5': 30, 'F6': 15,
    'F7': 10, 'F8': 20, 'F9': 15, 'F10': 15, 'F11': 20, 'F12': 10,
}

NIVELES = [
    (0, 'Sin evidencia'),
    (1, 'No se cumple'),
    (2, 'Insatisfactorio'),
    (3, 'Aceptable'),
    (4, 'Alto grado'),
    (5, 'Pleno'),
]

DIAS_ENVEJECIDO = 3


def nombre_corto(nombre):
    """'Factor 3: Profesores.' -> 'Profesores'."""
    texto = nombre.split(':', 1)[-1].strip()
    return texto[:-1] if texto.endswith('.') else texto


NOMBRES_FACTOR = {codigo: nombre_corto(nombre) for codigo, nombre in Documento.FACTORES_CNA}


@dataclass(frozen=True)
class Gradacion:
    nivel: int
    etiqueta: str
    porcentaje: int


@dataclass(frozen=True)
class CeldaFactor:
    codigo: str
    nombre: str
    aprobados: int
    pendientes: int
    meta: int
    gradacion: Gradacion

    @property
    def altura(self):
        """Altura de la columna de la huella: avance con tope en 100 %."""
        return min(self.gradacion.porcentaje, 100)


class MetricasService:
    """Métricas derivadas para los paneles por rol."""

    # ─── Gradación ───────────────────────────────────────────────

    @staticmethod
    def gradacion(aprobados, meta):
        """Nivel CNA según % de aprobadas frente a la meta (aclaración 2026-11-07)."""
        if not meta or meta <= 0 or aprobados <= 0:
            porcentaje = 0 if not meta or meta <= 0 else 0
            return Gradacion(0, NIVELES[0][1], porcentaje)
        porcentaje = round(aprobados * 100 / meta)
        if porcentaje >= 90:
            nivel = 5
        elif porcentaje >= 80:
            nivel = 4
        elif porcentaje >= 70:
            nivel = 3
        elif porcentaje >= 60:
            nivel = 2
        else:
            nivel = 1
        return Gradacion(nivel, NIVELES[nivel][1], porcentaje)

    @staticmethod
    def _celda(codigo, aprobados, pendientes):
        meta = METAS_POR_FACTOR.get(codigo, 10)
        return CeldaFactor(
            codigo=codigo, nombre=NOMBRES_FACTOR.get(codigo, codigo),
            aprobados=aprobados, pendientes=pendientes, meta=meta,
            gradacion=MetricasService.gradacion(aprobados, meta),
        )

    # ─── Huella de facultad (Decana y Coordinadora) ──────────────

    @staticmethod
    def huella_facultad():
        def consulta():
            filas = {
                f['factor_cna']: f
                for f in Documento.objects.exclude(factor_cna__isnull=True).exclude(factor_cna='')
                .values('factor_cna').annotate(
                    aprobados=Count('id', filter=Q(estado='APROBADO')),
                    pendientes=Count('id', filter=Q(estado='PENDIENTE')),
                )
            }
            limite = timezone.now() - timedelta(days=DIAS_ENVEJECIDO)
            envejecidos = Documento.objects.filter(estado='PENDIENTE', fecha_modificacion__lt=limite).count()
            pendientes_total = Documento.objects.filter(estado='PENDIENTE').count()
            celdas = [
                MetricasService._celda(codigo, filas.get(codigo, {}).get('aprobados', 0),
                                       filas.get(codigo, {}).get('pendientes', 0))
                for codigo, _ in Documento.FACTORES_CNA
            ]
            return {
                'celdas': celdas,
                'total_aprobados': sum(c.aprobados for c in celdas),
                'total_meta': sum(c.meta for c in celdas),
                'pendientes': pendientes_total,
                'pendientes_envejecidos': envejecidos,
            }
        datos = conteo_cacheado('metricas:huella', consulta)
        datos = dict(datos)
        datos['gradacion'] = MetricasService.gradacion(datos['total_aprobados'], datos['total_meta'])
        datos['mas_lejano'] = min(datos['celdas'], key=lambda c: (c.gradacion.porcentaje, -c.meta))
        return datos

    # ─── Matriz factor × programa ────────────────────────────────

    @staticmethod
    def matriz_factor_programa():
        from apps.usuarios.models import ProgramaAcademico

        def consulta():
            conteos = {}
            for f in (Documento.objects.exclude(factor_cna__isnull=True).exclude(factor_cna='')
                      .values('factor_cna', 'programa_id').annotate(
                          aprobados=Count('id', filter=Q(estado='APROBADO')),
                          pendientes=Count('id', filter=Q(estado='PENDIENTE')),
                      )):
                conteos[(f['factor_cna'], f['programa_id'])] = (f['aprobados'], f['pendientes'])
            programas = list(ProgramaAcademico.objects.order_by('nombre').values('id', 'nombre'))
            filas = []
            for codigo, _ in Documento.FACTORES_CNA:
                celdas = [
                    MetricasService._celda(codigo, *conteos.get((codigo, p['id']), (0, 0)))
                    for p in programas
                ]
                total = MetricasService._celda(
                    codigo,
                    sum(c.aprobados for c in celdas),
                    sum(c.pendientes for c in celdas),
                )
                filas.append({'codigo': codigo, 'nombre': NOMBRES_FACTOR[codigo],
                              'celdas': list(zip(programas, celdas)), 'facultad': total})
            # Fila de totales: suma por programa y de la facultad (todas las metas).
            meta_total = sum(METAS_POR_FACTOR.values())
            totales = []
            for i, p in enumerate(programas):
                aprobados = sum(f['celdas'][i][1].aprobados for f in filas)
                totales.append((p, CeldaFactor('Total', 'Total', aprobados, 0, meta_total,
                                               MetricasService.gradacion(aprobados, meta_total))))
            aprobados_fac = sum(f['facultad'].aprobados for f in filas)
            total_facultad = CeldaFactor('Total', 'Total', aprobados_fac, 0, meta_total,
                                         MetricasService.gradacion(aprobados_fac, meta_total))
            return {'programas': programas, 'filas': filas,
                    'totales': totales, 'total_facultad': total_facultad}
        return conteo_cacheado('metricas:matriz', consulta)

    # ─── Cola y tiempos de revisión ──────────────────────────────

    @staticmethod
    def cola_revision(limite=None):
        ahora = timezone.now()
        qs = (Documento.objects.filter(estado='PENDIENTE')
              .select_related('autor', 'programa', 'categoria')
              .order_by('fecha_modificacion'))
        if limite:
            qs = qs[:limite]
        cola = []
        for doc in qs:
            dias = (ahora - doc.fecha_modificacion).days
            doc.dias_esperando = dias
            doc.envejecido = dias > DIAS_ENVEJECIDO
            doc.celda = MetricasService._celda(doc.factor_cna, 0, 0) if doc.factor_cna else None
            cola.append(doc)
        return cola

    @staticmethod
    def tiempos_revision(semanas=4):
        """Horas desde la subida (o la última versión) hasta la aprobación o el rechazo."""
        from apps.auditoria.models import RegistroAuditoria

        def consulta():
            ahora = timezone.now()
            desde = ahora - timedelta(weeks=semanas)
            decisiones = list(
                RegistroAuditoria.objects.filter(accion__in=('APROBO', 'RECHAZO'), fecha_hora__gte=desde,
                                                 documento__isnull=False)
                .order_by('fecha_hora').values('documento_id', 'fecha_hora')
            )
            ids = {d['documento_id'] for d in decisiones}
            creacion = dict(Documento.all_objects.filter(id__in=ids).values_list('id', 'fecha_creacion'))
            versiones = {}
            for v in (RegistroAuditoria.objects.filter(accion='NUEVA_VERSION', documento_id__in=ids)
                      .order_by('fecha_hora').values('documento_id', 'fecha_hora')):
                versiones.setdefault(v['documento_id'], []).append(v['fecha_hora'])

            buckets = [[] for _ in range(semanas)]
            for d in decisiones:
                inicio = creacion.get(d['documento_id'])
                previas = [f for f in versiones.get(d['documento_id'], []) if f <= d['fecha_hora']]
                if previas:
                    inicio = previas[-1]
                if not inicio:
                    continue
                horas = max((d['fecha_hora'] - inicio).total_seconds() / 3600, 0)
                semana = min(int((ahora - d['fecha_hora']).days // 7), semanas - 1)
                buckets[semanas - 1 - semana].append(horas)

            puntos = []
            for i, valores in enumerate(buckets):
                puntos.append({
                    'etiqueta': 'Esta semana' if i == semanas - 1 else f'Hace {semanas - 1 - i} sem.',
                    'revisados': len(valores),
                    'media_horas': round(sum(valores) / len(valores), 1) if valores else None,
                    'mediana_horas': round(median(valores), 1) if valores else None,
                })
            todos = [h for b in buckets for h in b]
            return {
                'puntos': puntos,
                'revisados': len(todos),
                'media_horas': round(sum(todos) / len(todos), 1) if todos else None,
            }
        datos = dict(conteo_cacheado('metricas:tiempos', consulta, timeout=300))
        maximo = max([p['media_horas'] or 0 for p in datos['puntos']] + [1])
        datos['puntos'] = [dict(p, altura=round((p['media_horas'] or 0) * 100 / maximo)) for p in datos['puntos']]
        return datos

    # ─── Pulso de actividad y seguridad (30 días) ────────────────

    @staticmethod
    def pulso_30_dias(dias=30):
        from apps.auditoria.models import RegistroAuditoria
        from apps.permisos.models import SolicitudAcceso

        def consulta():
            hoy = timezone.localtime(timezone.now(), ZONA).date()
            inicio = hoy - timedelta(days=dias - 1)
            inicio_previo = inicio - timedelta(days=dias)
            desde = timezone.make_aware(
                timezone.datetime.combine(inicio_previo, timezone.datetime.min.time()), ZONA)

            serie = {'DESCARGO': {}, 'ACCESO_DENEGADO': {}, 'SOLICITUDES': {}}
            for fila in (RegistroAuditoria.objects.filter(accion__in=('DESCARGO', 'ACCESO_DENEGADO'),
                                                          fecha_hora__gte=desde)
                         .annotate(dia=TruncDate('fecha_hora', tzinfo=ZONA))
                         .values('accion', 'dia').annotate(n=Count('id'))):
                serie[fila['accion']][fila['dia']] = fila['n']
            for fila in (SolicitudAcceso.objects.filter(fecha_solicitud__gte=desde)
                         .annotate(dia=TruncDate('fecha_solicitud', tzinfo=ZONA))
                         .values('dia').annotate(n=Count('id'))):
                serie['SOLICITUDES'][fila['dia']] = fila['n']

            dias_lista = [inicio + timedelta(days=i) for i in range(dias)]
            resultado = []
            for clave, nombre, accion_filtro, alerta in (
                ('DESCARGO', 'Descargas', 'DESCARGO', False),
                ('ACCESO_DENEGADO', 'Accesos denegados', 'ACCESO_DENEGADO', True),
                ('SOLICITUDES', 'Solicitudes de acceso', 'SOLICITO_ACCESO', False),
            ):
                valores = [serie[clave].get(d, 0) for d in dias_lista]
                previo = sum(v for d, v in serie[clave].items() if inicio_previo <= d < inicio)
                resultado.append({
                    'clave': clave, 'nombre': nombre, 'accion': accion_filtro, 'alerta': alerta,
                    'valores': valores, 'total': sum(valores), 'previo': previo,
                    'variacion': sum(valores) - previo,
                    'ultimo': valores[-1],
                })
            return {'series': resultado, 'desde': inicio, 'hasta': hoy}
        datos = conteo_cacheado('metricas:pulso', consulta, timeout=300)
        series = []
        for s in datos['series']:
            maximo = max(s['valores'] + [1])
            barras = []
            for i, v in enumerate(s['valores']):
                alto = round(v * 36 / maximo) if v else 0
                barras.append({'x': i * 10, 'alto': max(alto, 1 if v else 0), 'y': 38 - max(alto, 1 if v else 0),
                               'valor': v, 'es_alto': v and v == maximo})
            series.append(dict(s, barras=barras))
        return dict(datos, series=series)

    # ─── Huella personal (docente) ───────────────────────────────

    @staticmethod
    def huella_personal(usuario, meses=12):
        """Últimos 12 meses de evidencias PROPIAS por estado. Nunca datos de la facultad."""
        def consulta():
            hoy = timezone.localtime(timezone.now(), ZONA).date().replace(day=1)
            lista_meses = []
            anio, mes = hoy.year, hoy.month
            for _ in range(meses):
                lista_meses.append((anio, mes))
                mes -= 1
                if mes == 0:
                    anio, mes = anio - 1, 12
            lista_meses.reverse()
            primero = timezone.make_aware(
                timezone.datetime(lista_meses[0][0], lista_meses[0][1], 1), ZONA)
            propios = Documento.objects.filter(autor=usuario)
            conteo = {}
            for fila in (propios.filter(fecha_creacion__gte=primero)
                         .annotate(m=TruncMonth('fecha_creacion', tzinfo=ZONA))
                         .values('m').annotate(
                             aprobadas=Count('id', filter=Q(estado='APROBADO')),
                             pendientes=Count('id', filter=Q(estado='PENDIENTE')),
                             rechazadas=Count('id', filter=Q(estado='RECHAZADO')))):
                m = fila['m']
                conteo[(m.year, m.month)] = fila
            totales = propios.aggregate(
                total=Count('id'),
                aprobadas=Count('id', filter=Q(estado='APROBADO')),
                pendientes=Count('id', filter=Q(estado='PENDIENTE')),
                rechazadas=Count('id', filter=Q(estado='RECHAZADO')),
            )
            return {'meses': lista_meses, 'conteo': conteo, 'totales': totales}
        datos = conteo_cacheado(f'metricas:personal:{usuario.pk}', consulta)
        nombres = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
        columnas = []
        maximo = max([sum((datos['conteo'].get(m) or {}).get(k, 0) for k in ('aprobadas', 'pendientes', 'rechazadas'))
                      for m in datos['meses']] + [1])
        for i, (anio, mes) in enumerate(datos['meses']):
            fila = datos['conteo'].get((anio, mes)) or {}
            aprobadas, pendientes, rechazadas = (fila.get('aprobadas', 0), fila.get('pendientes', 0),
                                                 fila.get('rechazadas', 0))
            total = aprobadas + pendientes + rechazadas
            columnas.append({
                'i': i, 'etiqueta': nombres[mes - 1], 'anio': anio, 'total': total,
                'aprobadas': aprobadas, 'pendientes': pendientes, 'rechazadas': rechazadas,
                'altura': round(total * 100 / maximo) if total else 0,
            })
        return {'columnas': columnas, 'totales': datos['totales']}
