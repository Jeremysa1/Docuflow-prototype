"""
Servicios del módulo de versiones.

Contiene toda la lógica de negocio relacionada con el control de versiones de documentos.
"""
from django.core.files.base import ContentFile
from apps.versiones.models import Version
from apps.documentos.models import Documento
from core.services.audit_service import AuditService
from apps.notificaciones.services import NotificacionService
from apps.usuarios.models import Usuario
from apps.documentos.models import Documento


class VersionService:
    """Servicio para la gestión de versiones de documentos."""

    @staticmethod
    def crear_version(documento_id, archivo, descripcion_cambio, autor):
        """
        Crea una nueva versión de un documento.
        Calcula automáticamente el número de versión siguiente.
        """
        documento = Documento.objects.get(pk=documento_id)

        # Obtener el siguiente número de versión
        ultima_version = Version.objects.filter(
            documento=documento
        ).order_by('-numero_version').first()

        numero = (ultima_version.numero_version + 1) if ultima_version else 1

        version = Version.objects.create(
            documento=documento,
            archivo=archivo,
            numero_version=numero,
            descripcion_cambio=descripcion_cambio,
            autor=autor,
        )
        return version

    @staticmethod
    def listar_versiones(documento_id):
        """Lista todas las versiones de un documento."""
        return Version.objects.filter(
            documento_id=documento_id
        ).select_related('autor').order_by('-numero_version')

    @staticmethod
    def obtener_version(version_id):
        """Obtiene una versión específica."""
        try:
            return Version.objects.select_related('documento', 'autor').get(pk=version_id)
        except Version.DoesNotExist:
            return None

    @staticmethod
    def restaurar_version(version_id, usuario):
        version = Version.objects.get(pk=version_id)
        documento = version.documento

        # Crear copia del archivo físico para la nueva versión y el doc
        archivo_copia = ContentFile(version.archivo.read(), name=f"restored_{version.archivo.name.split('/')[-1]}")

        # Siguiente numero
        ultima_version = Version.objects.filter(documento=documento).order_by('-numero_version').first()
        numero = (ultima_version.numero_version + 1) if ultima_version else 1

        # Crear version
        nueva_version = Version.objects.create(
            documento=documento,
            archivo=archivo_copia,
            numero_version=numero,
            descripcion_cambio=f"Restaurado desde v{version.numero_version}",
            autor=usuario
        )

        # Actualizar doc
        documento.archivo.save(archivo_copia.name, archivo_copia, save=True)
        documento.fecha_modificacion = nueva_version.fecha_creacion
        documento.save(update_fields=['fecha_modificacion'])

        # Auditoria
        AuditService.log(
            usuario=usuario, accion='MODIFICO', documento=documento,
            detalle=f"Restauró versión {version.numero_version}"
        )

        # Notificar a los coordinadores y decana si estaba pendiente o si lo cambió alguien más
        # (Simplified notification based on prompt)
        if documento.estado == 'PENDIENTE':
            coordinadores = Usuario.objects.filter(rol='COORDINADOR', programa_academico=documento.programa)
            for coord in coordinadores:
                NotificacionService.crear_notificacion(usuario=coord, mensaje=f"{usuario.get_full_name()} restauró versión de '{documento.titulo}'.", tipo='INFO', documento=documento)
        
        return nueva_version
