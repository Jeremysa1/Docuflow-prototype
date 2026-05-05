"""
Vistas del módulo de versiones.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from apps.versiones.services import VersionService
from apps.documentos.models import Documento


@login_required
def lista_versiones(request, documento_id):
    """Lista las versiones de un documento."""
    documento = get_object_or_404(Documento, pk=documento_id)
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
    if request.method == 'POST':
        archivo = request.FILES.get('archivo')
        descripcion = request.POST.get('descripcion_cambio', '')
        if archivo:
            version = VersionService.crear_version(
                documento_id=documento_id,
                archivo=archivo,
                descripcion_cambio=descripcion,
                autor=request.user,
            )
            messages.success(request, f'Versión {version.numero_version} creada exitosamente.')
            return redirect('versiones:lista', documento_id=documento_id)
        else:
            messages.error(request, 'Debe seleccionar un archivo.')

    return render(request, 'versiones/crear.html', {
        'documento': documento,
        'documento_id': documento_id
    })

@login_required
def restaurar_version_view(request, version_id):
    """Restaura una versión de un documento."""
    if request.method == 'POST':
        try:
            version = VersionService.obtener_version(version_id)
            if not version:
                raise Exception("La versión no existe.")
            
            doc = version.documento
            if request.user != doc.autor and request.user.rol not in ('COORDINADOR', 'DECANA'):
                raise PermissionError("No tienes permiso para restaurar esta versión.")
            
            nueva_version = VersionService.restaurar_version(version_id, request.user)
            messages.success(request, f'Versión {version.numero_version} restaurada como versión {nueva_version.numero_version}.')
            return redirect('documentos:detalle', documento_id=doc.id)
        except Exception as e:
            messages.error(request, str(e))
            
    return redirect(request.META.get('HTTP_REFERER', 'documentos:busqueda'))
