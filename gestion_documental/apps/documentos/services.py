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
        """Elimina un documento y su archivo asociado."""
        documento = Documento.objects.get(pk=documento_id)

        # Auditoría
        if usuario:
            AuditService.log(
                usuario=usuario, accion='ELIMINO', documento=documento, request=request,
                detalle=f'Eliminó: {documento.titulo}'
            )

        StorageService.delete_document(documento.archivo.name)
        documento.delete()
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
