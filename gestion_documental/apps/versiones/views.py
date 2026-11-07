"""
Vistas del módulo de versiones.
"""
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from apps.versiones.services import VersionService
from apps.documentos.models import Documento
from apps.permisos.services import PermisoService
from core.services.audit_service import AuditService
from core.utils.helpers import ReglaNegocioError, validar_archivo_subido
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)
MSG_ERROR_GENERICO = 'No se pudo completar la acción. Inténtalo de nuevo o contacta a soporte.'


def _denegar(request, documento, detalle, mensaje):
    """A6: registra el intento y responde 403."""
    AuditService.log(usuario=request.user, accion='ACCESO_DENEGADO',
                     documento=documento, request=request, detalle=detalle)
    raise PermissionDenied(mensaje)


def _puede_versionar(usuario, documento):
    return usuario == documento.autor or usuario.rol in ('COORDINADOR', 'DECANA')


@login_required
def lista_versiones(request, documento_id):
    """Lista las versiones de un documento."""
    documento = get_object_or_404(Documento, pk=documento_id)
    if not PermisoService.usuario_tiene_acceso(request.user, documento):
        return _denegar(request, documento, 'Intento de ver el historial de versiones sin permiso',
                        'No tienes permiso para ver las versiones de este documento.')
    versiones = VersionService.listar_versiones(documento_id)
    return render(request, 'versiones/lista.html', {
        'documento': documento,
        'versiones': versiones,
        'documento_id': documento_id,
    })


@login_required
def crear_version(request, documento_id):
    """Crea una nueva versión de un documento."""
    documento = get_object_or_404(Documento, pk=documento_id)
    # Solo autor o directivos de facultad pueden versionar (1 Decana + 1 Coordinadora facultad)
    if not PermisoService.usuario_tiene_acceso(request.user, documento) or not _puede_versionar(request.user, documento):
        return _denegar(request, documento, 'Intento de crear una versión sin permiso',
                        'Solo el autor o un directivo pueden crear versiones.')

    contexto = {'documento': documento, 'documento_id': documento_id}
    if request.method == 'POST':
        archivo = request.FILES.get('archivo')
        descripcion = request.POST.get('descripcion_cambio', '')
        try:
            validar_archivo_subido(archivo)
            version = VersionService.crear_version(
                documento_id=documento_id,
                archivo=archivo,
                descripcion_cambio=descripcion,
                autor=request.user,
                request=request,
            )
        except ValidationError as e:
            messages.error(request, ' '.join(e.messages))
            return render(request, 'versiones/crear.html', contexto)
        except Exception:
            logger.exception('Error al crear versión del documento %s', documento_id)
            messages.error(request, MSG_ERROR_GENERICO)
            return render(request, 'versiones/crear.html', contexto)

        mensaje = f'Versión {version.numero_version} creada exitosamente.'
        if version.documento.estado == 'PENDIENTE' and request.user.rol == 'DOCENTE_PLANTA':
            mensaje += ' El documento volvió a revisión.'
        messages.success(request, mensaje)
        return redirect('versiones:lista', documento_id=documento_id)

    return render(request, 'versiones/crear.html', contexto)


@login_required
def restaurar_version_view(request, version_id):
    """Restaura una versión de un documento."""
    if request.method == 'POST':
        version = VersionService.obtener_version(version_id)
        if not version:
            messages.error(request, 'La versión no existe.')
        else:
            doc = version.documento
            if not PermisoService.usuario_tiene_acceso(request.user, doc) or not _puede_versionar(request.user, doc):
                AuditService.log(usuario=request.user, accion='ACCESO_DENEGADO', documento=doc,
                                 request=request, detalle=f'Intento de restaurar la versión {version.numero_version} sin permiso')
                messages.error(request, 'No tienes permiso para restaurar esta versión.')
            else:
                try:
                    nueva_version = VersionService.restaurar_version(version_id, request.user, request=request)
                    messages.success(request, f'Versión {version.numero_version} restaurada como versión {nueva_version.numero_version}.')
                    return redirect('documentos:detalle', documento_id=doc.id)
                except ReglaNegocioError as e:
                    messages.error(request, str(e))
                except Exception:
                    logger.exception('Error al restaurar la versión %s', version_id)
                    messages.error(request, MSG_ERROR_GENERICO)

    from core.utils.helpers import redirect_back_seguro
    return redirect_back_seguro(request, 'documentos:busqueda')
