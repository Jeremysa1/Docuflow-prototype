"""
Modelos del módulo de versiones.

Define el historial de versiones de un documento.
"""
from django.db import models
from django.conf import settings

from ..documentos.models import Documento


class Version(models.Model):
    """Historial de versiones de un documento."""

    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='versiones',
        verbose_name='Documento'
    )
    archivo = models.FileField(upload_to='docs/versiones/', verbose_name='Archivo de versión')
    numero_version = models.PositiveIntegerField(verbose_name='Número de versión')
    descripcion_cambio = models.TextField(blank=True, verbose_name='Descripción del cambio')
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='versiones',
        verbose_name='Autor'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')

    class Meta:
        verbose_name = 'Versión'
        verbose_name_plural = 'Versiones'
        ordering = ['-numero_version']
        unique_together = ['documento', 'numero_version']

    def __str__(self):
        return f"{self.documento.titulo} - v{self.numero_version}"
