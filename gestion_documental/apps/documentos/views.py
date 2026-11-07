"""
Vistas del módulo de documentos.

Las vistas reciben la petición HTTP, validan formularios y delegan
la lógica de negocio al servicio correspondiente.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import DocumentoForm, DocumentoEditForm
from .services import DocumentoService
from .models import Documento
from ..usuarios.models import ProgramaAcademico
from ..notificaciones.services import NotificacionService
from core.decorators.role_required import role_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.http import FileResponse
import logging
import os

from core.utils.helpers import ReglaNegocioError

logger = logging.getLogger(__name__)

# FR-010: textos fijos; el detalle técnico solo va al log del servidor.
MSG_ERROR_GENERICO = 'No se pudo completar la acción. Inténtalo de nuevo o contacta a soporte.'


def _auditar_denegado(request, documento, detalle):
    """A6: todo intento de acceso sin permiso queda en la auditoría."""
    from core.services.audit_service import AuditService
    AuditService.log(usuario=request.user, accion='ACCESO_DENEGADO',
                     documento=documento, request=request, detalle=detalle)


def _respuesta_archivo(ruta, inline=False, content_type=None):
    """Entrega un archivo de MEDIA_ROOT por Nginx (X-Accel-Redirect) o por Django."""
    from django.conf import settings
    from django.http import HttpResponse
    from core.utils.helpers import content_disposition_seguro, nombre_archivo_seguro
    import urllib.parse

    filename = nombre_archivo_seguro(os.path.basename(ruta))
    if getattr(settings, 'USE_X_ACCEL_REDIRECT', False):
        rel_path = os.path.relpath(ruta, settings.MEDIA_ROOT).replace('\\', '/')
        if rel_path.startswith('..'):
            raise ValueError('Ruta de archivo fuera del almacenamiento permitido.')
        response = HttpResponse(content_type=content_type) if content_type else HttpResponse()
        response['X-Accel-Redirect'] = f"/internal_media/{urllib.parse.quote(rel_path)}"
        disposition = content_disposition_seguro(filename)
        response['Content-Disposition'] = disposition.replace('attachment', 'inline', 1) if inline else disposition
    else:
        response = FileResponse(open(ruta, 'rb'), as_attachment=not inline,
                                filename=filename, content_type=content_type)
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@login_required
def dashboard_view(request):
    """Dashboard principal según rol del usuario."""
    from django.urls import reverse
    from django.utils.html import format_html
    from .metricas import MetricasService

    user = request.user
    context = {'rol': user.rol}

    if user.rol in ('DECANA', 'COORDINADOR'):
        huella = MetricasService.huella_facultad()
        cola = MetricasService.cola_revision()
        context.update({
            'huella': huella,
            'matriz': MetricasService.matriz_factor_programa(),
            'cola': cola[:6] if user.rol == 'DECANA' else cola,
            'cola_total': len(cola),
            'tiempos': MetricasService.tiempos_revision(),
            'pulso': MetricasService.pulso_30_dias(),
            'notificaciones': NotificacionService.listar_notificaciones(user)[:5],
        })
        if user.rol == 'DECANA':
            context.update({
                'banner_titular': 'Así va la acreditación de la facultad',
                'banner_cifra': f"{huella['total_aprobados']} / {huella['total_meta']}",
                'banner_detalle': f"evidencias aprobadas · {huella['gradacion'].porcentaje} % de la meta",
                'banner_nota': format_html(
                    'El factor más lejos de su meta es <strong>{} · {}</strong> ({} de {}).',
                    huella['mas_lejano'].codigo, huella['mas_lejano'].nombre,
                    huella['mas_lejano'].aprobados, huella['mas_lejano'].meta,
                ),
                'banner_acciones': [
                    {'url': reverse('documentos:factores_cna'), 'texto': 'Ver la matriz CNA',
                     'icono': 'grid-3x3', 'clase': 'sg-btn--primario'},
                ],
            })
        else:
            mas_antigua = cola[0] if cola else None
            context.update({
                'banner_titular': 'Tu cola de revisión' if mas_antigua else 'Tu cola está al día',
                'banner_cifra': str(len(cola)),
                'banner_detalle': 'evidencia por revisar' if len(cola) == 1 else 'evidencias por revisar',
                'banner_nota': (
                    format_html('La más antigua, <strong>{}</strong>, lleva {} {} esperando. '
                                'La facultad va en {} de {} evidencias aprobadas.',
                                mas_antigua.titulo, mas_antigua.dias_esperando,
                                'día' if mas_antigua.dias_esperando == 1 else 'días',
                                huella['total_aprobados'], huella['total_meta'])
                    if mas_antigua else
                    format_html('La facultad va en {} de {} evidencias aprobadas.',
                                huella['total_aprobados'], huella['total_meta'])
                ),
                'banner_acciones': (
                    [{'url': reverse('documentos:detalle', args=[mas_antigua.id]),
                      'texto': 'Revisar la más antigua', 'icono': 'clipboard-check',
                      'clase': 'sg-btn--primario'}] if mas_antigua else []
                ),
            })
        if huella['pendientes_envejecidos']:
            context['banner_acciones'].append({
                'url': reverse('documentos:aprobar') + '?urgente=1',
                'texto': f"{huella['pendientes_envejecidos']} con más de 3 días",
                'icono': 'hourglass', 'clase': 'sg-btn--alerta',
            })
    else:
        personal = MetricasService.huella_personal(user)
        t = personal['totales']
        context.update(DocumentoService.stats_docente(user))
        context.update({
            'personal': personal,
            'banner_titular': 'Tus evidencias del último año' if t['total'] else 'Aún no has subido evidencias',
            'banner_nota': (
                format_html('<strong>{}</strong> {}, <strong>{}</strong> en revisión y '
                            '<strong>{}</strong> {}.',
                            t['aprobadas'], 'aprobada' if t['aprobadas'] == 1 else 'aprobadas',
                            t['pendientes'], t['rechazadas'],
                            'rechazada' if t['rechazadas'] == 1 else 'rechazadas')
                if t['total'] else 'Sube tu primera evidencia y elige el factor CNA al que aporta.'
            ),
            'banner_cifra': str(t['total']),
            'banner_detalle': 'evidencia subida' if t['total'] == 1 else 'evidencias subidas',
            'banner_acciones': [
                {'url': reverse('documentos:subir'), 'texto': 'Subir evidencia',
                 'icono': 'upload', 'clase': 'sg-btn--primario'},
            ],
            'rechazadas_recientes': Documento.objects.filter(autor=user, estado='RECHAZADO')
            .order_by('-fecha_modificacion')[:3],
        })

    return render(request, 'documentos/dashboard.html', context)


@login_required
def busqueda_avanzada_view(request):
    """Vista de búsqueda avanzada."""
    from ..permisos.services import PermisoService

    query        = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria')
    programa_id  = request.GET.get('programa')
    factor_cna   = request.GET.get('factor')
    estado       = request.GET.get('estado')
    fecha_desde  = request.GET.get('desde')
    fecha_hasta  = request.GET.get('hasta')
    autor_query  = request.GET.get('autor', '').strip()
    vigente      = request.GET.get('vigente')
    visibilidad_filter = request.GET.get('visibilidad')
    orden        = request.GET.get('orden', 'recientes')

    # Solo ejecutar la búsqueda si hay algún parámetro activo
    hay_busqueda = any([query, categoria_id, programa_id, factor_cna, estado,
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
            orden=orden, programa_id=programa_id,
        )
        paginator  = Paginator(resultados, 15)
        page_obj   = paginator.get_page(request.GET.get('page', 1))
        total_resultados = paginator.count

        # Batch H-03: 2 queries fijas en vez de 2 por documento.
        # Directivos y superusuarios siempre tienen acceso: sin consultas.
        docs_pagina = list(page_obj)
        if docs_pagina and not (
            request.user.is_superuser or request.user.rol in ('COORDINADOR', 'DECANA')
        ):
            permisos_ids, solicitudes_ids = PermisoService.precargar_accesos(
                request.user, [d.id for d in docs_pagina]
            )
        else:
            permisos_ids, solicitudes_ids = set(), set()

        for doc in docs_pagina:
            doc.tiene_acceso = PermisoService.usuario_tiene_acceso(
                request.user, doc, _permisos_ids=permisos_ids
            )
            doc.solicitud_pendiente = (
                not doc.tiene_acceso and doc.id in solicitudes_ids
            )

    return render(request, 'documentos/busqueda_avanzada.html', {
        'page_obj':        page_obj,
        'hay_busqueda':    hay_busqueda,
        'categorias':      DocumentoService.listar_categorias(),
        'programas':       ProgramaAcademico.objects.order_by('nombre'),
        'factores_cna':    Documento.FACTORES_CNA,
        'total_resultados': total_resultados,
        'filtros_activos': sum(1 for v in [categoria_id, programa_id, factor_cna, estado, fecha_desde, fecha_hasta, autor_query, vigente, visibilidad_filter] if v),
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
    queryset = Documento.objects.filter(autor=request.user).select_related(
        'programa', 'categoria', 'autor'
    )

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

    # Regla facultad: COORDINADOR (única) y DECANA ven todos los programas.
    queryset = Documento.objects.all().select_related('programa', 'categoria', 'autor')

    if estado:
        queryset = queryset.filter(estado=estado)
        
    hace_3_dias = timezone.now() - timedelta(days=3)
    # H-13: rango del día (index-friendly) en vez de __date.
    _ahora = timezone.now()
    inicio_hoy = _ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    fin_hoy = inicio_hoy + timedelta(days=1)
    
    # Calcular contadores (facultad completa para COORDINADOR y DECANA)
    # Un solo agregado en vez de 3 consultas secuenciales.
    conteo = Documento.objects.aggregate(
        urgentes=Count('id', filter=Q(estado='PENDIENTE', fecha_modificacion__lt=hace_3_dias)),
        por_revisar=Count('id', filter=Q(estado='PENDIENTE')),
        aprobados_hoy=Count(
            'id', filter=Q(
                estado='APROBADO',
                fecha_modificacion__gte=inicio_hoy,
                fecha_modificacion__lt=fin_hoy,
            )
        ),
        rechazados_hoy=Count(
            'id', filter=Q(
                estado='RECHAZADO',
                fecha_modificacion__gte=inicio_hoy,
                fecha_modificacion__lt=fin_hoy,
            )
        ),
    )
    por_revisar = conteo['por_revisar']
    aprobados_hoy = conteo['aprobados_hoy']
    rechazados_hoy = conteo['rechazados_hoy']
    # C1: el contador sale del mismo agregado (antes: NameError -> 500).
    docs_urgentes_count = conteo['urgentes']
    hay_urgentes = docs_urgentes_count > 0

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
        'docs_urgentes_count': docs_urgentes_count,
        'estado_actual': estado,
        'es_urgente': urgente == '1',
    })


@login_required
def subir_documento(request):
    """Vista para subir un nuevo documento."""
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES, usuario=request.user)
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
            messages.success(request, f'Subiste «{documento.titulo}».' + (' Quedó en revisión.' if documento.estado == 'PENDIENTE' else ''))
            return redirect('documentos:lista')
    else:
        form = DocumentoForm(usuario=request.user)

    return render(request, 'documentos/subir.html', {'form': form})


@login_required
def editar_documento(request, documento_id):
    """Vista para editar metadatos de un documento existente."""
    from .models import Documento
    from core.services.audit_service import AuditService
    
    documento = get_object_or_404(Documento, id=documento_id)
    
    # Solo el autor o decana/coordinador pueden editar
    if request.user != documento.autor and request.user.rol not in ['DECANA', 'COORDINADOR']:
        messages.error(request, 'No tienes permiso para editar esta evidencia.')
        return redirect('documentos:detalle', documento_id=documento.id)

    if request.method == 'POST':
        form = DocumentoEditForm(request.POST, instance=documento, usuario=request.user)
        if form.is_valid():
            documento = form.save(commit=False)
            # M7: si un docente cambia los datos de una evidencia aprobada, vuelve a revisión
            # (las directivas conservan el estado, igual que con las versiones).
            volvio_a_revision = (request.user.rol not in ('DECANA', 'COORDINADOR')
                                 and documento.estado == Documento.Estado.APROBADO and form.has_changed())
            if volvio_a_revision:
                documento.estado = Documento.Estado.PENDIENTE
            documento.save()
            
            # Registrar en auditoría
            AuditService.log(
                usuario=request.user,
                accion='EDITO_METADATOS',
                documento=documento,
                request=request,
                detalle='Se actualizaron los metadatos del documento.'
            )
            
            messages.success(request, f'Guardaste los cambios de «{documento.titulo}».'
                             + (' Volvió a revisión porque estaba aprobada.' if volvio_a_revision else ''))
            return redirect('documentos:detalle', documento_id=documento.id)
    else:
        form = DocumentoEditForm(instance=documento, usuario=request.user)

    return render(request, 'documentos/editar.html', {'form': form, 'documento': documento})



@login_required
def detalle_documento(request, documento_id):
    """Vista de detalle de un documento."""
    try:
        context = DocumentoService.obtener_detalle_documento(documento_id, request.user)
        if not context:
            messages.error(request, 'La evidencia no existe.')
            return redirect('documentos:mis_documentos')
    except PermissionError:
        # Si no tiene acceso, mostramos una versión bloqueada del detalle
        from .models import Documento
        from ..permisos.models import SolicitudAcceso
        doc = get_object_or_404(Documento, pk=documento_id)
        _auditar_denegado(request, doc, 'Intento de ver el detalle sin permiso')

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
            messages.success(request, 'Evidencia aprobada. Ya cuenta en su factor.')
        except ReglaNegocioError as e:
            messages.error(request, str(e))
        except Documento.DoesNotExist:
            messages.error(request, 'La evidencia no existe.')
        except Exception:
            logger.exception('Error al aprobar documento %s', documento_id)
            messages.error(request, MSG_ERROR_GENERICO)
    return redirect('documentos:aprobar')


@login_required
@role_required('DECANA', 'COORDINADOR')
def aprobar_documentos_lote(request):
    """Procesa la aprobación de múltiples documentos seleccionados."""
    if request.method == 'POST':
        documento_ids = request.POST.getlist('documento_ids')
        if not documento_ids:
            messages.warning(request, 'Selecciona al menos una evidencia para aprobar.')
            return redirect('documentos:aprobar')
            
        aprobados = 0
        errores = 0
        
        for doc_id in documento_ids:
            try:
                DocumentoService.aprobar_documento(doc_id, request.user, request)
                aprobados += 1
            except ReglaNegocioError as e:
                messages.warning(request, str(e))
            except Exception:
                logger.exception('Error al aprobar en lote el documento %s', doc_id)
                errores += 1
        
        if aprobados > 0:
            messages.success(request, f'Aprobaste {aprobados} evidencia' + ('s.' if aprobados != 1 else '.'))
        if errores > 0:
            messages.error(request, f'No se pudo aprobar {errores} evidencia' + ('s.' if errores != 1 else '.'))
            
    return redirect('documentos:aprobar')


@login_required
@role_required('DECANA', 'COORDINADOR')
def rechazar_documento(request, documento_id):
    """Vista para rechazar un documento (POST)."""
    if request.method == 'POST':
        comentario = request.POST.get('comentario', '').strip()
        if not comentario:
            messages.error(request, 'Escribe el motivo del rechazo para que el autor sepa qué corregir.')
            return redirect('documentos:aprobar')
            
        try:
            DocumentoService.rechazar_documento(
                documento_id, request.user, comentario, request
            )
            messages.success(request, 'Evidencia rechazada. Le avisamos al autor con tu motivo.')
        except ReglaNegocioError as e:
            messages.error(request, str(e))
        except Documento.DoesNotExist:
            messages.error(request, 'La evidencia no existe.')
        except Exception:
            logger.exception('Error al rechazar documento %s', documento_id)
            messages.error(request, MSG_ERROR_GENERICO)
    return redirect('documentos:aprobar')


@login_required
def eliminar_documento(request, documento_id):
    """Vista para enviar un documento a la papelera (Soft Delete)."""
    if request.method == 'POST':
        try:
            DocumentoService.eliminar_documento(
                documento_id, request.user, request
            )
            messages.success(request, 'Evidencia enviada a la papelera. Puedes restaurarla desde allí.')
        except PermissionError as e:
            messages.error(request, str(e))
        except Documento.DoesNotExist:
            messages.error(request, 'La evidencia no existe.')
        except Exception:
            logger.exception('Error al enviar a la papelera el documento %s', documento_id)
            messages.error(request, MSG_ERROR_GENERICO)
    return redirect('documentos:lista')

@login_required
def papelera_documentos(request):
    """Vista de la papelera de reciclaje."""
    from .models import Documento
    # Solo mostrar documentos en la papelera
    if request.user.rol in ['DECANA', 'COORDINADOR']:
        documentos = Documento.all_objects.filter(is_deleted=True).select_related(
            'programa', 'categoria', 'autor'
        ).order_by('-deleted_at')
    else:
        # Docentes u otros roles solo ven sus propios documentos eliminados
        documentos = Documento.all_objects.filter(
            is_deleted=True,
            autor=request.user
        ).select_related('programa', 'categoria', 'autor').order_by('-deleted_at')
        
    return render(request, 'documentos/papelera.html', {'documentos': documentos})

@login_required
def restaurar_documento(request, documento_id):
    """Restaura un documento desde la papelera."""
    if request.method == 'POST':
        try:
            from .models import Documento
            doc = Documento.all_objects.get(pk=documento_id)
            
            # Verificar permisos
            if request.user.rol not in ['DECANA', 'COORDINADOR'] and doc.autor != request.user:
                messages.error(request, 'No tienes permiso para restaurar esta evidencia.')
                return redirect('documentos:papelera')
                
            DocumentoService.restaurar_documento(documento_id, request.user, request)
            messages.success(request, 'Evidencia restaurada.')
        except Documento.DoesNotExist:
            messages.error(request, 'La evidencia no existe.')
        except Exception:
            logger.exception('Error al restaurar el documento %s', documento_id)
            messages.error(request, MSG_ERROR_GENERICO)
    return redirect('documentos:papelera')


@login_required
@role_required('DECANA')
def factores_cna_view(request):
    """Vista de Factores CNA para la Decana."""
    from .metricas import MetricasService

    return render(request, 'documentos/factores_cna.html', {
        'huella': MetricasService.huella_facultad(),
        'matriz': MetricasService.matriz_factor_programa(),
    })

@login_required
@role_required('DECANA')
def exportar_factores_excel(request):
    """Exporta las estadísticas CNA a Excel."""
    from django.http import HttpResponse
    from django.contrib import messages
    from .services import ReporteService
    
    try:
        excel_data = ReporteService.generar_excel_cna()
        response = HttpResponse(excel_data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="estadisticas_cna.xlsx"'
        return response
    except Exception:
        logger.exception('Error al generar el Excel de factores CNA')
        messages.error(request, 'No se pudo generar el archivo Excel. Inténtalo de nuevo.')
        return redirect('documentos:factores_cna')

@login_required
@role_required('DECANA')
def exportar_factores_pdf(request):
    """Exporta las estadísticas CNA a PDF."""
    from django.http import HttpResponse
    from django.contrib import messages
    from .services import ReporteService
    
    try:
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="estadisticas_cna.pdf"'
        ReporteService.generar_pdf_cna(response)
        return response
    except Exception:
        logger.exception('Error al generar el PDF de factores CNA')
        messages.error(request, 'No se pudo generar el archivo PDF. Inténtalo de nuevo.')
        return redirect('documentos:factores_cna')

@login_required
def descargar_documento_view(request, documento_id):
    """Descarga de documento con registro de auditoría."""
    try:
        ruta = DocumentoService.registrar_descarga(documento_id, request.user, request)
        if os.path.exists(ruta):
            return _respuesta_archivo(ruta)
        messages.error(request, 'El archivo no está disponible. Contacta a soporte.')
    except Documento.DoesNotExist:
        messages.error(request, 'La evidencia no existe.')
    except PermissionError:
        _auditar_denegado(request, Documento.objects.filter(pk=documento_id).first(),
                          'Intento de descarga sin permiso')
        messages.error(request, 'No tienes permiso para descargar este documento.')
    except Exception:
        logger.exception('Error al descargar el documento %s', documento_id)
        messages.error(request, MSG_ERROR_GENERICO)

    from core.utils.helpers import redirect_back_seguro
    return redirect_back_seguro(request, 'documentos:busqueda')

@login_required
def previsualizar_documento(request, documento_id):
    """A4: vista previa en línea (solo PDF) con el mismo control de acceso que la descarga."""
    from django.core.exceptions import PermissionDenied
    from django.http import Http404
    try:
        ruta = DocumentoService.archivo_para_vista_previa(documento_id, request.user, request)
    except Documento.DoesNotExist:
        raise Http404('Documento no disponible.')
    except PermissionError:
        raise PermissionDenied('No tienes permiso para ver este documento.')
    except FileNotFoundError:
        raise Http404('Vista previa no disponible.')
    return _respuesta_archivo(ruta, inline=True, content_type='application/pdf')


@login_required
def descargar_version_view(request, ver_id):
    """Descarga de una versión anterior con auditoría."""
    from ..versiones.models import Version
    doc = None
    try:
        version = Version.objects.select_related('documento').get(pk=ver_id)
        doc = version.documento

        # Verificar permisos y registrar una única auditoría con detalle
        DocumentoService.registrar_descarga(
            doc.id, request.user, request, detalle=f"Versión {version.numero_version}"
        )

        ruta = version.archivo.path
        if os.path.exists(ruta):
            return _respuesta_archivo(ruta)
        messages.error(request, 'El archivo de la versión no está disponible. Contacta a soporte.')
    except (Version.DoesNotExist, Documento.DoesNotExist):
        messages.error(request, 'La versión no existe.')
    except PermissionError:
        _auditar_denegado(request, doc, f'Intento de descargar la versión {ver_id} sin permiso')
        messages.error(request, 'No tienes permiso para descargar esta versión.')
    except Exception:
        logger.exception('Error al descargar la versión %s', ver_id)
        messages.error(request, MSG_ERROR_GENERICO)

    from core.utils.helpers import redirect_back_seguro
    return redirect_back_seguro(request, 'documentos:busqueda')

from django.http import JsonResponse
from django.db.models import Q

@login_required
def buscar_documentos_ajax(request):
    """Búsqueda de documentos vía AJAX para el navbar."""
    from core.utils.helpers import throttle_fijo
    # 60 búsquedas/min por usuario: invisible para humanos, frena abusos.
    if throttle_fijo(f"sigea:throttle:buscar:{request.user.id}", 60, 60):
        return JsonResponse({'results': [], 'throttled': True}, status=429)
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})

    # Filtrar documentos visibles para el usuario usando la misma lógica de visibilidad
    # Regla facultad: DECANA y COORDINADOR son únicos de facultad -> ven todo.
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
