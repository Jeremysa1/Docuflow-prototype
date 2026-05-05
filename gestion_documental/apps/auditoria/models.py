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

    def __str__(self):
        return f"{self.usuario} - {self.get_accion_display()} - {self.fecha_hora}"
