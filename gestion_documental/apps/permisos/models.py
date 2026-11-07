"""
Modelos del módulo de permisos.

Define los permisos granulares por usuario y documento,
las solicitudes de acceso y los votos para documentos sensibles.
"""
from django.db import models
from django.conf import settings

from ..documentos.models import Documento


class PermisoDocumento(models.Model):
    """Permisos específicos de un usuario sobre un documento."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='permisos_documento',
        verbose_name='Usuario'
    )
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='permisos',
        verbose_name='Documento'
    )
    puede_ver = models.BooleanField(default=True, verbose_name='Puede ver')
    puede_descargar = models.BooleanField(default=True, verbose_name='Puede descargar')
    otorgado_en = models.DateTimeField(auto_now_add=True, verbose_name='Otorgado en')
    otorgado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='permisos_otorgados',
        verbose_name='Otorgado por'
    )

    class Meta:
        verbose_name = 'Permiso de Documento'
        verbose_name_plural = 'Permisos de Documentos'
        unique_together = ['usuario', 'documento']

    def __str__(self):
        return f"{self.usuario} → {self.documento} (ver: {self.puede_ver}, descargar: {self.puede_descargar})"


class SolicitudAcceso(models.Model):
    """Solicitud de acceso a un documento."""

    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
    ]

    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='solicitudes_enviadas',
        verbose_name='Solicitante'
    )
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='solicitudes_acceso',
        verbose_name='Documento'
    )
    motivo = models.TextField(verbose_name='Motivo de la solicitud')
    estado = models.CharField(
        max_length=10,
        choices=ESTADOS,
        default='PENDIENTE',
        verbose_name='Estado'
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de solicitud')
    fecha_respuesta = models.DateTimeField(
        null=True, blank=True, verbose_name='Fecha de respuesta'
    )
    respondido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='solicitudes_respondidas',
        verbose_name='Respondido por'
    )
    motivo_rechazo = models.TextField(
        null=True, blank=True,
        verbose_name='Motivo del rechazo'
    )

    class Meta:
        # Un usuario solo puede tener una solicitud activa por documento
        unique_together = ['solicitante', 'documento']
        ordering = ['-fecha_solicitud']
        indexes = [
            models.Index(fields=['estado', '-fecha_solicitud'], name='sol_estado_fsol_idx'),
        ]

    def __str__(self):
        return f"{self.solicitante} → {self.documento}"


class VotoAccesoSensible(models.Model):
    """Voto individual para aprobar/rechazar acceso a documentos sensibles."""

    VOTOS = [
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
    ]

    solicitud = models.ForeignKey(
        SolicitudAcceso,
        on_delete=models.CASCADE,
        related_name='votos',
        verbose_name='Solicitud'
    )
    votante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='votos_acceso',
        verbose_name='Votante'
    )
    voto = models.CharField(
        max_length=10,
        choices=VOTOS,
        verbose_name='Voto'
    )
    motivo_rechazo = models.TextField(
        null=True, blank=True,
        verbose_name='Motivo del rechazo'
    )
    fecha_voto = models.DateTimeField(auto_now_add=True, verbose_name='Fecha del voto')

    class Meta:
        # Cada votante solo puede votar una vez por solicitud
        unique_together = ['solicitud', 'votante']
        verbose_name = 'Voto de Acceso Sensible'
        verbose_name_plural = 'Votos de Acceso Sensible'

    def __str__(self):
        return f"{self.votante} → {self.get_voto_display()} ({self.solicitud})"
