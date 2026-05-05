"""
Funciones auxiliares reutilizables.
"""
import os
from django.conf import settings


def validar_extension_archivo(filename):
    """
    Valida que la extensión del archivo esté permitida.

    Args:
        filename: Nombre del archivo

    Returns:
        bool: True si la extensión está permitida
    """
    ext = os.path.splitext(filename)[1].lower()
    return ext in settings.ALLOWED_DOCUMENT_EXTENSIONS


def validar_tamano_archivo(file):
    """
    Valida que el tamaño del archivo no exceda el máximo permitido.

    Args:
        file: Archivo subido

    Returns:
        bool: True si el tamaño es válido
    """
    return file.size <= settings.MAX_UPLOAD_SIZE


def obtener_ip_cliente(request):
    """
    Obtiene la dirección IP del cliente desde el request HTTP.

    Args:
        request: HttpRequest de Django

    Returns:
        str: Dirección IP del cliente
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def formato_tamano_archivo(size_bytes):
    """
    Convierte bytes a formato legible (KB, MB, GB).

    Args:
        size_bytes: Tamaño en bytes

    Returns:
        str: Tamaño formateado
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
