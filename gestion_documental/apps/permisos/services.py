"""
Servicios del módulo de permisos.

Contiene toda la lógica de negocio relacionada con la asignación
y verificación de permisos, solicitudes de acceso y votos sensibles.
"""
from django.utils import timezone
from .models import PermisoDocumento, SolicitudAcceso, VotoAccesoSensible
from ..notificaciones.services import NotificacionService
from ..usuarios.models import Usuario


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
    def usuario_tiene_acceso(usuario, documento):
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
        return PermisoDocumento.objects.filter(
            usuario=usuario,
            documento=documento,
            puede_ver=True
        ).exists()

    # ─── SOLICITUDES DE ACCESO ───────────────────────────────────

    @staticmethod
    def solicitar_acceso(solicitante, documento_id, motivo):
        """
        Crea una solicitud de acceso a un documento.
        Notifica según si el documento es sensible o no.
        """
        from ..documentos.models import Documento

        documento = Documento.objects.get(pk=documento_id)

        # Verificar que no sea el autor
        if documento.autor == solicitante:
            raise Exception("Eres el autor de este documento.")

        # Verificar que no tenga ya un permiso activo
        if PermisoDocumento.objects.filter(
            usuario=solicitante, documento=documento, puede_ver=True
        ).exists():
            raise Exception("Ya tienes acceso a este documento.")

        # Verificar solicitud PENDIENTE existente
        solicitud_existente = SolicitudAcceso.objects.filter(
            solicitante=solicitante, documento=documento
        ).first()

        if solicitud_existente:
            if solicitud_existente.estado == 'PENDIENTE':
                raise Exception("Ya tienes una solicitud pendiente para este documento.")
            # Si fue RECHAZADA, permitir nueva solicitud (eliminar anterior)
            solicitud_existente.delete()

        # Crear solicitud
        solicitud = SolicitudAcceso.objects.create(
            solicitante=solicitante,
            documento=documento,
            motivo=motivo,
            estado='PENDIENTE'
        )

        # NOTIFICACIONES según tipo de documento
        if documento.es_sensible:
            # Notificar al autor + coordinadores del programa + decanas
            destinatarios = set()
            destinatarios.add(documento.autor)

            coordinadores = Usuario.objects.filter(
                rol='COORDINADOR',
                programa_academico=documento.programa
            )
            for coord in coordinadores:
                destinatarios.add(coord)

            decanas = Usuario.objects.filter(rol='DECANA')
            for decana in decanas:
                destinatarios.add(decana)

            for dest in destinatarios:
                NotificacionService.crear_notificacion(
                    usuario=dest,
                    mensaje=(
                        f"{solicitante.get_full_name()} solicitó acceso al documento "
                        f"sensible '{documento.titulo}'. Se requiere tu aprobación "
                        f"en Gestionar Accesos."
                    ),
                    tipo='INFO',
                    documento=documento
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
    def responder_solicitud_normal(solicitud_id, respondedor, decision, motivo_rechazo=None):
        """
        Responde una solicitud de acceso para documentos NO sensibles.
        Solo puede responder el autor del documento.
        """
        solicitud = SolicitudAcceso.objects.select_related(
            'documento', 'solicitante'
        ).get(pk=solicitud_id)

        # Verificar que el respondedor sea el autor
        if respondedor != solicitud.documento.autor:
            raise Exception("Solo el autor puede responder esta solicitud.")

        # Verificar que esté pendiente
        if solicitud.estado != 'PENDIENTE':
            raise Exception("Esta solicitud ya fue respondida.")

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
                raise Exception("El motivo de rechazo es obligatorio.")

            solicitud.estado = 'RECHAZADA'
            solicitud.motivo_rechazo = motivo_rechazo
            solicitud.fecha_respuesta = timezone.now()
            solicitud.respondido_por = respondedor
            solicitud.save()

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
    def votar_acceso_sensible(solicitud_id, votante, voto, motivo_rechazo=None):
        """
        Registra un voto para una solicitud de acceso a documento sensible.
        Requiere 2 aprobaciones para conceder acceso.
        Un solo rechazo deniega inmediatamente.
        """
        solicitud = SolicitudAcceso.objects.select_related(
            'documento', 'documento__programa', 'solicitante'
        ).get(pk=solicitud_id)
        documento = solicitud.documento

        # Verificar que el votante tiene derecho a votar
        es_autor = (votante == documento.autor)
        es_coordinador = (votante.rol == 'COORDINADOR')
        es_decana = (votante.rol == 'DECANA')

        if not (es_autor or es_coordinador or es_decana):
            raise Exception("No tienes permiso para votar en esta solicitud.")

        # Verificar que no haya votado ya
        if VotoAccesoSensible.objects.filter(
            solicitud=solicitud, votante=votante
        ).exists():
            raise Exception("Ya emitiste tu voto para esta solicitud.")

        # Verificar que esté pendiente
        if solicitud.estado != 'PENDIENTE':
            raise Exception("Esta solicitud ya fue resuelta.")

        if voto == 'RECHAZADO':
            if not motivo_rechazo or not motivo_rechazo.strip():
                raise Exception("El motivo de rechazo es obligatorio.")

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
    def revocar_acceso(documento_id, usuario_id, revocador):
        """
        Revoca el acceso de un usuario a un documento.
        Solo el autor del documento puede revocar accesos.
        """
        from ..documentos.models import Documento

        documento = Documento.objects.get(pk=documento_id)
        usuario = Usuario.objects.get(pk=usuario_id)

        if revocador != documento.autor:
            raise Exception("Solo el autor puede revocar accesos.")

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
            queryset = queryset.filter(documento__programa=usuario.programa_academico)
        elif usuario.rol != 'DECANA':
            queryset = queryset.none()
        return queryset
