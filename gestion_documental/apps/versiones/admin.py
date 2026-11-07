from django.contrib import admin
from unfold.admin import ModelAdmin
from core.admin_mixins import AdminSimpleSubmitMixin
from apps.versiones.models import Version


@admin.register(Version)
class VersionAdmin(AdminSimpleSubmitMixin, ModelAdmin):
    list_display = ('documento', 'numero_version', 'autor', 'fecha_creacion')
    list_filter = ('fecha_creacion',)
    search_fields = ('documento__titulo', 'descripcion_cambio')
    readonly_fields = ('fecha_creacion',)
