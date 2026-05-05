"""
Servicios del módulo de notificaciones.

Contiene toda la lógica de negocio relacionada con la gestión de notificaciones.
"""
from .models import Notificacion


class NotificacionService:
    """Servicio para la gestión de notificaciones."""

    @staticmethod
    def crear_notificacion(usuario, mensaje, tipo='INFO', documento=None):
        """Crea una nueva notificación para un usuario."""
        return Notificacion.objects.create(
            usuario=usuario,
            mensaje=mensaje,
            tipo=tipo,
            documento=documento,
        )

    @staticmethod
    def listar_notificaciones(usuario, solo_no_leidas=False):
        """Lista las notificaciones de un usuario."""
        queryset = Notificacion.objects.filter(usuario=usuario)
        if solo_no_leidas:
            queryset = queryset.filter(leida=False)
        return queryset

    @staticmethod
    def contar_no_leidas(usuario):
        """Cuenta las notificaciones no leídas de un usuario."""
        return Notificacion.objects.filter(
            usuario=usuario,
            leida=False,
        ).count()

    @staticmethod
    def marcar_como_leida(notificacion_id):
        """Marca una notificación como leída."""
        Notificacion.objects.filter(pk=notificacion_id).update(leida=True)

    @staticmethod
    def marcar_todas_como_leidas(usuario):
        """Marca todas las notificaciones de un usuario como leídas."""
        Notificacion.objects.filter(
            usuario=usuario,
            leida=False,
        ).update(leida=True)
