"""
Modelos del módulo de usuarios.

Define el modelo de usuario personalizado con roles y programa académico,
así como el catálogo de programas académicos.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class ProgramaAcademico(models.Model):
    """Catálogo de programas académicos de la facultad."""

    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=20, unique=True)

    class Meta:
        verbose_name = 'Programa Académico'
        verbose_name_plural = 'Programas Académicos'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado que extiende AbstractUser.
    Agrega campos de rol, programa académico, habilitación y seguridad.
    """

    class Rol(models.TextChoices):
        DECANA = 'DECANA', 'Decana'
        COORDINADOR = 'COORDINADOR', 'Coordinador'
        DOCENTE_PLANTA = 'DOCENTE_PLANTA', 'Docente de Planta'

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.DOCENTE_PLANTA,
        verbose_name='Rol'
    )
    programa_academico = models.ForeignKey(
        ProgramaAcademico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios',
        verbose_name='Programa Académico'
    )

    # Habilitación (Docentes se crean inhabilitados hasta que la Decana los active)
    esta_habilitado = models.BooleanField(
        default=False,
        verbose_name='Está habilitado'
    )

    # Seguridad: bloqueo por intentos fallidos
    intentos_fallidos = models.IntegerField(default=0, verbose_name='Intentos fallidos')
    bloqueado_hasta = models.DateTimeField(
        null=True, blank=True, verbose_name='Bloqueado hasta'
    )

    # Recuperación de contraseña
    token_recuperacion = models.CharField(
        max_length=6, null=True, blank=True, verbose_name='Token de recuperación'
    )
    token_expiracion = models.DateTimeField(
        null=True, blank=True, verbose_name='Expiración del token'
    )
    token_intentos = models.IntegerField(default=0, verbose_name='Intentos de token')

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['rol'], name='usr_rol_idx'),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_rol_display()})"

    def get_full_name(self):
        """Retorna el nombre completo del usuario."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username

    @property
    def iniciales(self):
        """Retorna las iniciales del usuario para el avatar."""
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        return self.username[:2].upper()
