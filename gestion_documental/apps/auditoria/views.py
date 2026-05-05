"""
Vistas del módulo de auditoría.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from apps.auditoria.services import AuditoriaService
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
    
    # Estadísticas para el sidebar (optimizadas)
    total_registros = registros.count()
    if total_registros > 0:
        subidas = registros.filter(accion='SUBIO').count()
        aprobaciones = registros.filter(accion='APROBO').count()
        eliminaciones = registros.filter(accion='ELIMINO').count()
        
        stats = {
            'total': total_registros,
            'subidas_pct': int((subidas / total_registros) * 100),
            'aprobaciones_pct': int((aprobaciones / total_registros) * 100),
            'eliminaciones_pct': int((eliminaciones / total_registros) * 100),
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

    return render(request, 'auditoria/lista.html', {
        'page_obj': page_obj,
        'stats': stats,
    })

import csv
from django.http import HttpResponse

@login_required
@role_required('DECANA', 'COORDINADOR')
def exportar_auditoria(request):
    """Exporta los registros de auditoría filtrados a CSV."""
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

    response = HttpResponse(
        content_type='text/csv',
    )
    response['Content-Disposition'] = 'attachment; filename="auditoria_docuflow.csv"'
    # Añadir BOM para que Excel lea correctamente el UTF-8 con caracteres especiales
    response.write('\ufeff'.encode('utf8'))

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Fecha', 'Hora', 'Usuario (Email)', 'Nombre', 'Programa Académico', 'Acción', 'Documento/Descripción', 'Dirección IP'])

    for reg in registros:
        fecha = reg.fecha_hora.astimezone().strftime('%d/%m/%Y')
        hora = reg.fecha_hora.astimezone().strftime('%H:%M:%S')
        email = reg.usuario.email if reg.usuario else 'Sistema'
        nombre = reg.usuario.get_full_name() if reg.usuario else '-'
        programa = reg.usuario.programa_academico.nombre if reg.usuario and hasattr(reg.usuario, 'programa_academico') and reg.usuario.programa_academico else '-'
        accion = reg.get_accion_display()
        
        # Documento o Detalle
        if reg.documento:
            doc_desc = f"{reg.documento.titulo} (ID: {reg.documento.id})"
        else:
            doc_desc = reg.detalle or '-'
            
        ip = reg.ip_address or '-'

        writer.writerow([fecha, hora, email, nombre, programa, accion, doc_desc, ip])

    return response
