"""
Vistas del módulo de notificaciones.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.paginator import Paginator

from apps.notificaciones.services import NotificacionService


@login_required
def lista_notificaciones(request):
    """Lista las notificaciones del usuario actual."""
    notificaciones = NotificacionService.listar_notificaciones(request.user)
    paginator = Paginator(notificaciones, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'notificaciones/lista.html', {
        'page_obj': page_obj,
    })


@login_required
def marcar_leida(request, notificacion_id):
    """Marca una notificación como leída (POST) o navega a su documento (GET)."""
    from django.urls import reverse
    from apps.notificaciones.models import Notificacion

    next_url = request.GET.get('next')
    if request.method == 'POST':
        NotificacionService.marcar_como_leida(notificacion_id, request.user)
        if next_url:
            from django.utils.http import url_has_allowed_host_and_scheme
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                return redirect(next_url)
        return redirect('notificaciones:lista')

    # H4: por GET no hay cambio de estado, salvo navegar al propio documento:
    # se marca solo si `next` es exactamente el detalle del documento de ESTA notificación.
    try:
        notif = Notificacion.objects.get(pk=notificacion_id, usuario=request.user)
    except (Notificacion.DoesNotExist, ValueError):
        return redirect('notificaciones:lista')
    if notif.documento_id and next_url == reverse('documentos:detalle', args=[notif.documento_id]):
        NotificacionService.marcar_como_leida(notificacion_id, request.user)
        return redirect(next_url)
    return redirect('notificaciones:lista')


@login_required
@require_POST
def marcar_todas_leidas(request):
    """Marca todas las notificaciones como leídas (solo POST)."""
    NotificacionService.marcar_todas_como_leidas(request.user)
    messages.success(request, 'Todas las notificaciones marcadas como leídas.')
    return redirect('notificaciones:lista')
