"""
AuditService - Servicio transversal de auditoría.

Proporciona un punto de acceso centralizado para registrar auditorías
desde cualquier módulo del sistema.
"""
from apps.auditoria.models import RegistroAuditoria


class AuditService:
    """Servicio transversal de auditoría."""

    @staticmethod
    def log(usuario, accion, documento=None, request=None, detalle=''):
        """
        Registra una acción en el log de auditoría.

        Args:
            usuario: Instancia del usuario que realizó la acción
            accion: Tipo de acción (usar RegistroAuditoria.Accion choices)
            documento: Documento relacionado (opcional)
            request: Request HTTP para obtener IP (opcional)
            detalle: Texto descriptivo adicional
        """
        ip_address = None
        if request:
            ip_address = AuditService._get_client_ip(request)

        return RegistroAuditoria.objects.create(
            usuario=usuario,
            accion=accion,
            documento=documento,
            ip_address=ip_address,
            detalle=detalle or '',
        )

    @staticmethod
    def _get_client_ip(request):
        """IP confiable y validada (C3): ver core.utils.helpers.obtener_ip_cliente."""
        from core.utils.helpers import obtener_ip_cliente
        return obtener_ip_cliente(request)
