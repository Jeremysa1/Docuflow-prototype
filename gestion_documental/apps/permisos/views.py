"""
Vistas del módulo de permisos.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden

from apps.permisos.services import PermisoService
from apps.permisos.models import SolicitudAcceso, VotoAccesoSensible
from apps.documentos.models import Documento
from apps.usuarios.models import Usuario
from core.decorators.role_required import role_required
from django.core.paginator import Paginator


@login_required
def gestionar_accesos_view(request, doc_id):
    """
    Vista para gestionar accesos de un documento.
    Solo pueden acceder: el autor, COORDINADOR del mismo programa, DECANA.
    """
    documento = get_object_or_404(
        Documento.objects.select_related('programa', 'autor'), pk=doc_id
    )

    # Verificar permisos de acceso a esta pantalla
    user = request.user
    es_autor = (user == documento.autor)
    es_coordinador_programa = (
        user.rol == 'COORDINADOR' and
        user.programa_academico == documento.programa
    )
    es_decana = (user.rol == 'DECANA')

    if not (es_autor or es_coordinador_programa or es_decana):
        return HttpResponseForbidden("No tienes permiso para gestionar accesos de este documento.")

    # Obtener estado de accesos
    estado_accesos = PermisoService.obtener_estado_accesos_documento(doc_id, user)

    # Anotar cada solicitud con datos calculados para simplificar el template
    solicitudes = list(estado_accesos['solicitudes_pendientes'])
    for sol in solicitudes:
        if documento.es_sensible:
            sol.ya_voto = VotoAccesoSensible.objects.filter(
                solicitud=sol, votante=user
            ).exists()
            # Contar aprobaciones
            sol.aprobaciones_count = VotoAccesoSensible.objects.filter(
                solicitud=sol, voto='APROBADO'
            ).count()
        else:
            sol.ya_voto = False
            sol.aprobaciones_count = 0

    context = {
        'documento': documento,
        'solicitudes_pendientes': solicitudes,
        'usuarios_con_acceso': estado_accesos['usuarios_con_acceso'],
        'solicitudes_rechazadas': estado_accesos['solicitudes_rechazadas'],
        'puede_revocar': estado_accesos['puede_revocar'],
        'es_sensible': documento.es_sensible,
    }

    return render(request, 'permisos/gestionar_accesos.html', context)


@login_required
def responder_solicitud_view(request, solicitud_id):
    """Responde a una solicitud de acceso (POST)."""
    if request.method != 'POST':
        return redirect('documentos:busqueda')

    decision = request.POST.get('decision')
    motivo_rechazo = request.POST.get('motivo_rechazo', '').strip()

    try:
        solicitud = SolicitudAcceso.objects.select_related('documento').get(pk=solicitud_id)
        documento = solicitud.documento

        if documento.es_sensible:
            # Normalizar decision: el formulario envía APROBADA/RECHAZADA,
            # pero VotoAccesoSensible usa APROBADO/RECHAZADO
            voto_map = {'APROBADA': 'APROBADO', 'RECHAZADA': 'RECHAZADO',
                        'APROBADO': 'APROBADO', 'RECHAZADO': 'RECHAZADO'}
            voto_normalizado = voto_map.get(decision, decision)

            PermisoService.votar_acceso_sensible(
                solicitud_id=solicitud_id,
                votante=request.user,
                voto=voto_normalizado,
                motivo_rechazo=motivo_rechazo if voto_normalizado == 'RECHAZADO' else None
            )
            messages.success(request, f'Tu voto fue registrado exitosamente.')
        else:
            # Responder solicitud normal
            PermisoService.responder_solicitud_normal(
                solicitud_id=solicitud_id,
                respondedor=request.user,
                decision=decision,
                motivo_rechazo=motivo_rechazo if decision == 'RECHAZADA' else None
            )
            msg = 'aprobada' if decision == 'APROBADA' else 'rechazada'
            messages.success(request, f'Solicitud {msg} exitosamente.')

        return redirect('permisos:gestionar_accesos', doc_id=documento.id)

    except Exception as e:
        messages.error(request, str(e))
        # Try to redirect back to the document
        try:
            solicitud = SolicitudAcceso.objects.select_related('documento').get(pk=solicitud_id)
            return redirect('permisos:gestionar_accesos', doc_id=solicitud.documento.id)
        except SolicitudAcceso.DoesNotExist:
            return redirect('documentos:busqueda')


@login_required
def revocar_acceso_view(request, doc_id, usuario_id):
    """Revoca el acceso de un usuario a un documento (POST)."""
    if request.method == 'POST':
        try:
            PermisoService.revocar_acceso(doc_id, usuario_id, request.user)
            messages.success(request, 'Acceso revocado exitosamente.')
        except Exception as e:
            messages.error(request, str(e))
    return redirect('permisos:gestionar_accesos', doc_id=doc_id)


@login_required
def solicitar_acceso_view(request, doc_id):
    """Solicita acceso a un documento (POST)."""
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '').strip()

        if not motivo:
            messages.error(request, 'El motivo es obligatorio.')
            return redirect('documentos:busqueda')

        try:
            PermisoService.solicitar_acceso(request.user, doc_id, motivo)
            messages.success(
                request,
                'Tu solicitud fue enviada. Recibirás una notificación cuando sea respondida.'
            )
        except Exception as e:
            messages.error(request, str(e))

    return redirect('documentos:busqueda')


# ─── VISTAS LEGACY (mantenidas por compatibilidad) ───────────

@login_required
@role_required('COORDINADOR', 'DECANA')
def listar_solicitudes_view(request):
    """Lista las solicitudes pendientes (vista legacy)."""
    queryset = PermisoService.listar_solicitudes_pendientes(request.user)

    paginator = Paginator(queryset, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'permisos/solicitudes.html', {
        'page_obj': page_obj
    })
