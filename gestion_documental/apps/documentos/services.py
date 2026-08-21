"""
Servicios del módulo de documentos.

Contiene toda la lógica de negocio relacionada con la gestión de documentos.
"""
from datetime import timedelta

from django.db.models import Q, Count
from django.utils import timezone

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

        # Notificaciones si va a revisión
        if estado == 'PENDIENTE':
            if autor.rol == 'DOCENTE_PLANTA':
                # Notificar al Coordinador del programa
                coordinadores = Usuario.objects.filter(
                    rol='COORDINADOR',
                    programa_academico=autor.programa_academico
                )
                for coord in coordinadores:
                    NotificacionService.crear_notificacion(
                        usuario=coord,
                        mensaje=f"{autor.get_full_name()} subió '{titulo}' y requiere tu revisión.",
                        tipo='INFO',
                        documento=documento
                    )
            elif autor.rol == 'COORDINADOR':
                # Notificar a la Decana
                decanas = Usuario.objects.filter(rol='DECANA')
                for decana in decanas:
                    NotificacionService.crear_notificacion(
                        usuario=decana,
                        mensaje=f"{autor.get_full_name()} subió '{titulo}' y requiere tu revisión.",
                        tipo='INFO',
                        documento=documento
                    )

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
        puede_aprobar = usuario.rol in ('COORDINADOR', 'DECANA') and doc.estado == 'PENDIENTE'
        puede_descargar = tiene_acceso
        puede_ver = tiene_acceso
        
        if not puede_ver:
            raise PermissionError("No tienes permiso para ver este documento.")

        # Verificar si el usuario puede gestionar accesos
        puede_gestionar_accesos = (
            usuario == doc.autor or
            (usuario.rol == 'COORDINADOR' and usuario.programa_academico == doc.programa) or
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
                          visibilidad_filter=None, orden=None):
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
        if visibilidad_filter and usuario.rol in ('COORDINADOR', 'DECANA'):
            queryset = queryset.filter(visibilidad=visibilidad_filter)
        if query:
            queryset = queryset.filter(Q(titulo__icontains=query) | Q(descripcion__icontains=query))
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        if factor_cna:
            queryset = queryset.filter(factor_cna=factor_cna)
        if estado:
            queryset = queryset.filter(estado=estado)
        if fecha_desde:
            queryset = queryset.filter(fecha_creacion__date__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_creacion__date__lte=fecha_hasta)
        if autor_query:
            queryset = queryset.filter(
                Q(autor__first_name__icontains=autor_query) |
                Q(autor__last_name__icontains=autor_query) |
                Q(autor__email__icontains=autor_query)
            )
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
    def aprobar_documento(documento_id, usuario, request=None):
        """Aprueba un documento y notifica al autor."""
        documento = Documento.objects.get(pk=documento_id)
        
        # Validación de seguridad: Coordinadores solo pueden aprobar de su propio programa
        if usuario.rol == 'COORDINADOR' and documento.programa != usuario.programa_academico:
            raise PermissionError("No tienes permiso para gestionar documentos de otro programa.")

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

        return documento

    @staticmethod
    def rechazar_documento(documento_id, usuario, comentario, request=None):
        """Rechaza un documento y notifica al autor."""
        documento = Documento.objects.get(pk=documento_id)
        
        # Validación de seguridad: Coordinadores solo pueden rechazar de su propio programa
        if usuario.rol == 'COORDINADOR' and documento.programa != usuario.programa_academico:
            raise PermissionError("No tienes permiso para gestionar documentos de otro programa.")

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

        return documento

    @staticmethod
    def eliminar_documento(documento_id, usuario=None, request=None):
        """Envía un documento a la papelera (Soft Delete)."""
        from django.utils import timezone
        # Use all_objects in case we are deleting something that's somehow already hidden, though typically objects is fine
        documento = Documento.all_objects.get(pk=documento_id)

        documento.is_deleted = True
        documento.deleted_at = timezone.now()
        documento.save()

        # Auditoría
        if usuario:
            AuditService.log(
                usuario=usuario, accion='ELIMINO', documento=documento, request=request,
                detalle=f'Envió a la papelera: {documento.titulo}'
            )

        return True

    @staticmethod
    def restaurar_documento(documento_id, usuario=None, request=None):
        """Restaura un documento desde la papelera."""
        documento = Documento.all_objects.get(pk=documento_id)
        
        documento.is_deleted = False
        documento.deleted_at = None
        documento.save()

        if usuario:
            AuditService.log(
                usuario=usuario, accion='ACTUALIZO', documento=documento, request=request,
                detalle=f'Restauró de la papelera: {documento.titulo}'
            )
        return True

    @staticmethod
    def registrar_descarga(documento_id, usuario, request):
        """Registra la descarga en auditoría y retorna el archivo."""
        from ..permisos.services import PermisoService
        doc = Documento.objects.get(pk=documento_id)
        
        puede_descargar = PermisoService.usuario_tiene_acceso(usuario, doc)
        if not puede_descargar:
            raise PermissionError("No tienes permiso para descargar este documento.")

        AuditService.log(
            usuario=usuario, accion='DESCARGO', documento=doc, request=request
        )
        return doc.archivo.path

    @staticmethod
    def listar_categorias():
        """Lista todas las categorías."""
        return Categoria.objects.all()

    # ─── ESTADÍSTICAS PARA DASHBOARD ─────────────────────────────

    @staticmethod
    def stats_docente(usuario):
        """Estadísticas para el dashboard del docente."""
        mis_docs = Documento.objects.filter(autor=usuario)
        return {
            'mis_docs_count': mis_docs.count(),
            'pendientes_count': mis_docs.filter(estado='PENDIENTE').count(),
            'aprobados_count': mis_docs.filter(estado='APROBADO').count(),
            'rechazados_count': mis_docs.filter(estado='RECHAZADO').count(),
            'actividad_reciente': mis_docs.select_related('categoria')[:5],
            'notificaciones': NotificacionService.listar_notificaciones(usuario, solo_no_leidas=False)[:4],
        }

    @staticmethod
    def stats_coordinador(usuario):
        """Estadísticas para el dashboard del coordinador."""
        mis_docs = Documento.objects.filter(autor=usuario)
        hoy = timezone.now().date()
        programa = usuario.programa_academico
        docs_programa = Documento.objects.filter(programa=programa) if programa else Documento.objects.none()

        return {
            'mis_docs_count': mis_docs.count(),
            'por_aprobar_count': docs_programa.filter(estado='PENDIENTE').count(),
            'aprobados_hoy_count': docs_programa.filter(
                estado='APROBADO', fecha_modificacion__date=hoy
            ).count(),
            'rechazados_hoy_count': docs_programa.filter(
                estado='RECHAZADO', fecha_modificacion__date=hoy
            ).count(),
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
        hoy = timezone.now().date()
        inicio_mes = hoy.replace(day=1)
        hace_3_dias = timezone.now() - timedelta(days=3)

        categorias_conteo = Categoria.objects.annotate(
            cantidad=Count('documentos')
        ).order_by('-cantidad')

        return {
            'total_docs_count': todos.count(),
            'por_aprobar_count': todos.filter(estado='PENDIENTE').count(),
            'usuarios_activos_count': Usuario.objects.filter(
                is_active=True, esta_habilitado=True
            ).count(),
            'docs_este_mes_count': todos.filter(
                fecha_creacion__date__gte=inicio_mes
            ).count(),
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
        
        metas_por_factor = {
            'F1': 15, 'F2': 25, 'F3': 20, 'F4': 10, 'F5': 30, 'F6': 15,
            'F7': 10, 'F8': 20, 'F9': 15, 'F10': 15, 'F11': 20, 'F12': 10,
        }

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
