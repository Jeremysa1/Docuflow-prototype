"""
Servicios del módulo de auditoría.

Contiene la lógica de negocio para registrar y consultar actividades.
"""
from django.db import models
from django.db.models import Q
from apps.auditoria.models import RegistroAuditoria


class AuditoriaService:
    """Servicio para la gestión de registros de auditoría."""

    @staticmethod
    def registrar(usuario, accion, documento=None, ip_address=None, detalle=''):
        """Registra una acción en el log de auditoría."""
        return RegistroAuditoria.objects.create(
            usuario=usuario,
            accion=accion,
            documento=documento,
            ip_address=ip_address,
            detalle=detalle,
        )

    @staticmethod
    def listar_registros(usuario=None, accion=None, documento=None, fecha_inicio=None, fecha_fin=None):
        """Lista registros de auditoría con filtros opcionales."""
        queryset = RegistroAuditoria.objects.select_related('usuario', 'documento').order_by('-fecha_hora')

        if usuario:
            # Intentar filtrar por ID si es numérico, de lo contrario por nombre/email
            if usuario.isdigit():
                queryset = queryset.filter(usuario_id=usuario)
            else:
                queryset = queryset.filter(
                    Q(usuario__first_name__icontains=usuario) |
                    Q(usuario__last_name__icontains=usuario) |
                    Q(usuario__email__icontains=usuario)
                )

        if accion:
            queryset = queryset.filter(accion=accion)

        if documento:
            if documento.isdigit():
                queryset = queryset.filter(documento_id=documento)
            else:
                queryset = queryset.filter(documento__titulo__icontains=documento)

        if fecha_inicio:
            queryset = queryset.filter(fecha_hora__date__gte=fecha_inicio)
        
        if fecha_fin:
            queryset = queryset.filter(fecha_hora__date__lte=fecha_fin)

        return queryset

    @staticmethod
    def obtener_historial_documento(documento_id):
        """Obtiene el historial de auditoría de un documento específico."""
        return RegistroAuditoria.objects.filter(
            documento_id=documento_id
        ).select_related('usuario').order_by('-fecha_hora')
