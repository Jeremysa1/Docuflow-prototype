"""
Template tags del sistema de diseño SIGEA (contracts/componentes.md).

    {% load sigea %}
    {% icono "search" %}                       → icono decorativo
    {% icono "trash-2" etiqueta="Eliminar" %}  → icono con nombre accesible
    {% chip_factor celda %}                    → chip "F3 · 4 / 20" en su gradación
    {% chip_factor_codigo doc.factor_cna %}    → chip con el avance actual de la facultad
    {% estado_documento doc %}                 → estado con forma + color
    {% tipo_archivo doc %}                     → icono del tipo de archivo (PDF, Word, Excel, PowerPoint)
    {{ n|plural:"evidencia,evidencias" }}
    {{ usuario|iniciales }}
"""
from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils import timezone

register = template.Library()

_ICONOS_CONOCIDOS = None


def _iconos_conocidos():
    global _ICONOS_CONOCIDOS
    if _ICONOS_CONOCIDOS is None:
        import re
        from django.contrib.staticfiles import finders
        ruta = finders.find('icons/lucide.svg')
        texto = open(ruta, encoding='utf-8').read() if ruta else ''
        _ICONOS_CONOCIDOS = set(re.findall(r'<symbol id="([^"]+)"', texto))
    return _ICONOS_CONOCIDOS


@register.simple_tag
def icono(nombre, clase='', etiqueta=''):
    if settings.DEBUG and nombre not in _iconos_conocidos():
        raise template.TemplateSyntaxError(f'Icono desconocido en el sprite: {nombre}')
    # ?v= obliga al navegador a recargar el sprite cuando se le agregan iconos
    href = f"{static('icons/lucide.svg')}?v=2#{nombre}"
    clases = f'sg-icono {clase}'.strip()
    if etiqueta:
        return format_html('<svg class="{}" role="img" aria-label="{}"><use href="{}"></use></svg>',
                           clases, etiqueta, href)
    return format_html('<svg class="{}" aria-hidden="true" focusable="false"><use href="{}"></use></svg>',
                       clases, href)


@register.filter
def plural(n, formas):
    singular, _, plural_ = formas.partition(',')
    try:
        n = int(n)
    except (TypeError, ValueError):
        n = 0
    return f'{n} {singular if n == 1 else plural_}'


@register.filter
def iniciales(usuario):
    if usuario is None:
        return '?'
    nombre = (getattr(usuario, 'first_name', '') or '').strip()
    apellido = (getattr(usuario, 'last_name', '') or '').strip()
    letras = (nombre[:1] + apellido[:1]).upper()
    if not letras:
        base = (getattr(usuario, 'email', '') or getattr(usuario, 'username', '') or '').strip()
        letras = base[:1].upper()
    return letras or '?'


@register.inclusion_tag('componentes/chip_factor.html')
def chip_factor(celda, enlace=None, compacto=False):
    return {'celda': celda, 'enlace': enlace, 'compacto': compacto}


@register.inclusion_tag('componentes/chip_factor.html', takes_context=True)
def chip_factor_codigo(context, codigo, enlace=None):
    """Chip de un factor con el avance actual de la facultad (o vacío si no tiene factor).

    Zero-Trust: el avance de la facultad es solo para directivas. Para el docente el
    chip muestra el código del factor, sin cifra ni gradación.
    """
    if not codigo:
        return {'celda': None}
    usuario = context.get('user') or getattr(context.get('request'), 'user', None)
    if getattr(usuario, 'rol', None) not in ('DECANA', 'COORDINADOR'):
        from apps.documentos.metricas import NOMBRES_FACTOR
        return {'codigo_solo': codigo, 'nombre': NOMBRES_FACTOR.get(codigo, codigo), 'enlace': enlace}
    from apps.documentos.metricas import MetricasService
    celdas = {c.codigo: c for c in MetricasService.huella_facultad()['celdas']}
    return {'celda': celdas.get(codigo), 'enlace': enlace, 'compacto': False}


@register.inclusion_tag('componentes/estado_documento.html')
def estado_documento(doc, mostrar_sensible=True):
    estado = getattr(doc, 'estado', '')
    envejecido = False
    if estado == 'PENDIENTE' and getattr(doc, 'fecha_modificacion', None):
        envejecido = (timezone.now() - doc.fecha_modificacion).days > 3
    return {
        'estado': estado,
        'etiqueta': {'APROBADO': 'Aprobado', 'PENDIENTE': 'En revisión', 'RECHAZADO': 'Rechazado'}.get(estado, estado.title()),
        'envejecido': envejecido,
        'sensible': mostrar_sensible and getattr(doc, 'es_sensible', False),
    }


@register.filter
def dias(fecha):
    """Antigüedad siempre en días: 'Hoy', '1 día', '63 días'."""
    if not fecha:
        return ''
    n = (timezone.now() - fecha).days
    return 'Hoy' if n <= 0 else ('1 día' if n == 1 else f'{n} días')


_TIPOS = {
    '.pdf': ('pdf', 'PDF', 'Documento PDF'),
    '.doc': ('word', 'DOC', 'Documento de Word'),
    '.docx': ('word', 'DOC', 'Documento de Word'),
    '.xls': ('excel', 'XLS', 'Hoja de cálculo de Excel'),
    '.xlsx': ('excel', 'XLS', 'Hoja de cálculo de Excel'),
    '.ppt': ('ppt', 'PPT', 'Presentación de PowerPoint'),
    '.pptx': ('ppt', 'PPT', 'Presentación de PowerPoint'),
}


def datos_tipo_archivo(origen):
    """(clase, sigla, nombre) del tipo de archivo de un documento, un FieldFile o un nombre."""
    import os
    archivo = getattr(origen, 'archivo', origen)
    nombre = getattr(archivo, 'name', archivo) or ''
    ext = os.path.splitext(str(nombre))[1].lower()
    return _TIPOS.get(ext, ('otro', ext[1:4].upper() or 'ARC', 'Archivo'))


@register.inclusion_tag('componentes/tipo_archivo.html')
def tipo_archivo(origen, grande=False):
    clase, sigla, nombre = datos_tipo_archivo(origen)
    return {'clase': clase, 'sigla': sigla, 'nombre': nombre, 'grande': grande}


@register.filter
def gradacion_clase(celda):
    return f'sg-grad-{getattr(getattr(celda, "gradacion", None), "nivel", 0)}'
