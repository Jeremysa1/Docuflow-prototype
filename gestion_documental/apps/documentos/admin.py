from django.contrib import admin
from apps.documentos.models import Documento, Categoria


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'programa', 'categoria', 'autor', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'programa', 'categoria', 'es_compartido', 'es_sensible')
    search_fields = ('titulo', 'descripcion')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
