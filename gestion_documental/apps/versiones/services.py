"""
Servicios del módulo de versiones.

Contiene toda la lógica de negocio relacionada con el control de versiones de documentos.

A1: la versión creada o restaurada pasa a ser el archivo vigente del documento.
Si la sube un docente sobre un documento aprobado o rechazado, vuelve a revisión.
"""
import logging
import os

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Max

from apps.documentos.models import Documento
from apps.notificaciones.services import NotificacionService
from apps.versiones.models import Version
from core.cache_stats import bump_stats
from core.services.audit_service import AuditService

logger = logging.getLogger(__name__)

DESCRIPCION_INICIAL = 'Versión inicial cargada por el autor.'


class VersionService:
    """Servicio para la gestión de versiones de documentos."""

    # ─── Helpers internos (llamar dentro de transaction.atomic) ──────────

    @staticmethod
    def _bloquear_documento(documento_id):
        """Bloquea la fila del documento: serializa la numeración de versiones."""
        return Documento.objects.select_for_update().get(pk=documento_id)

    @staticmethod
    def _asegurar_version_inicial(documento):
        """Si el documento aún no tiene versiones, guarda su archivo original como v1.

        Sin esto, al reemplazar el archivo vigente el original quedaría inaccesible.
        """
        if Version.objects.filter(documento=documento).exists() or not documento.archivo:
            return None
        try:
            with documento.archivo.open('rb') as original:
                contenido = original.read()
        except (FileNotFoundError, OSError):
            logger.warning('Documento %s sin archivo físico; no se crea la v1.', documento.pk)
            return None
        nombre = os.path.basename(documento.archivo.name)
        return Version.objects.create(
            documento=documento,
            archivo=ContentFile(contenido, name=nombre),
            numero_version=1,
            descripcion_cambio=DESCRIPCION_INICIAL,
            autor=documento.autor,
        )

    @staticmethod
    def _siguiente_numero(documento):
        ultimo = Version.objects.filter(documento=documento).aggregate(m=Max('numero_version'))['m']
        return (ultimo or 0) + 1

    @staticmethod
    def _aplicar_cambio_vigente(documento, version, usuario):
        """Fija el archivo vigente y aplica la regla de revisión. Devuelve True si pasó a PENDIENTE."""
        documento.archivo.name = version.archivo.name
        paso_a_pendiente = (
            usuario.rol == 'DOCENTE_PLANTA'
            and documento.estado in (Documento.Estado.APROBADO, Documento.Estado.RECHAZADO)
        )
        if paso_a_pendiente:
            documento.estado = Documento.Estado.PENDIENTE
        documento.save(update_fields=['archivo', 'estado', 'fecha_modificacion'])
        return paso_a_pendiente

    @staticmethod
    def _notificar_si_requiere_revision(documento, usuario, mensaje):
        if documento.estado == Documento.Estado.PENDIENTE and usuario.rol == 'DOCENTE_PLANTA':
            NotificacionService.notificar_revisores(documento, mensaje, actor=usuario)

    # ─── API pública ─────────────────────────────────────────────────────

    @staticmethod
    def crear_version(documento_id, archivo, descripcion_cambio, autor, request=None):
        """Crea una versión nueva y la deja como archivo vigente del documento."""
        from core.utils.helpers import validar_archivo_subido
        validar_archivo_subido(archivo)

        with transaction.atomic():
            documento = VersionService._bloquear_documento(documento_id)
            VersionService._asegurar_version_inicial(documento)
            version = Version.objects.create(
                documento=documento,
                archivo=archivo,
                numero_version=VersionService._siguiente_numero(documento),
                descripcion_cambio=descripcion_cambio,
                autor=autor,
            )
            paso_a_pendiente = VersionService._aplicar_cambio_vigente(documento, version, autor)
            AuditService.log(
                usuario=autor, accion='NUEVA_VERSION', documento=documento, request=request,
                detalle=(f"Versión {version.numero_version}"
                         + ("; el documento volvió a revisión" if paso_a_pendiente else "")),
            )
            VersionService._notificar_si_requiere_revision(
                documento, autor,
                f"{autor.get_full_name()} subió la versión {version.numero_version} de "
                f"'{documento.titulo}' y requiere tu revisión.",
            )
        bump_stats()
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
    def restaurar_version(version_id, usuario, request=None):
        """Copia una versión anterior como versión nueva y la deja vigente."""
        from core.utils.helpers import validar_archivo_subido

        with transaction.atomic():
            version = Version.objects.select_related('documento').get(pk=version_id)
            documento = VersionService._bloquear_documento(version.documento_id)

            # Copia física: la versión restaurada es un archivo nuevo e independiente.
            with version.archivo.open('rb') as origen:
                archivo_copia = ContentFile(
                    origen.read(), name=f"restored_{os.path.basename(version.archivo.name)}"
                )
            # R2-04: misma política que al crear — nada bloqueado/sobredimensionado vuelve al doc vivo
            validar_archivo_subido(archivo_copia)

            nueva_version = Version.objects.create(
                documento=documento,
                archivo=archivo_copia,
                numero_version=VersionService._siguiente_numero(documento),
                descripcion_cambio=f"Restaurado desde v{version.numero_version}",
                autor=usuario,
            )
            paso_a_pendiente = VersionService._aplicar_cambio_vigente(documento, nueva_version, usuario)
            AuditService.log(
                usuario=usuario, accion='MODIFICO', documento=documento, request=request,
                detalle=(f"Restauró la versión {version.numero_version} como v{nueva_version.numero_version}"
                         + ("; el documento volvió a revisión" if paso_a_pendiente else "")),
            )
            VersionService._notificar_si_requiere_revision(
                documento, usuario,
                f"{usuario.get_full_name()} restauró una versión de '{documento.titulo}' y requiere tu revisión.",
            )
        bump_stats()
        return nueva_version
