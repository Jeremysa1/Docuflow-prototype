from django.contrib import admin
from unfold.admin import ModelAdmin
from core.admin_mixins import AdminSimpleSubmitMixin
from apps.permisos.models import PermisoDocumento, SolicitudAcceso, VotoAccesoSensible


@admin.register(PermisoDocumento)
class PermisoDocumentoAdmin(AdminSimpleSubmitMixin, ModelAdmin):
    list_display = ('usuario', 'documento', 'puede_ver', 'puede_descargar', 'otorgado_en', 'otorgado_por')
    list_filter = ('puede_ver', 'puede_descargar')
    search_fields = ('usuario__username', 'documento__titulo')


@admin.register(SolicitudAcceso)
class SolicitudAccesoAdmin(AdminSimpleSubmitMixin, ModelAdmin):
    list_display = ('solicitante', 'documento', 'estado', 'fecha_solicitud', 'respondido_por')
    list_filter = ('estado',)
    search_fields = ('solicitante__username', 'documento__titulo')


@admin.register(VotoAccesoSensible)
class VotoAccesoSensibleAdmin(AdminSimpleSubmitMixin, ModelAdmin):
    list_display = ('solicitud', 'votante', 'voto', 'fecha_voto')
    list_filter = ('voto',)
