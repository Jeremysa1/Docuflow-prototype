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
            detalle=detalle,
        )

    @staticmethod
    def _get_client_ip(request):
        """Obtiene la dirección IP del cliente desde el request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
