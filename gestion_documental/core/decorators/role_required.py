"""
Decoradores de permisos y roles.

Proporcionan control de acceso basado en roles y permisos sobre documentos.
"""
from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404

from apps.permisos.models import PermisoDocumento
from apps.documentos.models import Documento


def role_required(*roles):
    """
    Decorador que verifica que el usuario autenticado tenga uno de los roles permitidos.

    Uso:
        @role_required('DECANA', 'COORDINADOR')
        def mi_vista(request):
            ...

    Retorna 403 si el usuario no tiene ninguno de los roles especificados.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden('Acceso denegado. Debe iniciar sesión.')

            if request.user.rol not in roles:
                return HttpResponseForbidden(
                    'Acceso denegado. No tiene los permisos necesarios para acceder a este recurso.'
                )

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def document_permission_required(permission_type='ver'):
    """
    Decorador que verifica permisos específicos del usuario sobre un documento.

    La vista debe recibir 'documento_id' como parámetro.

    Args:
        permission_type: Tipo de permiso requerido ('ver' o 'descargar')

    Retorna 403 si el usuario no tiene el permiso requerido.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            documento_id = kwargs.get('documento_id')
            if not documento_id:
                return HttpResponseForbidden('Documento no especificado.')

            documento = get_object_or_404(Documento, pk=documento_id)

            # El autor siempre tiene permisos completos
            if documento.autor == request.user:
                return view_func(request, *args, **kwargs)

            # Roles administrativos tienen acceso completo
            if request.user.rol in ('DECANA', 'COORDINADOR'):
                return view_func(request, *args, **kwargs)

            # Verificar permisos específicos
            try:
                permiso = PermisoDocumento.objects.get(
                    usuario=request.user,
                    documento=documento,
                )
                if permission_type == 'ver' and permiso.puede_ver:
                    return view_func(request, *args, **kwargs)
                elif permission_type == 'descargar' and permiso.puede_descargar:
                    return view_func(request, *args, **kwargs)
            except PermisoDocumento.DoesNotExist:
                pass

            # Si el documento es compartido, permitir ver
            if permission_type == 'ver' and documento.es_compartido:
                return view_func(request, *args, **kwargs)

            return HttpResponseForbidden(
                'Acceso denegado. No tiene permisos para realizar esta acción sobre el documento.'
            )
        return _wrapped_view
    return decorator
