"""
Context processor para notificaciones.

Inyecta el conteo de notificaciones no leídas en todos los templates.
"""
from .services import NotificacionService


def notificaciones_no_leidas(request):
    """Agrega el conteo de notificaciones no leídas al contexto global."""
    if request.user.is_authenticated:
        return {
            'notificaciones_no_leidas_count': NotificacionService.contar_no_leidas(request.user),
        }
    return {'notificaciones_no_leidas_count': 0}
