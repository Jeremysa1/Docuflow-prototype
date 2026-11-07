"""
Modelos del módulo de notificaciones.

Define las notificaciones/alertas del sistema para los usuarios.
"""
from django.db import models
from django.conf import settings

from apps.documentos.models import Documento


class Notificacion(models.Model):
    """Notificación o alerta del sistema."""

    class Tipo(models.TextChoices):
        INFO = 'INFO', 'Información'
        APROBADO = 'APROBADO', 'Aprobado'
        RECHAZADO = 'RECHAZADO', 'Rechazado'
        ACTUALIZADO = 'ACTUALIZADO', 'Actualizado'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name='Usuario'
    )
    mensaje = models.TextField(verbose_name='Mensaje')
    tipo = models.CharField(
        max_length=20,
        choices=Tipo.choices,
        default=Tipo.INFO,
        verbose_name='Tipo'
    )
    leida = models.BooleanField(default=False, verbose_name='Leída')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    documento = models.ForeignKey(
        Documento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notificaciones',
        verbose_name='Documento'
    )

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(
                fields=['usuario', 'leida', '-fecha_creacion'],
                name='notif_usr_leida_idx',
            ),
        ]

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.mensaje[:50]}"
