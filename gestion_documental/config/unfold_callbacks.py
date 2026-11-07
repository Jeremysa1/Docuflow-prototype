"""Callbacks de personalización de django-unfold (admin premium SIGEA).

Se referencian por ruta punteada desde el dict UNFOLD en settings.py.
"""
from django.conf import settings


def environment(request):
    """Etiqueta de entorno en la esquina superior del admin."""
    if settings.DEBUG:
        return ["Desarrollo", "info"]
    return ["Producción", "danger"]
