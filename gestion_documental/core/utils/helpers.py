"""
Funciones auxiliares reutilizables.
"""
import os
from django.conf import settings
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme


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




def validar_archivo_subido(file, extensiones=None, max_size=None):
    """Valida extensión y tamaño de un archivo subido. Lanza ValidationError si falla."""
    if file is None:
        raise ValidationError('Elige un archivo.')
    extensiones = extensiones or settings.ALLOWED_DOCUMENT_EXTENSIONS
    max_size = max_size or settings.MAX_UPLOAD_SIZE
    ext = os.path.splitext(getattr(file, 'name', ''))[1].lower()
    if ext not in extensiones:
        raise ValidationError(
            f'Extensión no permitida ({ext or "sin extensión"}). Válidas: {", ".join(extensiones)}'
        )
    size = getattr(file, 'size', 0) or 0
    if size > max_size:
        raise ValidationError(f'El archivo excede el tamaño máximo de {max_size // (1024 * 1024)}MB.')
    if not contenido_coincide_con_extension(file, ext):
        raise ValidationError('El contenido del archivo no corresponde a su extensión. Sube el documento original.')
    return True


# Carpeta interna que identifica cada formato Office (OOXML es un ZIP).
_CARPETA_OOXML = {'.docx': 'word/', '.xlsx': 'xl/', '.pptx': 'ppt/'}


def contenido_coincide_con_extension(file, ext):
    """Revisa la firma real del archivo, no solo su nombre.

    PDF empieza por %PDF; docx, xlsx y pptx son ZIP con [Content_Types].xml y su carpeta.
    Deja el puntero del archivo al inicio para que se pueda guardar después.
    """
    import zipfile
    try:
        file.seek(0)
        cabecera = file.read(8)
        file.seek(0)
        if ext == '.pdf':
            return cabecera.startswith(b'%PDF')
        if ext in _CARPETA_OOXML:
            if not cabecera.startswith(b'PK\x03\x04'):
                return False
            with zipfile.ZipFile(file) as z:
                nombres = z.namelist()
            file.seek(0)
            return '[Content_Types].xml' in nombres and any(n.startswith(_CARPETA_OOXML[ext]) for n in nombres)
        return False
    except (zipfile.BadZipFile, OSError, ValueError):
        return False



def redirect_back_seguro(request, fallback='documentos:busqueda'):
    """R2-05: vuelve al Referer solo si es URL interna válida; si no, al fallback."""
    referer = request.META.get('HTTP_REFERER')
    if referer and url_has_allowed_host_and_scheme(
        referer, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(referer)
    return redirect(fallback)


def sanear_celda_excel(valor):
    """H1: neutraliza formula-injection (=,+,-,@ al inicio) prefijando apóstrofe."""
    texto = '' if valor is None else str(valor)
    if texto[:1] in ('=', '+', '-', '@'):
        return "'" + texto
    return texto


def nombre_archivo_seguro(filename):
    """H2: nombre para Content-Disposition sin comillas, CRLF ni separadores."""
    base = (filename or 'archivo').replace('\\', '/').split('/')[-1]
    base = ''.join(c for c in base if c not in '"\r\n;')
    return base[:150] or 'archivo'


def content_disposition_seguro(filename):
    """H2: attachment con filename ASCII saneado + filename* RFC5987."""
    import urllib.parse
    seguro = nombre_archivo_seguro(filename)
    ascii_name = seguro.encode('ascii', 'ignore').decode() or 'archivo'
    return f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{urllib.parse.quote(seguro)}'


def parse_fecha_segura(valor):
    """H6: parsea YYYY-MM-DD; devuelve date o None si es inválida (en vez de 500)."""
    from datetime import datetime
    if not valor or not isinstance(valor, str):
        return None
    try:
        return datetime.strptime(valor.strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def inicio_dia(fecha):
    """H-13: date -> datetime aware a las 00:00 en la zona del proyecto.

    Permite filtros `campo__gte / campo__lt` (usan índice) en vez de
    `campo__date__...` (aplica función sobre la columna y no lo usa).
    """
    from datetime import datetime
    from django.utils import timezone
    if fecha is None:
        return None
    if isinstance(fecha, datetime):
        fecha = fecha.date()
    return timezone.make_aware(datetime.combine(fecha, datetime.min.time()))


def throttle_fijo(clave, max_intentos, ventana_seg=60):
    """Ventana fija con la caché de Django (sin dependencias).

    Retorna True si se superó el límite (responder 429). El primer uso
    crea la ventana; `incr` no renueva el TTL (ventana realmente fija).
    """
    from django.core.cache import cache
    try:
        return cache.incr(clave) > max_intentos
    except ValueError:
        cache.set(clave, 1, timeout=ventana_seg)
        return False


class ReglaNegocioError(Exception):
    """Error de negocio cuyo mensaje SÍ se puede mostrar al usuario.

    Cualquier otra excepción se considera interna: se registra en el log y el
    usuario solo ve un mensaje genérico (FR-010).
    """


def enmascarar_email(email):
    """'yeremi@gmail.com' -> 'ye***@gmail.com'. Nunca devuelve el texto completo."""
    texto = (email or '').strip()
    if '@' not in texto:
        return '***'
    local, dominio = texto.rsplit('@', 1)
    visible = local[:2] if len(local) > 2 else local[:1]
    return f"{visible}***@{dominio}"


def _ip_valida(valor):
    import ipaddress
    try:
        return str(ipaddress.ip_address((valor or '').strip()))
    except ValueError:
        return None


def obtener_ip_cliente(request):
    """IP confiable del cliente (C3).

    - TRUSTED_PROXY_COUNT == 0 (por defecto): solo REMOTE_ADDR; X-Forwarded-For
      lo controla el cliente y se ignora.
    - TRUSTED_PROXY_COUNT == N: la entrada N-ésima desde la derecha de
      X-Forwarded-For (la que añadió el proxy más externo de confianza).
    Devuelve None si el valor no es una IP válida, para que nunca rompa la acción.
    """
    if request is None:
        return None
    remote = request.META.get('REMOTE_ADDR')
    proxies = getattr(settings, 'TRUSTED_PROXY_COUNT', 0) or 0
    if proxies > 0:
        cadena = [p.strip() for p in request.META.get('HTTP_X_FORWARDED_FOR', '').split(',') if p.strip()]
        if len(cadena) >= proxies:
            return _ip_valida(cadena[-proxies])
    return _ip_valida(remote)


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
