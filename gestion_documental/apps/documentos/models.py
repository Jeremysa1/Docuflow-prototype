"""
Modelos del módulo de documentos.

Define el modelo Documento y el catálogo de Categorías.
"""
from django.db import models
from django.conf import settings

from ..usuarios.models import ProgramaAcademico


class Categoria(models.Model):
    """Catálogo de categorías de documentos."""

    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Documento(models.Model):
    """Modelo principal de documento."""

    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        APROBADO = 'APROBADO', 'Aprobado'
        RECHAZADO = 'RECHAZADO', 'Rechazado'

    FACTORES_CNA = [
        ('F1', 'Factor 1: Proyecto Educativo del Programa e Identidad Institucional.'),
        ('F2', 'Factor 2: Estudiantes.'),
        ('F3', 'Factor 3: Profesores.'),
        ('F4', 'Factor 4: Egresados.'),
        ('F5', 'Factor 5: Aspectos Académicos y Resultados de Aprendizaje.'),
        ('F6', 'Factor 6: Permanencia y Graduación.'),
        ('F7', 'Factor 7: Interacción con el Entorno Nacional e Internacional.'),
        ('F8', 'Factor 8: Aportes de la Investigación, la Innovación, el Desarrollo Tecnológico y la Creación.'),
        ('F9', 'Factor 9: Bienestar de la Comunidad Académica.'),
        ('F10', 'Factor 10: Medios Educativos y Ambientes de Aprendizaje.'),
        ('F11', 'Factor 11: Organización, Administración y Financiación del Programa Académico.'),
        ('F12', 'Factor 12: Recursos Físicos y Tecnológicos.'),
    ]

    VISIBILIDAD_CHOICES = [
        ('PROGRAMA', 'Por programa'),
        ('INSTITUCIONAL', 'Institucional'),
    ]

    titulo = models.CharField(max_length=255, verbose_name='Título')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    archivo = models.FileField(upload_to='docs/', max_length=500, verbose_name='Archivo')
    programa = models.ForeignKey(
        ProgramaAcademico,
        on_delete=models.CASCADE,
        related_name='documentos',
        verbose_name='Programa Académico'
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name='documentos',
        verbose_name='Categoría'
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documentos',
        verbose_name='Autor'
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        verbose_name='Estado'
    )
    # DEPRECADO — reemplazado por visibilidad
    es_compartido = models.BooleanField(default=False, verbose_name='Es compartido')
    es_sensible = models.BooleanField(default=False, verbose_name='Es sensible')
    
    factor_cna = models.CharField(
        max_length=3,
        choices=FACTORES_CNA,
        null=True,
        blank=True,
        verbose_name='Factor CNA'
    )
    fecha_vigencia = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de vigencia'
    )
    visibilidad = models.CharField(
        max_length=15,
        choices=VISIBILIDAD_CHOICES,
        default='PROGRAMA',
        verbose_name='Visibilidad'
    )
    comentario_rechazo = models.TextField(blank=True, null=True, verbose_name='Motivo de rechazo')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name='Fecha de modificación')

    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.titulo} ({self.get_estado_display()})"
