"""
Vistas del módulo de documentos.

Las vistas reciben la petición HTTP, validan formularios y delegan
la lógica de negocio al servicio correspondiente.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import DocumentoForm
from .services import DocumentoService
from .models import Documento
from ..usuarios.models import ProgramaAcademico
from ..notificaciones.services import NotificacionService
from core.decorators.role_required import role_required
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from django.http import FileResponse
import os


@login_required
def dashboard_view(request):
    """Dashboard principal según rol del usuario."""
    user = request.user
    context = {}

    if user.rol == 'DOCENTE_PLANTA':
        context = DocumentoService.stats_docente(user)
    elif user.rol == 'COORDINADOR':
        context = DocumentoService.stats_coordinador(user)
    elif user.rol == 'DECANA':
        context = DocumentoService.stats_decana()

    return render(request, 'documentos/dashboard.html', context)


@login_required
def busqueda_avanzada_view(request):
    """Vista de búsqueda avanzada."""
    from ..permisos.services import PermisoService
    from apps.permisos.models import SolicitudAcceso

    query        = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria')
    factor_cna   = request.GET.get('factor')
    estado       = request.GET.get('estado')
    fecha_desde  = request.GET.get('desde')
    fecha_hasta  = request.GET.get('hasta')
    autor_query  = request.GET.get('autor', '').strip()
    vigente      = request.GET.get('vigente')
    visibilidad_filter = request.GET.get('visibilidad')
    orden        = request.GET.get('orden', 'recientes')

    # Solo ejecutar la búsqueda si hay algún parámetro activo
    hay_busqueda = any([query, categoria_id, factor_cna, estado,
                        fecha_desde, fecha_hasta, autor_query, vigente, visibilidad_filter])

    page_obj       = None
    total_resultados = 0

    if hay_busqueda:
        resultados = DocumentoService.busqueda_avanzada(
            usuario=request.user, query=query, categoria_id=categoria_id,
            factor_cna=factor_cna, estado=estado, fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta, autor_query=autor_query or None,
            vigente=vigente,
            visibilidad_filter=visibilidad_filter if visibilidad_filter else None,
            orden=orden,
        )
        total_resultados = resultados.count()

        paginator  = Paginator(resultados, 15)
        page_obj   = paginator.get_page(request.GET.get('page', 1))

        for doc in page_obj:
            doc.tiene_acceso = PermisoService.usuario_tiene_acceso(request.user, doc)
            if not doc.tiene_acceso:
                doc.solicitud_pendiente = SolicitudAcceso.objects.filter(
                    solicitante=request.user, documento=doc, estado='PENDIENTE'
                ).exists()

    return render(request, 'documentos/busqueda_avanzada.html', {
        'page_obj':        page_obj,
        'hay_busqueda':    hay_busqueda,
        'categorias':      DocumentoService.listar_categorias(),
        'factores_cna':    Documento.FACTORES_CNA,
        'total_resultados': total_resultados,
        'orden_actual':    orden,
    })


@login_required
def mis_documentos_view(request):
    """Vista de mis documentos (exclusivamente los del autor)."""
    estado = request.GET.get('estado')
    categoria = request.GET.get('categoria')
    factor = request.GET.get('factor')
    orden = request.GET.get('orden', '-fecha_creacion')
    q = request.GET.get('q')

    # Filtrado: Solo documentos del usuario actual
    queryset = Documento.objects.filter(autor=request.user)

    if q: queryset = queryset.filter(titulo__icontains=q)
    if estado: queryset = queryset.filter(estado=estado)
    if categoria: queryset = queryset.filter(categoria_id=categoria)
    if factor: queryset = queryset.filter(factor_cna=factor)

    if orden == 'antiguo':
        queryset = queryset.order_by('fecha_creacion')
    elif orden == 'nombre':
        queryset = queryset.order_by('titulo')
    else:
        queryset = queryset.order_by('-fecha_creacion')

    paginator = Paginator(queryset, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'documentos/mis_documentos.html', {
        'page_obj': page_obj,
        'categorias': DocumentoService.listar_categorias(),
        'factores_cna': Documento.FACTORES_CNA,
    })


@login_required
@role_required('COORDINADOR', 'DECANA')
def aprobar_documentos_view(request):
    """Vista exclusiva para revisar y aprobar documentos."""
    estado = request.GET.get('estado', 'PENDIENTE')
    urgente = request.GET.get('urgente')

    if request.user.rol == 'COORDINADOR':
        queryset = Documento.objects.filter(programa=request.user.programa_academico)
    else:
        queryset = Documento.objects.all()

    if estado:
        queryset = queryset.filter(estado=estado)
        
    hoy = timezone.now().date()
    hace_3_dias = timezone.now() - timedelta(days=3)
    
    # Calcular contadores
    pendientes_base = Documento.objects.filter(estado='PENDIENTE')
    if request.user.rol == 'COORDINADOR':
        pendientes_base = pendientes_base.filter(programa=request.user.programa_academico)

    por_revisar = pendientes_base.count()
    
    docs_urgentes = pendientes_base.filter(fecha_modificacion__lt=hace_3_dias)
    hay_urgentes = docs_urgentes.exists()
    
    base_hoy = Documento.objects.filter(fecha_modificacion__date=hoy)
    if request.user.rol == 'COORDINADOR':
        base_hoy = base_hoy.filter(programa=request.user.programa_academico)
        
    aprobados_hoy = base_hoy.filter(estado='APROBADO').count()
    rechazados_hoy = base_hoy.filter(estado='RECHAZADO').count()

    if urgente == '1':
        queryset = queryset.filter(estado='PENDIENTE', fecha_modificacion__lt=hace_3_dias)

    queryset = queryset.order_by('-fecha_modificacion')
    
    paginator = Paginator(queryset, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'documentos/aprobar_documentos.html', {
        'page_obj': page_obj,
        'por_revisar': por_revisar,
        'aprobados_hoy': aprobados_hoy,
        'rechazados_hoy': rechazados_hoy,
        'hay_urgentes': hay_urgentes,
        'docs_urgentes_count': docs_urgentes.count(),
        'estado_actual': estado,
        'es_urgente': urgente == '1',
    })


@login_required
def subir_documento(request):
    """Vista para subir un nuevo documento."""
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            requiere_aprobacion = request.POST.get('requiere_aprobacion') == 'on'

            documento = DocumentoService.crear_documento(
                titulo=form.cleaned_data['titulo'],
                descripcion=form.cleaned_data['descripcion'],
                archivo=request.FILES['archivo'],
                programa=form.cleaned_data['programa'],
                categoria=form.cleaned_data['categoria'],
                autor=request.user,
                requiere_aprobacion=requiere_aprobacion,
                es_sensible=form.cleaned_data['es_sensible'],
                factor_cna=form.cleaned_data.get('factor_cna'),
                fecha_vigencia=form.cleaned_data.get('fecha_vigencia'),
                visibilidad=form.cleaned_data.get('visibilidad', 'PROGRAMA'),
            )
            messages.success(request, f'Documento "{documento.titulo}" subido exitosamente.')
            return redirect('documentos:lista')
    else:
        form = DocumentoForm()

    return render(request, 'documentos/subir.html', {'form': form})


@login_required
def detalle_documento(request, documento_id):
    """Vista de detalle de un documento."""
    try:
        context = DocumentoService.obtener_detalle_documento(documento_id, request.user)
        if not context:
            messages.error(request, 'El documento no existe.')
            return redirect('documentos:mis_documentos')
    except PermissionError:
        # Si no tiene acceso, mostramos una versión bloqueada del detalle
        from .models import Documento
        from apps.permisos.models import SolicitudAcceso
        doc = get_object_or_404(Documento, pk=documento_id)
        
        solicitud_pendiente = SolicitudAcceso.objects.filter(
            solicitante=request.user, documento=doc, estado='PENDIENTE'
        ).exists()
        
        context = {
            'documento': doc,
            'acceso_denegado': True,
            'solicitud_pendiente': solicitud_pendiente,
        }

    return render(request, 'documentos/detalle.html', context)


@login_required
@role_required('DECANA', 'COORDINADOR')
def aprobar_documento(request, documento_id):
    """Vista para aprobar un documento (POST)."""
    if request.method == 'POST':
        try:
            DocumentoService.aprobar_documento(
                documento_id, request.user, request
            )
            messages.success(request, 'Documento aprobado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al aprobar: {e}')
    return redirect('documentos:aprobar')


@login_required
@role_required('DECANA', 'COORDINADOR')
def aprobar_documentos_lote(request):
    """Procesa la aprobación de múltiples documentos seleccionados."""
    if request.method == 'POST':
        documento_ids = request.POST.getlist('documento_ids')
        if not documento_ids:
            messages.warning(request, 'No se seleccionaron documentos para aprobar.')
            return redirect('documentos:aprobar')
            
        aprobados = 0
        errores = 0
        
        for doc_id in documento_ids:
            try:
                DocumentoService.aprobar_documento(doc_id, request.user, request)
                aprobados += 1
            except Exception:
                errores += 1
        
        if aprobados > 0:
            messages.success(request, f'Se aprobaron {aprobados} documentos correctamente.')
        if errores > 0:
            messages.error(request, f'No se pudieron aprobar {errores} documentos.')
            
    return redirect('documentos:aprobar')


@login_required
@role_required('DECANA', 'COORDINADOR')
def rechazar_documento(request, documento_id):
    """Vista para rechazar un documento (POST)."""
    if request.method == 'POST':
        comentario = request.POST.get('comentario', '').strip()
        if not comentario:
            messages.error(request, 'El motivo de rechazo es obligatorio.')
            return redirect('documentos:aprobar')
            
        try:
            DocumentoService.rechazar_documento(
                documento_id, request.user, comentario, request
            )
            messages.success(request, 'Documento rechazado.')
        except Exception as e:
            messages.error(request, f'Error al rechazar: {e}')
    return redirect('documentos:aprobar')


@login_required
def eliminar_documento(request, documento_id):
    """Vista para eliminar un documento."""
    if request.method == 'POST':
        try:
            DocumentoService.eliminar_documento(
                documento_id, request.user, request
            )
            messages.success(request, 'Documento eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar el documento: {e}')
    return redirect('documentos:lista')


@login_required
@role_required('DECANA')
def factores_cna_view(request):
    """Vista de Factores CNA para la Decana."""
    from django.db.models import Count, Q

    # Metas requeridas por factor (teóricas, pueden moverse a BBDD en el futuro)
    metas_por_factor = {
        'F1': 15, 'F2': 25, 'F3': 20, 'F4': 10, 'F5': 30, 'F6': 15,
        'F7': 10, 'F8': 20, 'F9': 15, 'F10': 15, 'F11': 20, 'F12': 10,
    }

    # Agrupar documentos por factor y contar aprobados y pendientes
    stats = Documento.objects.exclude(factor_cna__isnull=True).exclude(factor_cna='').values('factor_cna').annotate(
        total_aprobados=Count('id', filter=Q(estado='APROBADO')),
        total_pendientes=Count('id', filter=Q(estado='PENDIENTE'))
    )
    stats_dict = {item['factor_cna']: item for item in stats}

    factores_data = []
    total_requeridos = 0
    total_aprobados_global = 0

    for codigo, nombre in Documento.FACTORES_CNA:
        meta = metas_por_factor.get(codigo, 10)
        total_requeridos += meta

        f_stats = stats_dict.get(codigo, {'total_aprobados': 0, 'total_pendientes': 0})
        aprobados = f_stats['total_aprobados']
        pendientes = f_stats['total_pendientes']
        
        faltantes = max(0, meta - aprobados)
        porcentaje = int((aprobados / meta) * 100) if meta > 0 else 100
        if porcentaje > 100: porcentaje = 100

        total_aprobados_global += aprobados

        # Limpiar el nombre (quitar "Factor X: ")
        nombre_limpio = nombre.split(':', 1)[-1].strip() if ':' in nombre else nombre

        factores_data.append({
            'codigo': codigo,
            'numero': codigo.replace('F', ''),
            'nombre': nombre_limpio,
            'aprobados': aprobados,
            'pendientes': pendientes,
            'faltantes': faltantes,
            'porcentaje': porcentaje,
        })

    # Calcular progreso general
    total_faltantes_global = max(0, total_requeridos - total_aprobados_global)
    progreso_general = int((total_aprobados_global / total_requeridos) * 100) if total_requeridos > 0 else 0
    if progreso_general > 100: progreso_general = 100

    context = {
        'factores': factores_data,
        'total_requeridos': total_requeridos,
        'total_aprobados': total_aprobados_global,
        'total_faltantes': total_faltantes_global,
        'progreso_general': progreso_general,
    }

    return render(request, 'documentos/factores_cna.html', context)

@login_required
def descargar_documento_view(request, documento_id):
    """Descarga de documento con registro de auditoría."""
    try:
        ruta = DocumentoService.registrar_descarga(documento_id, request.user, request)
        if os.path.exists(ruta):
            response = FileResponse(open(ruta, 'rb'), as_attachment=True)
            return response
        else:
            messages.error(request, 'El archivo físico no se encontró en el servidor.')
    except PermissionError:
        messages.error(request, 'No tienes permiso para descargar este documento.')
    except Exception as e:
        messages.error(request, f'Error al descargar: {e}')
    
    return redirect(request.META.get('HTTP_REFERER', 'documentos:busqueda'))

@login_required
def descargar_version_view(request, ver_id):
    """Descarga de una versión anterior con auditoría."""
    from apps.versiones.models import Version
    from core.services.audit_service import AuditService
    try:
        version = Version.objects.get(pk=ver_id)
        doc = version.documento
        
        # Verificar permisos (mismos que para el doc actual)
        DocumentoService.registrar_descarga(doc.id, request.user, request)
        
        # Sobreescribir auditoría
        AuditService.log(
            usuario=request.user, accion='DESCARGO', documento=doc, request=request,
            detalle=f"Versión {version.numero_version}"
        )
        
        ruta = version.archivo.path
        if os.path.exists(ruta):
            response = FileResponse(open(ruta, 'rb'), as_attachment=True)
            return response
        else:
            messages.error(request, 'El archivo físico de la versión no se encontró.')
    except Exception as e:
        messages.error(request, f'Error al descargar la versión: {e}')
        
    return redirect(request.META.get('HTTP_REFERER', 'documentos:busqueda'))

from django.http import JsonResponse
from django.db.models import Q

@login_required
def buscar_documentos_ajax(request):
    """Búsqueda de documentos vía AJAX para el navbar."""
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})

    # Filtrar documentos visibles para el usuario usando la misma lógica de visibilidad
    if request.user.rol == 'DECANA':
        queryset = Documento.objects.all()
    elif request.user.rol == 'COORDINADOR':
        queryset = Documento.objects.all()
    else:
        queryset = Documento.objects.filter(
            Q(autor=request.user) |
            Q(visibilidad='INSTITUCIONAL') |
            Q(visibilidad='PROGRAMA', programa=request.user.programa_academico) |
            Q(permisos__usuario=request.user, permisos__puede_ver=True)
        ).distinct()

    results = queryset.filter(titulo__icontains=query)[:5]
    
    data = []
    for doc in results:
        data.append({
            'id': doc.id,
            'titulo': doc.titulo,
            'url': f"/documentos/{doc.id}/",
        })
    
    return JsonResponse({'results': data})
