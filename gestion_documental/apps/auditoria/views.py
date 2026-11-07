"""
Vistas del módulo de auditoría.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.contrib import messages

import logging

from apps.auditoria.services import AuditoriaService

logger = logging.getLogger(__name__)
from core.decorators.role_required import role_required


@login_required
@role_required('DECANA', 'COORDINADOR')
def lista_auditoria(request):
    """Vista del log de auditoría (solo para roles administrativos)."""
    usuario_filtro = request.GET.get('usuario')
    accion_filtro = request.GET.get('accion')
    documento_filtro = request.GET.get('documento')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    registros = AuditoriaService.listar_registros(
        usuario=usuario_filtro,
        accion=accion_filtro,
        documento=documento_filtro,
        fecha_inicio=fecha_inicio if fecha_inicio else None,
        fecha_fin=fecha_fin if fecha_fin else None,
    )
    
    # Estadísticas para el sidebar: un solo agregado en vez de 4 consultas.
    conteo = registros.aggregate(
        total=Count('id'),
        subidas=Count('id', filter=Q(accion='SUBIO')),
        aprobaciones=Count('id', filter=Q(accion='APROBO')),
        eliminaciones=Count('id', filter=Q(accion='ELIMINO')),
    )
    total_registros = conteo['total']
    if total_registros > 0:
        stats = {
            'total': total_registros,
            'subidas_pct': int((conteo['subidas'] / total_registros) * 100),
            'aprobaciones_pct': int((conteo['aprobaciones'] / total_registros) * 100),
            'eliminaciones_pct': int((conteo['eliminaciones'] / total_registros) * 100),
        }
    else:
        stats = {
            'total': 0,
            'subidas_pct': 0,
            'aprobaciones_pct': 0,
            'eliminaciones_pct': 0,
        }
    
    paginator = Paginator(registros, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    from apps.auditoria.models import RegistroAuditoria

    return render(request, 'auditoria/lista.html', {
        'page_obj': page_obj,
        'stats': stats,
        'acciones': RegistroAuditoria.Accion.choices,
    })

import csv
from django.http import HttpResponse

@login_required
@role_required('DECANA', 'COORDINADOR')
def exportar_auditoria_excel(request):
    """Exporta los registros de auditoria filtrados a Excel."""
    usuario_filtro = request.GET.get('usuario')
    accion_filtro = request.GET.get('accion')
    documento_filtro = request.GET.get('documento')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    try:
        registros = AuditoriaService.listar_registros(
            usuario=usuario_filtro,
            accion=accion_filtro,
            documento=documento_filtro,
            fecha_inicio=fecha_inicio if fecha_inicio else None,
            fecha_fin=fecha_fin if fecha_fin else None,
        )

        excel_data = AuditoriaService.generar_auditoria_excel(registros)
        response = HttpResponse(excel_data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="auditoria_SIGEA.xlsx"'
        return response
    except Exception:
        logger.exception('Error al exportar la auditoría a Excel')
        messages.error(request, 'No se pudo generar el archivo Excel. Inténtalo de nuevo.')
        return redirect('auditoria:lista')

@login_required
@role_required('DECANA', 'COORDINADOR')
def exportar_auditoria_pdf(request):
    """Exporta los registros de auditoria filtrados a PDF."""
    usuario_filtro = request.GET.get('usuario')
    accion_filtro = request.GET.get('accion')
    documento_filtro = request.GET.get('documento')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    try:
        registros = AuditoriaService.listar_registros(
            usuario=usuario_filtro,
            accion=accion_filtro,
            documento=documento_filtro,
            fecha_inicio=fecha_inicio if fecha_inicio else None,
            fecha_fin=fecha_fin if fecha_fin else None,
        )

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="auditoria_SIGEA.pdf"'
        AuditoriaService.generar_auditoria_pdf(response, registros)
        return response
    except Exception:
        logger.exception('Error al exportar la auditoría a PDF')
        messages.error(request, 'No se pudo generar el archivo PDF. Inténtalo de nuevo.')
        return redirect('auditoria:lista')


