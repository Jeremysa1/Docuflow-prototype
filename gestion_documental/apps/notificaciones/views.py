"""
Vistas del módulo de notificaciones.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
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
    """Marca una notificación como leída."""
    if request.method == 'POST' or 'next' in request.GET:
        NotificacionService.marcar_como_leida(notificacion_id)
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)
    return redirect('notificaciones:lista')


@login_required
def marcar_todas_leidas(request):
    """Marca todas las notificaciones como leídas."""
    NotificacionService.marcar_todas_como_leidas(request.user)
    messages.success(request, 'Todas las notificaciones marcadas como leídas.')
    return redirect('notificaciones:lista')
