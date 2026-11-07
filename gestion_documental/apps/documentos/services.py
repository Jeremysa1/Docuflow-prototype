"""
Servicios del módulo de documentos.

Contiene toda la lógica de negocio relacionada con la gestión de documentos.
"""
from datetime import timedelta

from core.utils.helpers import ReglaNegocioError

from django.db.models import Q, Count
from django.core.cache import cache
from django.utils import timezone

from core.cache_stats import bump_stats, conteo_cacheado

from .models import Documento, Categoria
from ..usuarios.models import ProgramaAcademico, Usuario
from ..notificaciones.services import NotificacionService
from core.services.storage_service import StorageService
from core.services.audit_service import AuditService


class DocumentoService:
    """Servicio para la gestión de documentos."""

    @staticmethod
    def crear_documento(titulo, descripcion, archivo, programa, categoria,
                        autor, requiere_aprobacion=True,
                        es_sensible=False,
                        factor_cna=None, fecha_vigencia=None, visibilidad='PROGRAMA'):
        """
        Crea un nuevo documento aplicando reglas de aprobación por rol.
        """
        # Regla de negocio por rol
        if autor.rol == 'DOCENTE_PLANTA':
            requiere_aprobacion = True  # Forzar siempre
            estado = 'PENDIENTE'
        elif requiere_aprobacion:
            estado = 'PENDIENTE'
        else:
            estado = 'APROBADO'  # Coordinador/Decana sin revisión

        # Guardar archivo mediante StorageService
        ruta = StorageService.save_document(archivo, programa, categoria)

        documento = Documento.objects.create(
            titulo=titulo,
            descripcion=descripcion,
            archivo=ruta,
            programa=programa,
            categoria=categoria,
            autor=autor,
            estado=estado,
            es_compartido=False,  # DEPRECADO — siempre False
            es_sensible=es_sensible,
            factor_cna=factor_cna,
            fecha_vigencia=fecha_vigencia,
            visibilidad=visibilidad,
        )

        # Registrar auditoría
        AuditService.log(usuario=autor, accion='SUBIO', documento=documento)

        # Notificaciones si va a revisión.
        # A3: la Coordinadora es única de facultad -> no se filtra por programa.
        if estado == 'PENDIENTE':
            mensaje = f"{autor.get_full_name()} subió '{titulo}' y requiere tu revisión."
            if autor.rol == 'DOCENTE_PLANTA':
                NotificacionService.notificar_revisores(documento, mensaje, actor=autor)
            elif autor.rol == 'COORDINADOR':
                # Lo que sube la Coordinadora lo revisa la Decana.
                NotificacionService.notificar_revisores(
                    documento, mensaje, actor=autor, incluir_decana=True
                )

        bump_stats()
        return documento

    @staticmethod
    def obtener_detalle_documento(documento_id, usuario):
        """Retorna documento con permisos y metadata extra."""
        from ..versiones.models import Version
        from ..auditoria.models import RegistroAuditoria
        from ..permisos.services import PermisoService
        from ..permisos.models import SolicitudAcceso

        try:
            doc = Documento.objects.select_related('programa', 'categoria', 'autor').get(pk=documento_id)
        except Documento.DoesNotExist:
            return None

        # Permisos usando nueva lógica
        tiene_acceso = PermisoService.usuario_tiene_acceso(usuario, doc)
        # M6: nadie revisa su propia evidencia
        puede_aprobar = usuario.rol in ('COORDINADOR', 'DECANA') and doc.estado == 'PENDIENTE' and doc.autor_id != usuario.id
        puede_descargar = tiene_acceso
        puede_ver = tiene_acceso
        
        if not puede_ver:
            raise PermissionError("No tienes permiso para ver este documento.")

        # Verificar si el usuario puede gestionar accesos
        # Regla facultad: autor, COORDINADOR (única de facultad) o DECANA.
        puede_gestionar_accesos = (
            usuario == doc.autor or
            usuario.rol == 'COORDINADOR' or
            usuario.rol == 'DECANA'
        )

        # Contar solicitudes pendientes
        solicitudes_pendientes_count = 0
        if puede_gestionar_accesos:
            solicitudes_pendientes_count = SolicitudAcceso.objects.filter(
                documento=doc, estado='PENDIENTE'
            ).count()

        versiones = Version.objects.filter(documento=doc).order_by('-numero_version')
        historial_auditoria = RegistroAuditoria.objects.filter(documento=doc).order_by('-fecha_hora')[:10]
        total_descargas = RegistroAuditoria.objects.filter(documento=doc, accion='DESCARGO').count()

        return {
            'documento': doc,
            'versiones': versiones,
            'historial_auditoria': historial_auditoria,
            'puede_aprobar': puede_aprobar,
            'puede_descargar': puede_descargar,
            'total_descargas': total_descargas,
            'puede_gestionar_accesos': puede_gestionar_accesos,
            'solicitudes_pendientes_count': solicitudes_pendientes_count,
        }


    @staticmethod
    def busqueda_avanzada(usuario, query=None, categoria_id=None,
                          factor_cna=None, estado=None,
                          fecha_desde=None, fecha_hasta=None,
                          autor_query=None, vigente=None,
                          visibilidad_filter=None, orden=None, programa_id=None):
        """Búsqueda avanzada con todos los filtros y ordenamiento dinámico."""
        queryset = Documento.objects.select_related('programa', 'categoria', 'autor')

        # Rol filtrado base con lógica de visibilidad
        if usuario.rol in ('COORDINADOR', 'DECANA'):
            pass  # Ven todo el sistema
        else:
            es_autor = Q(autor=usuario)
            tiene_permiso = Q(permisos__usuario=usuario, permisos__puede_ver=True)
            es_institucional = Q(visibilidad='INSTITUCIONAL')
            es_mismo_programa = Q(
                visibilidad='PROGRAMA',
                programa=usuario.programa_academico
            )
            queryset = queryset.filter(
                es_autor | tiene_permiso | es_institucional | es_mismo_programa
            ).distinct()

        # Filtros
        from core.utils.helpers import parse_fecha_segura, inicio_dia
        if visibilidad_filter and usuario.rol in ('COORDINADOR', 'DECANA'):
            queryset = queryset.filter(visibilidad=visibilidad_filter)
        # M5: un sensible sin acceso no se encuentra por descripción ni por autor
        if usuario.rol in ('COORDINADOR', 'DECANA') or usuario.is_superuser:
            detalle_visible = Q()
        else:
            detalle_visible = Q(es_sensible=False) | Q(autor=usuario) | Q(
                permisos__usuario=usuario, permisos__puede_ver=True)
        if query:
            queryset = queryset.filter(
                Q(titulo__icontains=query) | (Q(descripcion__icontains=query) & detalle_visible)
            ).distinct()
        if programa_id and str(programa_id).isdigit():
            queryset = queryset.filter(programa_id=programa_id)
        if categoria_id and str(categoria_id).isdigit():
            queryset = queryset.filter(categoria_id=categoria_id)
        if factor_cna:
            queryset = queryset.filter(factor_cna=factor_cna)
        if estado:
            queryset = queryset.filter(estado=estado)
        fecha_desde = parse_fecha_segura(fecha_desde)
        fecha_hasta = parse_fecha_segura(fecha_hasta)
        if fecha_desde:
            # H-13: rangos index-friendly en vez de __date.
            queryset = queryset.filter(fecha_creacion__gte=inicio_dia(fecha_desde))
        if fecha_hasta:
            queryset = queryset.filter(
                fecha_creacion__lt=inicio_dia(fecha_hasta) + timedelta(days=1)
            )
        if autor_query:
            queryset = queryset.filter(
                (Q(autor__first_name__icontains=autor_query) |
                 Q(autor__last_name__icontains=autor_query) |
                 Q(autor__email__icontains=autor_query)) & detalle_visible
            ).distinct()
        if vigente == '1':
            queryset = queryset.filter(
                Q(fecha_vigencia__gte=timezone.now().date()) | Q(fecha_vigencia__isnull=True)
            )

        # Ordenamiento dinámico
        ORDENES_VALIDOS = {
            'recientes': '-fecha_creacion',
            'antiguos': 'fecha_creacion',
            'az': 'titulo',
            'za': '-titulo',
        }
        orden_campo = ORDENES_VALIDOS.get(orden, '-fecha_creacion')
        return queryset.order_by(orden_campo)

    @staticmethod
    def _validar_revision(documento, usuario):
        """M6: solo se decide sobre evidencias en revisión y nunca sobre las propias."""
        if documento.estado != Documento.Estado.PENDIENTE:
            raise ReglaNegocioError(f'«{documento.titulo}» ya no está en revisión.')
        if documento.autor_id == usuario.id:
            raise ReglaNegocioError(f'«{documento.titulo}» es tuya: debe revisarla otra persona.')

    @staticmethod
    def aprobar_documento(documento_id, usuario, request=None):
        """Aprueba un documento y notifica al autor."""
        documento = Documento.objects.get(pk=documento_id)
        DocumentoService._validar_revision(documento, usuario)

        # Regla facultad: 1 Coordinadora para toda la facultad -> puede aprobar de cualquier programa.
        # (Solo se bloquea si el rol no es directivo; la vista ya exige COORDINADOR/DECANA.)

        documento.estado = Documento.Estado.APROBADO
        documento.save(update_fields=['estado', 'fecha_modificacion'])

        # Auditoría
        AuditService.log(
            usuario=usuario, accion='APROBO', documento=documento, request=request
        )

        # Notificar al autor
        NotificacionService.crear_notificacion(
            usuario=documento.autor,
            mensaje=f'Tu documento "{documento.titulo}" ha sido aprobado por {usuario.get_full_name()}.',
            tipo='APROBADO',
            documento=documento
        )

        bump_stats()
        return documento

    @staticmethod
    def rechazar_documento(documento_id, usuario, comentario, request=None):
        """Rechaza un documento y notifica al autor."""
        documento = Documento.objects.get(pk=documento_id)
        DocumentoService._validar_revision(documento, usuario)

        # Regla facultad: 1 Coordinadora para toda la facultad -> puede rechazar de cualquier programa.

        documento.estado = Documento.Estado.RECHAZADO
        documento.comentario_rechazo = comentario
        documento.save(update_fields=['estado', 'comentario_rechazo', 'fecha_modificacion'])

        # Auditoría
        AuditService.log(
            usuario=usuario, accion='RECHAZO', documento=documento, request=request, detalle=comentario
        )

        # Notificar al autor
        NotificacionService.crear_notificacion(
            usuario=documento.autor,
            mensaje=f'Tu documento "{documento.titulo}" fue rechazado. Motivo: {comentario}',
            tipo='RECHAZADO',
            documento=documento
        )

        bump_stats()
        return documento

    @staticmethod
    def eliminar_documento(documento_id, usuario=None, request=None):
        """Envía un documento a la papelera (Soft Delete)."""
        from django.utils import timezone
        # Use all_objects in case we are deleting something that's somehow already hidden, though typically objects is fine
        documento = Documento.all_objects.get(pk=documento_id)

        # H-02: solo autor, DECANA o COORDINADOR (única de facultad) pueden enviar a papelera.
        if usuario is None or not getattr(usuario, 'is_authenticated', False):
            raise PermissionError("Inicia sesión para eliminar evidencias.")
        es_autor = (usuario == documento.autor or getattr(usuario, 'pk', None) == getattr(documento, 'autor_id', None))
        if not (es_autor or getattr(usuario, 'rol', None) in ('DECANA', 'COORDINADOR')):
            raise PermissionError("No tienes permiso para eliminar este documento.")

        documento.is_deleted = True
        documento.deleted_at = timezone.now()
        documento.save()

        # Auditoría
        if usuario:
            AuditService.log(
                usuario=usuario, accion='ELIMINO', documento=documento, request=request,
                detalle=f'Envió a la papelera: {documento.titulo}'
            )

        bump_stats()
        return True

    @staticmethod
    def restaurar_documento(documento_id, usuario=None, request=None):
        """Restaura un documento desde la papelera."""
        documento = Documento.all_objects.get(pk=documento_id)

        # H-02: mismo control que eliminar.
        if usuario is None or not getattr(usuario, 'is_authenticated', False):
            raise PermissionError("Inicia sesión para restaurar evidencias.")
        es_autor = (usuario == documento.autor or getattr(usuario, 'pk', None) == getattr(documento, 'autor_id', None))
        if not (es_autor or getattr(usuario, 'rol', None) in ('DECANA', 'COORDINADOR')):
            raise PermissionError("No tienes permiso para restaurar este documento.")
        
        documento.is_deleted = False
        documento.deleted_at = None
        documento.save()

        if usuario:
            AuditService.log(
                usuario=usuario, accion='ACTUALIZO', documento=documento, request=request,
                detalle=f'Restauró de la papelera: {documento.titulo}'
            )
        bump_stats()
        return True

    @staticmethod
    def registrar_descarga(documento_id, usuario, request, detalle=''):
        """Registra la descarga en auditoría y retorna el archivo."""
        from ..permisos.services import PermisoService
        doc = Documento.objects.get(pk=documento_id)
        
        puede_descargar = PermisoService.usuario_tiene_acceso(usuario, doc)
        if not puede_descargar:
            raise PermissionError("No tienes permiso para descargar este documento.")

        AuditService.log(
            usuario=usuario, accion='DESCARGO', documento=doc, request=request, detalle=detalle or ''
        )
        return doc.archivo.path

    @staticmethod
    def archivo_para_vista_previa(documento_id, usuario, request=None):
        """A4: ruta del PDF vigente si el usuario puede verlo. Audita el resultado.

        Lanza Documento.DoesNotExist, PermissionError (ya auditado como
        ACCESO_DENEGADO) o FileNotFoundError (formato sin vista previa o
        archivo físico ausente).
        """
        import os
        from ..permisos.services import PermisoService

        doc = Documento.objects.get(pk=documento_id)
        if not PermisoService.usuario_tiene_acceso(usuario, doc):
            AuditService.log(usuario=usuario, accion='ACCESO_DENEGADO', documento=doc,
                             request=request, detalle='Intento de vista previa sin permiso')
            raise PermissionError("No tienes permiso para ver este documento.")
        if not doc.archivo or not doc.archivo.name.lower().endswith('.pdf'):
            raise FileNotFoundError('Formato sin vista previa.')
        ruta = doc.archivo.path
        if not os.path.exists(ruta):
            raise FileNotFoundError('Archivo físico ausente.')
        AuditService.log(usuario=usuario, accion='VISUALIZO', documento=doc, request=request)
        return ruta

    @staticmethod
    def listar_categorias():
        """Lista todas las categorías (cache 1h: catálogo casi estático)."""
        cats = cache.get("sigea:categorias")
        if cats is None:
            cats = list(Categoria.objects.all())
            cache.set("sigea:categorias", cats, 3600)
        return cats

    # ─── ESTADÍSTICAS PARA DASHBOARD ─────────────────────────────

    @staticmethod
    def stats_docente(usuario):
        """Estadísticas para el dashboard del docente."""
        mis_docs = Documento.objects.filter(autor=usuario)
        conteo = conteo_cacheado(
            f"dash:docente:{usuario.id}",
            lambda: mis_docs.aggregate(
                total=Count('id'),
                pendientes=Count('id', filter=Q(estado='PENDIENTE')),
                aprobados=Count('id', filter=Q(estado='APROBADO')),
                rechazados=Count('id', filter=Q(estado='RECHAZADO')),
            ),
        )
        return {
            'mis_docs_count': conteo['total'],
            'pendientes_count': conteo['pendientes'],
            'aprobados_count': conteo['aprobados'],
            'rechazados_count': conteo['rechazados'],
            'actividad_reciente': mis_docs.select_related('categoria')[:5],
            'notificaciones': NotificacionService.listar_notificaciones(usuario, solo_no_leidas=False)[:4],
        }

    @staticmethod
    def stats_coordinador(usuario):
        """Estadísticas para el dashboard del coordinador."""
        mis_docs = Documento.objects.filter(autor=usuario)
        _ahora = timezone.now()
        inicio_hoy = _ahora.replace(hour=0, minute=0, second=0, microsecond=0)
        fin_hoy = inicio_hoy + timedelta(days=1)
        # Regla facultad: la Coordinadora ve toda la facultad, no solo su programa.
        docs_programa = Documento.objects.all()
        conteo = conteo_cacheado(
            f"dash:coord:{usuario.id}",
            lambda: docs_programa.aggregate(
                por_aprobar=Count('id', filter=Q(estado='PENDIENTE')),
                aprobados_hoy=Count(
                    'id', filter=Q(
                        estado='APROBADO',
                        fecha_modificacion__gte=inicio_hoy,
                        fecha_modificacion__lt=fin_hoy,
                    )
                ),
                rechazados_hoy=Count(
                    'id', filter=Q(
                        estado='RECHAZADO',
                        fecha_modificacion__gte=inicio_hoy,
                        fecha_modificacion__lt=fin_hoy,
                    )
                ),
            ),
        )

        return {
            'mis_docs_count': mis_docs.count(),
            'por_aprobar_count': conteo['por_aprobar'],
            'aprobados_hoy_count': conteo['aprobados_hoy'],
            'rechazados_hoy_count': conteo['rechazados_hoy'],
            'docs_pendientes': docs_programa.filter(
                estado='PENDIENTE'
            ).select_related('autor', 'categoria')[:10],
            'notificaciones': NotificacionService.listar_notificaciones(usuario, solo_no_leidas=False)[:5],
        }

    @staticmethod
    def stats_decana():
        """Estadísticas para el dashboard de la decana."""
        from ..auditoria.models import RegistroAuditoria

        todos = Documento.objects.all()
        _ahora_mes = timezone.now()
        # H-13: inicio de mes como rango (index-friendly) en vez de __date.
        desde_mes = _ahora_mes.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        hace_3_dias = timezone.now() - timedelta(days=3)

        categorias_conteo = Categoria.objects.annotate(
            cantidad=Count('documentos')
        ).order_by('-cantidad')

        conteo = conteo_cacheado(
            "dash:decana",
            lambda: todos.aggregate(
                total=Count('id'),
                por_aprobar=Count('id', filter=Q(estado='PENDIENTE')),
                este_mes=Count('id', filter=Q(fecha_creacion__gte=desde_mes)),
            ),
        )

        return {
            'total_docs_count': conteo['total'],
            'por_aprobar_count': conteo['por_aprobar'],
            'usuarios_activos_count': Usuario.objects.filter(
                is_active=True, esta_habilitado=True
            ).count(),
            'docs_este_mes_count': conteo['este_mes'],
            'categorias_conteo': categorias_conteo,
            'trazabilidad_reciente': RegistroAuditoria.objects.select_related(
                'usuario', 'documento'
            )[:5],
            'hay_docs_vencidos': todos.filter(
                estado='PENDIENTE', fecha_modificacion__lt=hace_3_dias
            ).exists(),
        }

class ReporteService:
    """Servicio para la generación de reportes y estadísticas."""

    @staticmethod
    def obtener_estadisticas_cna():
        """Obtiene las estadísticas de documentos agrupados por factor CNA."""
        from django.db.models import Count, Q
        
        from .metricas import METAS_POR_FACTOR as metas_por_factor

        stats = Documento.objects.exclude(factor_cna__isnull=True).exclude(factor_cna='').values('factor_cna').annotate(
            total_aprobados=Count('id', filter=Q(estado='APROBADO')),
            total_pendientes=Count('id', filter=Q(estado='PENDIENTE'))
        )
        stats_dict = {item['factor_cna']: item for item in stats}

        factores_data = []
        total_requeridos = 0
        total_aprobados_global = 0

        for codigo, nombre in Documento.FACTORES_CNA:
            meta = metas_por_factor.get(codigo, 10)
            total_requeridos += meta

            f_stats = stats_dict.get(codigo, {'total_aprobados': 0, 'total_pendientes': 0})
            aprobados = f_stats['total_aprobados']
            pendientes = f_stats['total_pendientes']
            
            faltantes = max(0, meta - aprobados)
            porcentaje = int((aprobados / meta) * 100) if meta > 0 else 100
            if porcentaje > 100: porcentaje = 100

            total_aprobados_global += aprobados
            nombre_limpio = nombre.split(':', 1)[-1].strip() if ':' in nombre else nombre

            factores_data.append({
                'codigo': codigo,
                'numero': codigo.replace('F', ''),
                'nombre': nombre_limpio,
                'aprobados': aprobados,
                'pendientes': pendientes,
                'faltantes': faltantes,
                'porcentaje': porcentaje,
                'meta': meta
            })

        total_faltantes_global = max(0, total_requeridos - total_aprobados_global)
        progreso_general = int((total_aprobados_global / total_requeridos) * 100) if total_requeridos > 0 else 0
        if progreso_general > 100: progreso_general = 100

        return {
            'factores': factores_data,
            'total_requeridos': total_requeridos,
            'total_aprobados': total_aprobados_global,
            'total_faltantes': total_faltantes_global,
            'progreso_general': progreso_general,
        }

    @staticmethod
    def generar_csv_cna():
        """Genera un archivo CSV en memoria con las estadísticas CNA, optimizado para Excel."""
        import csv
        import io
        
        datos = ReporteService.obtener_estadisticas_cna()
        output = io.StringIO()
        
        # Excel en español suele requerir el separador ';'
        writer = csv.writer(output, delimiter=';')
        
        # Escribir cabeceras
        writer.writerow(['Factor', 'Nombre', 'Meta Requerida', 'Aprobados', 'En Revisión', 'Faltantes', 'Porcentaje de Cumplimiento'])
        
        # Escribir filas
        for f in datos['factores']:
            writer.writerow([
                f['codigo'],
                f['nombre'],
                f['meta'],
                f['aprobados'],
                f['pendientes'],
                f['faltantes'],
                f"{f['porcentaje']}%"
            ])
            
        # Fila de totales
        writer.writerow([])
        writer.writerow(['TOTALES', '', datos['total_requeridos'], datos['total_aprobados'], '', datos['total_faltantes'], f"{datos['progreso_general']}%"])
        
        # Para que Excel lo lea bien (con tildes), devolvemos el string crudo y en la vista lo encodeamos con utf-8-sig
        return output.getvalue()

    @staticmethod
    def generar_pdf_cna(response):
        """Genera un reporte PDF de las estadísticas CNA utilizando ReportLab, escribiendo en el response."""
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from django.utils import timezone

        datos = ReporteService.obtener_estadisticas_cna()

        # Configurar documento (A4 Horizontal para acomodar tabla)
        doc = SimpleDocTemplate(response, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        elements = []
        styles = getSampleStyleSheet()

        # Título
        title_style = styles['Heading1']
        title_style.alignment = 1 # Center
        elements.append(Paragraph("Reporte de Estadísticas CNA (SIGEA)", title_style))
        elements.append(Spacer(1, 10))

        # Subtítulo y Fecha
        normal_style = styles['Normal']
        fecha_str = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        elements.append(Paragraph(f"Fecha de generación: {fecha_str}", normal_style))
        elements.append(Paragraph(f"Progreso General Documental: {datos['progreso_general']}% completado", normal_style))
        elements.append(Spacer(1, 20))

        # Datos para la tabla
        table_data = [['Factor', 'Nombre del Factor', 'Meta', 'Aprobados', 'En Revisión', 'Faltantes', '% Cumplimiento']]
        for f in datos['factores']:
            table_data.append([
                f['codigo'],
                Paragraph(f['nombre'], normal_style),
                str(f['meta']),
                str(f['aprobados']),
                str(f['pendientes']),
                str(f['faltantes']),
                f"{f['porcentaje']}%"
            ])
        
        # Fila de Totales
        table_data.append(['TOTALES', '', str(datos['total_requeridos']), str(datos['total_aprobados']), '', str(datos['total_faltantes']), f"{datos['progreso_general']}%"])

        # Crear y dar estilo a la tabla
        t = Table(table_data, colWidths=[50, 350, 50, 70, 70, 70, 90])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')), # Slate 900
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#F8FAFC')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.HexColor('#F8FAFC'), colors.HexColor('#FFFFFF')]),
            ('GRID', (0, 0), (-1, -2), 1, colors.HexColor('#E2E8F0')),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'), # El nombre a la izquierda
            # Estilo Totales
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#CBD5E1')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(t)
        doc.build(elements)
