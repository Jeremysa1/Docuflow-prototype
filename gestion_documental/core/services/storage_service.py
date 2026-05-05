"""
StorageService - Abstracción del almacenamiento de archivos.

Encapsula FileSystemStorage para que en el futuro cambiar a S3
solo requiera modificar esta clase.

Ruta de guardado: docs/{programa_codigo}/{categoria_nombre}/{timestamp}_{filename}
"""
import os
from datetime import datetime

from django.core.files.storage import default_storage
from django.conf import settings


class StorageService:
    """Servicio de almacenamiento de archivos."""

    @staticmethod
    def save_document(file, programa, categoria):
        """
        Guarda un documento en el sistema de archivos.

        Args:
            file: Archivo subido (InMemoryUploadedFile o TemporaryUploadedFile)
            programa: Instancia de ProgramaAcademico
            categoria: Instancia de Categoria

        Returns:
            str: Ruta relativa del archivo guardado
        """
        # Construir la ruta: docs/{programa_codigo}/{categoria_nombre}/{timestamp}_{filename}
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = file.name.replace(' ', '_')
        safe_categoria = categoria.nombre.replace(' ', '_').lower()
        safe_programa = programa.codigo.lower()

        relative_path = os.path.join(
            'docs',
            safe_programa,
            safe_categoria,
            f"{timestamp}_{filename}"
        )

        # Guardar usando el storage backend configurado
        saved_path = default_storage.save(relative_path, file)
        return saved_path

    @staticmethod
    def delete_document(path):
        """
        Elimina un archivo del sistema de almacenamiento.

        Args:
            path: Ruta relativa del archivo a eliminar
        """
        if path and default_storage.exists(path):
            default_storage.delete(path)

    @staticmethod
    def get_document_url(path):
        """
        Obtiene la URL pública de un documento.

        Args:
            path: Ruta relativa del archivo

        Returns:
            str: URL del archivo
        """
        if path and default_storage.exists(path):
            return default_storage.url(path)
        return None

    @staticmethod
    def file_exists(path):
        """Verifica si un archivo existe."""
        return default_storage.exists(path)
