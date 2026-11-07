"""
Servicios del módulo de notificaciones.

Contiene toda la lógica de negocio relacionada con la gestión de notificaciones.
"""
from django.core.cache import cache

from .models import Notificacion

_TTL_NO_LEIDAS = 60


def _clave_no_leidas(usuario):
    uid = getattr(usuario, 'id', usuario)
    return f"sigea:notif_noleidas:{uid}"


def _invalidar_no_leidas(usuario):
    cache.delete(_clave_no_leidas(usuario))


class NotificacionService:
    """Servicio para la gestión de notificaciones."""

    @staticmethod
    def crear_notificacion(usuario, mensaje, tipo='INFO', documento=None):
        """Crea una nueva notificación para un usuario."""
        notif = Notificacion.objects.create(
            usuario=usuario,
            mensaje=mensaje,
            tipo=tipo,
            documento=documento,
        )
        _invalidar_no_leidas(usuario)
        return notif

    @staticmethod
    def notificar_revisores(documento, mensaje, actor=None, incluir_decana=False,
                            extra=None, tipo='INFO'):
        """Notifica a los revisores de la facultad (A3).

        Regla facultad: la Coordinadora es única para todos los programas, así que
        NO se filtra por programa. Si no hay Coordinadora activa (o se pide
        explícitamente) se incluye a la Decana. Sin duplicados y sin el actor.
        """
        from apps.usuarios.models import Usuario

        activos = Usuario.objects.filter(is_active=True, esta_habilitado=True)
        destinatarios = list(activos.filter(rol='COORDINADOR'))
        if incluir_decana or not destinatarios:
            destinatarios += list(activos.filter(rol='DECANA'))
        destinatarios += [u for u in (extra or []) if u is not None]

        vistos = set()
        if actor is not None:
            vistos.add(actor.pk)
        enviados = []
        for usuario in destinatarios:
            if usuario.pk in vistos:
                continue
            vistos.add(usuario.pk)
            enviados.append(NotificacionService.crear_notificacion(
                usuario=usuario, mensaje=mensaje, tipo=tipo, documento=documento,
            ))
        return enviados

    @staticmethod
    def listar_notificaciones(usuario, solo_no_leidas=False):
        """Lista las notificaciones de un usuario."""
        queryset = Notificacion.objects.filter(usuario=usuario)
        if solo_no_leidas:
            queryset = queryset.filter(leida=False)
        return queryset

    @staticmethod
    def contar_no_leidas(usuario):
        """Cuenta las notificaciones no leídas (cache 60s por usuario)."""
        clave = _clave_no_leidas(usuario)
        total = cache.get(clave)
        if total is None:
            total = Notificacion.objects.filter(
                usuario=usuario,
                leida=False,
            ).count()
            cache.set(clave, total, _TTL_NO_LEIDAS)
        return total

    @staticmethod
    def marcar_como_leida(notificacion_id, usuario=None):
        """Marca una notificación como leída (solo la del propio usuario)."""
        qs = Notificacion.objects.filter(pk=notificacion_id)
        if usuario is not None and getattr(usuario, 'is_authenticated', False):
            qs = qs.filter(usuario=usuario)
        else:
            # Sin usuario no se marca nada: evita IDOR desde llamadas sin contexto
            return 0
        actualizadas = qs.update(leida=True)
        if actualizadas:
            _invalidar_no_leidas(usuario)
        return actualizadas

    @staticmethod
    def marcar_todas_como_leidas(usuario):
        """Marca todas las notificaciones de un usuario como leídas."""
        Notificacion.objects.filter(
            usuario=usuario,
            leida=False,
        ).update(leida=True)
        _invalidar_no_leidas(usuario)
