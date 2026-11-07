"""
Modelos del módulo de auditoría.

Define el registro de actividades para trazabilidad del sistema.
"""
from django.db import models
from django.conf import settings

from ..documentos.models import Documento


class RegistroAuditoria(models.Model):
    """Registro de auditoría de actividades del sistema."""

    class Accion(models.TextChoices):
        SUBIO = 'SUBIO', 'Subió documento'
        MODIFICO = 'MODIFICO', 'Modificó documento'
        DESCARGO = 'DESCARGO', 'Descargó documento'
        ELIMINO = 'ELIMINO', 'Eliminó documento'
        APROBO = 'APROBO', 'Aprobó documento'
        RECHAZO = 'RECHAZO', 'Rechazó documento'
        EDITO_METADATOS = 'EDITO_METADATOS', 'Editó metadatos'
        ACTUALIZO = 'ACTUALIZO', 'Restauró documento'
        NUEVA_VERSION = 'NUEVA_VERSION', 'Subió nueva versión'
        VISUALIZO = 'VISUALIZO', 'Visualizó documento'
        ACCESO_DENEGADO = 'ACCESO_DENEGADO', 'Acceso denegado'
        # Sesión
        LOGIN = 'LOGIN', 'Inició sesión'
        LOGIN_FALLIDO = 'LOGIN_FALLIDO', 'Intento de sesión fallido'
        LOGOUT = 'LOGOUT', 'Cerró sesión'
        # Accesos Zero-Trust
        SOLICITO_ACCESO = 'SOLICITO_ACCESO', 'Solicitó acceso'
        VOTO_ACCESO = 'VOTO_ACCESO', 'Votó acceso sensible'
        APROBO_ACCESO = 'APROBO_ACCESO', 'Aprobó acceso'
        RECHAZO_ACCESO = 'RECHAZO_ACCESO', 'Rechazó acceso'
        REVOCO_ACCESO = 'REVOCO_ACCESO', 'Revocó acceso'
        # Gestión de usuarios
        CREO_USUARIO = 'CREO_USUARIO', 'Creó usuario'
        HABILITO_USUARIO = 'HABILITO_USUARIO', 'Habilitó usuario'
        DESHABILITO_USUARIO = 'DESHABILITO_USUARIO', 'Deshabilitó usuario'
        ELIMINO_USUARIO = 'ELIMINO_USUARIO', 'Eliminó usuario'
        ACTUALIZO_USUARIO = 'ACTUALIZO_USUARIO', 'Cambió rol o programa'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registros_auditoria',
        verbose_name='Usuario'
    )
    accion = models.CharField(
        max_length=20,
        choices=Accion.choices,
        verbose_name='Acción'
    )
    documento = models.ForeignKey(
        Documento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registros_auditoria',
        verbose_name='Documento'
    )
    fecha_hora = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y hora')
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Dirección IP'
    )
    detalle = models.TextField(blank=True, verbose_name='Detalle')

    class Meta:
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'
        ordering = ['-fecha_hora']
        indexes = [
            models.Index(fields=['accion', '-fecha_hora'], name='audit_accion_fh_idx'),
        ]

    def __str__(self):
        return f"{self.usuario} - {self.get_accion_display()} - {self.fecha_hora}"
