"""
Servicios del módulo de permisos.

Contiene toda la lógica de negocio relacionada con la asignación
y verificación de permisos, solicitudes de acceso y votos sensibles.
"""
from django.utils import timezone
from django.db import transaction
from .models import PermisoDocumento, SolicitudAcceso, VotoAccesoSensible
from ..notificaciones.services import NotificacionService
from ..usuarios.models import Usuario
from core.services.audit_service import AuditService
from core.utils.helpers import ReglaNegocioError


class PermisoService:
    """Servicio para la gestión de permisos de documentos."""

    # ─── PERMISOS BÁSICOS ────────────────────────────────────────

    @staticmethod
    def asignar_permiso(usuario, documento, puede_ver=True, puede_descargar=True, otorgado_por=None):
        """Asigna o actualiza permisos de un usuario sobre un documento."""
        permiso, created = PermisoDocumento.objects.update_or_create(
            usuario=usuario,
            documento=documento,
            defaults={
                'puede_ver': puede_ver,
                'puede_descargar': puede_descargar,
                'otorgado_por': otorgado_por,
            }
        )
        return permiso

    @staticmethod
    def revocar_permiso(usuario, documento):
        """Revoca todos los permisos de un usuario sobre un documento."""
        PermisoDocumento.objects.filter(
            usuario=usuario,
            documento=documento,
        ).delete()

    @staticmethod
    def verificar_permiso(usuario, documento, tipo='ver'):
        """
        Verifica si un usuario tiene un permiso específico sobre un documento.
        tipo puede ser 'ver' o 'descargar'.
        """
        try:
            permiso = PermisoDocumento.objects.get(
                usuario=usuario,
                documento=documento,
            )
            if tipo == 'ver':
                return permiso.puede_ver
            elif tipo == 'descargar':
                return permiso.puede_descargar
        except PermisoDocumento.DoesNotExist:
            return False

    @staticmethod
    def listar_permisos_documento(documento):
        """Lista todos los permisos asignados a un documento."""
        return PermisoDocumento.objects.filter(
            documento=documento
        ).select_related('usuario', 'otorgado_por')

    @staticmethod
    def listar_permisos_usuario(usuario):
        """Lista todos los permisos de un usuario."""
        return PermisoDocumento.objects.filter(
            usuario=usuario
        ).select_related('documento')

    # ─── VERIFICACIÓN DE ACCESO ──────────────────────────────────

    @staticmethod
    def precargar_accesos(usuario, doc_ids):
        """Batch para listados: 2 queries fijas en vez de 2 por documento.

        Retorna (ids_con_permiso_ver, ids_con_solicitud_pendiente).
        """
        doc_ids = list(doc_ids)
        if not doc_ids:
            return set(), set()
        permisos_ids = set(PermisoDocumento.objects.filter(
            usuario=usuario,
            documento_id__in=doc_ids,
            puede_ver=True,
        ).values_list('documento_id', flat=True))
        solicitudes_ids = set(SolicitudAcceso.objects.filter(
            solicitante=usuario,
            documento_id__in=doc_ids,
            estado='PENDIENTE',
        ).values_list('documento_id', flat=True))
        return permisos_ids, solicitudes_ids

    @staticmethod
    def usuario_tiene_acceso(usuario, documento, _permisos_ids=None):
        """
        Determina si un usuario tiene acceso REAL (detalle y descarga) a un documento.
        
        Reglas finales:
        1. Superusuario o Autor: Acceso total.
        2. Directivos (COORDINADOR, DECANA): Acceso total administrativo.
        3. Docentes: Solo con permiso explícito (solicitud aprobada).
        """
        # Acceso total para Superusuario, Autor y Directivos
        if (usuario.is_superuser or 
            documento.autor == usuario or 
            usuario.rol in ('COORDINADOR', 'DECANA')):
            return True

        # Acceso para Docentes solo si la solicitud fue aprobada
        if _permisos_ids is not None:
            return documento.id in _permisos_ids
        return PermisoDocumento.objects.filter(
            usuario=usuario,
            documento=documento,
            puede_ver=True
        ).exists()

    # ─── SOLICITUDES DE ACCESO ───────────────────────────────────

    @staticmethod
    def solicitar_acceso(solicitante, documento_id, motivo, request=None):
        """
        Crea una solicitud de acceso a un documento.
        Notifica según si el documento es sensible o no.
        """
        from ..documentos.models import Documento

        documento = Documento.objects.get(pk=documento_id)

        # Verificar que no sea el autor
        if documento.autor == solicitante:
            raise ReglaNegocioError("Eres el autor de este documento.")

        # Verificar que no tenga ya un permiso activo
        if PermisoDocumento.objects.filter(
            usuario=solicitante, documento=documento, puede_ver=True
        ).exists():
            raise ReglaNegocioError("Ya tienes acceso a este documento.")

        # Verificar solicitud PENDIENTE existente
        solicitud_existente = SolicitudAcceso.objects.filter(
            solicitante=solicitante, documento=documento
        ).first()

        if solicitud_existente:
            if solicitud_existente.estado == 'PENDIENTE':
                raise ReglaNegocioError("Ya tienes una solicitud pendiente para este documento.")
            # Si fue RECHAZADA, permitir nueva solicitud (eliminar anterior)
            solicitud_existente.delete()

        # Crear solicitud
        solicitud = SolicitudAcceso.objects.create(
            solicitante=solicitante,
            documento=documento,
            motivo=motivo,
            estado='PENDIENTE'
        )
        AuditService.log(
            usuario=solicitante, accion='SOLICITO_ACCESO', documento=documento,
            request=request, detalle=f"Motivo: {motivo}",
        )

        # NOTIFICACIONES según tipo de documento
        if documento.es_sensible:
            # A3: autor + Coordinadora de facultad + Decana (quienes votan), sin duplicados.
            NotificacionService.notificar_revisores(
                documento,
                (
                    f"{solicitante.get_full_name()} solicitó acceso al documento "
                    f"sensible '{documento.titulo}'. Se requiere tu aprobación "
                    f"en Gestionar Accesos."
                ),
                actor=solicitante,
                incluir_decana=True,
                extra=[documento.autor],
            )
        else:
            # Solo notificar al autor
            NotificacionService.crear_notificacion(
                usuario=documento.autor,
                mensaje=(
                    f"{solicitante.get_full_name()} solicitó acceso a tu documento "
                    f"'{documento.titulo}'. Revisa la solicitud en Gestionar Accesos."
                ),
                tipo='INFO',
                documento=documento
            )

        return solicitud

    # ─── RESPUESTA A SOLICITUDES (DOCUMENTOS NORMALES) ───────────

    @staticmethod
    def responder_solicitud_normal(solicitud_id, respondedor, decision, motivo_rechazo=None, request=None):
        """
        Responde una solicitud de acceso para documentos NO sensibles.
        Solo puede responder el autor del documento.
        """
        solicitud = SolicitudAcceso.objects.select_related(
            'documento', 'solicitante'
        ).get(pk=solicitud_id)

        # Verificar que el respondedor sea el autor
        if respondedor != solicitud.documento.autor:
            raise ReglaNegocioError("Solo el autor puede responder esta solicitud.")

        # Verificar que esté pendiente
        if solicitud.estado != 'PENDIENTE':
            raise ReglaNegocioError("Esta solicitud ya fue respondida.")

        if decision == 'APROBADA':
            # Crear permiso
            PermisoService.asignar_permiso(
                solicitud.solicitante,
                solicitud.documento,
                puede_ver=True,
                puede_descargar=True,
                otorgado_por=respondedor
            )
            solicitud.estado = 'APROBADA'
            solicitud.fecha_respuesta = timezone.now()
            solicitud.respondido_por = respondedor
            solicitud.save()
            AuditService.log(
                usuario=respondedor, accion='APROBO_ACCESO', documento=solicitud.documento,
                request=request, detalle=f"Acceso concedido a {solicitud.solicitante.email}",
            )

            NotificacionService.crear_notificacion(
                usuario=solicitud.solicitante,
                mensaje=(
                    f"Tu solicitud de acceso al documento "
                    f"'{solicitud.documento.titulo}' fue aprobada. "
                    f"Ya puedes verlo en Mis documentos."
                ),
                tipo='APROBADO',
                documento=solicitud.documento
            )

        elif decision == 'RECHAZADA':
            if not motivo_rechazo or not motivo_rechazo.strip():
                raise ReglaNegocioError("El motivo de rechazo es obligatorio.")

            solicitud.estado = 'RECHAZADA'
            solicitud.motivo_rechazo = motivo_rechazo
            solicitud.fecha_respuesta = timezone.now()
            solicitud.respondido_por = respondedor
            solicitud.save()
            AuditService.log(
                usuario=respondedor, accion='RECHAZO_ACCESO', documento=solicitud.documento,
                request=request,
                detalle=f"Solicitud de {solicitud.solicitante.email} rechazada. Motivo: {motivo_rechazo}",
            )

            NotificacionService.crear_notificacion(
                usuario=solicitud.solicitante,
                mensaje=(
                    f"Tu solicitud de acceso al documento "
                    f"'{solicitud.documento.titulo}' fue rechazada. "
                    f"Motivo: {motivo_rechazo}"
                ),
                tipo='RECHAZADO',
                documento=solicitud.documento
            )

        return solicitud

    # ─── VOTOS PARA DOCUMENTOS SENSIBLES ─────────────────────────

    @staticmethod
    def votar_acceso_sensible(solicitud_id, votante, voto, motivo_rechazo=None, request=None):
        """
        Registra un voto para una solicitud de acceso a documento sensible.
        Requiere 2 aprobaciones para conceder acceso.
        Un solo rechazo deniega inmediatamente.
        """
        # R2-02: la transición del quórum debe ser atómica y con la fila bloqueada
        with transaction.atomic():
            solicitud = SolicitudAcceso.objects.select_for_update().select_related(
                'documento', 'documento__programa', 'solicitante'
            ).get(pk=solicitud_id)
            return PermisoService._aplicar_voto(solicitud, votante, voto, motivo_rechazo, request)

    @staticmethod
    def _aplicar_voto(solicitud, votante, voto, motivo_rechazo=None, request=None):
        """Aplica un voto con la solicitud ya bloqueada (llamar dentro de transaction.atomic)."""
        documento = solicitud.documento

        # Verificar que el votante tiene derecho a votar
        # Regla facultad: DECANA y COORDINADOR son únicos de facultad -> acceso total.
        # (Si a futuro hay un coordinador por programa, restringir aquí por programa.)
        es_autor = (votante == documento.autor)
        es_decana = (votante.rol == 'DECANA')
        es_coordinador = (votante.rol == 'COORDINADOR')

        if not (es_autor or es_coordinador or es_decana):
            raise ReglaNegocioError("No tienes permiso para votar en esta solicitud.")

        # R2-02: separación de funciones — el beneficiario no vota su propia solicitud
        if votante == solicitud.solicitante or getattr(votante, 'pk', None) == getattr(solicitud, 'solicitante_id', None):
            raise ReglaNegocioError("No puedes votar tu propia solicitud.")

        # Verificar que no haya votado ya
        if VotoAccesoSensible.objects.filter(
            solicitud=solicitud, votante=votante
        ).exists():
            raise ReglaNegocioError("Ya emitiste tu voto para esta solicitud.")

        # Verificar que esté pendiente
        if solicitud.estado != 'PENDIENTE':
            raise ReglaNegocioError("Esta solicitud ya fue resuelta.")

        if voto not in ('APROBADO', 'RECHAZADO'):
            raise ReglaNegocioError("Decisión no válida.")

        if voto == 'RECHAZADO':
            if not motivo_rechazo or not motivo_rechazo.strip():
                raise ReglaNegocioError("El motivo de rechazo es obligatorio.")

            # Crear voto de rechazo
            VotoAccesoSensible.objects.create(
                solicitud=solicitud,
                votante=votante,
                voto='RECHAZADO',
                motivo_rechazo=motivo_rechazo
            )

            # Un rechazo basta para denegar
            solicitud.estado = 'RECHAZADA'
            solicitud.motivo_rechazo = motivo_rechazo
            solicitud.fecha_respuesta = timezone.now()
            solicitud.respondido_por = votante
            solicitud.save()
            AuditService.log(
                usuario=votante, accion='VOTO_ACCESO', documento=documento, request=request,
                detalle=f"Voto RECHAZADO sobre solicitud de {solicitud.solicitante.email}",
            )
            AuditService.log(
                usuario=votante, accion='RECHAZO_ACCESO', documento=documento, request=request,
                detalle=f"Solicitud de {solicitud.solicitante.email} rechazada. Motivo: {motivo_rechazo}",
            )

            NotificacionService.crear_notificacion(
                usuario=solicitud.solicitante,
                mensaje=(
                    f"Tu solicitud de acceso al documento sensible "
                    f"'{documento.titulo}' fue rechazada. Motivo: {motivo_rechazo}"
                ),
                tipo='RECHAZADO',
                documento=documento
            )

            return solicitud

        elif voto == 'APROBADO':
            # Crear voto de aprobación
            VotoAccesoSensible.objects.create(
                solicitud=solicitud,
                votante=votante,
                voto='APROBADO'
            )

            # Contar votos aprobados
            votos_aprobados = VotoAccesoSensible.objects.filter(
                solicitud=solicitud, voto='APROBADO'
            ).count()
            AuditService.log(
                usuario=votante, accion='VOTO_ACCESO', documento=documento, request=request,
                detalle=f"Voto APROBADO ({votos_aprobados}/2) sobre solicitud de {solicitud.solicitante.email}",
            )

            if votos_aprobados >= 2:
                # Conceder acceso
                PermisoService.asignar_permiso(
                    solicitud.solicitante,
                    documento,
                    puede_ver=True,
                    puede_descargar=True,
                    otorgado_por=votante
                )
                solicitud.estado = 'APROBADA'
                solicitud.fecha_respuesta = timezone.now()
                solicitud.respondido_por = votante
                solicitud.save()
                AuditService.log(
                    usuario=votante, accion='APROBO_ACCESO', documento=documento, request=request,
                    detalle=f"Acceso sensible concedido a {solicitud.solicitante.email} con {votos_aprobados} votos",
                )

                NotificacionService.crear_notificacion(
                    usuario=solicitud.solicitante,
                    mensaje=(
                        f"Tu solicitud de acceso al documento sensible "
                        f"'{documento.titulo}' fue aprobada con "
                        f"{votos_aprobados} aprobaciones."
                    ),
                    tipo='APROBADO',
                    documento=documento
                )

        return solicitud

    # ─── REVOCAR ACCESO ──────────────────────────────────────────

    @staticmethod
    def revocar_acceso(documento_id, usuario_id, revocador, request=None):
        """
        Revoca el acceso de un usuario a un documento.
        Solo el autor del documento puede revocar accesos.
        """
        from ..documentos.models import Documento

        documento = Documento.objects.get(pk=documento_id)
        usuario = Usuario.objects.get(pk=usuario_id)

        if revocador != documento.autor:
            raise ReglaNegocioError("Solo el autor puede revocar accesos.")

        # Eliminar permiso
        PermisoDocumento.objects.filter(
            usuario=usuario, documento=documento
        ).delete()

        # Marcar solicitud como rechazada si existe
        SolicitudAcceso.objects.filter(
            solicitante=usuario,
            documento=documento,
            estado='APROBADA'
        ).update(
            estado='RECHAZADA',
            motivo_rechazo='Acceso revocado por el autor.',
            fecha_respuesta=timezone.now(),
            respondido_por=revocador
        )

        AuditService.log(
            usuario=revocador, accion='REVOCO_ACCESO', documento=documento, request=request,
            detalle=f"Acceso revocado a {usuario.email}",
        )

        # Notificar al usuario
        NotificacionService.crear_notificacion(
            usuario=usuario,
            mensaje=(
                f"Tu acceso al documento '{documento.titulo}' "
                f"fue revocado por el autor."
            ),
            tipo='INFO',
            documento=documento
        )

        return True

    # ─── CONSULTAS ───────────────────────────────────────────────

    @staticmethod
    def obtener_estado_accesos_documento(documento_id, usuario):
        """
        Retorna un dict con toda la información de accesos de un documento.
        """
        from ..documentos.models import Documento

        documento = Documento.objects.get(pk=documento_id)

        solicitudes_pendientes = SolicitudAcceso.objects.filter(
            documento=documento, estado='PENDIENTE'
        ).select_related('solicitante').order_by('-fecha_solicitud')

        usuarios_con_acceso = PermisoDocumento.objects.filter(
            documento=documento
        ).select_related('usuario', 'otorgado_por')

        solicitudes_rechazadas = SolicitudAcceso.objects.filter(
            documento=documento, estado='RECHAZADA'
        ).select_related('solicitante', 'respondido_por').order_by('-fecha_respuesta')

        # Votos por solicitud (solo para sensibles)
        votos_por_solicitud = {}
        if documento.es_sensible:
            for sol in solicitudes_pendientes:
                votos_por_solicitud[sol.id] = VotoAccesoSensible.objects.filter(
                    solicitud=sol
                ).select_related('votante')

        puede_revocar = (usuario == documento.autor)

        return {
            'solicitudes_pendientes': solicitudes_pendientes,
            'usuarios_con_acceso': usuarios_con_acceso,
            'solicitudes_rechazadas': solicitudes_rechazadas,
            'votos_por_solicitud': votos_por_solicitud,
            'puede_revocar': puede_revocar,
        }

    @staticmethod
    def listar_solicitudes_pendientes(usuario):
        """Lista las solicitudes pendientes visibles para el usuario."""
        queryset = SolicitudAcceso.objects.filter(
            estado='PENDIENTE'
        ).select_related(
            'solicitante', 'documento'
        ).order_by('-fecha_solicitud')

        if usuario.rol == 'COORDINADOR':
            # Regla facultad: la Coordinadora ve solicitudes de todos los programas.
            pass
        elif usuario.rol != 'DECANA':
            queryset = queryset.none()
        return queryset
