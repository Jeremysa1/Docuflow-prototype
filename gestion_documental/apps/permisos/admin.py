from django.contrib import admin
from apps.permisos.models import PermisoDocumento, SolicitudAcceso, VotoAccesoSensible


@admin.register(PermisoDocumento)
class PermisoDocumentoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'documento', 'puede_ver', 'puede_descargar', 'otorgado_en', 'otorgado_por')
    list_filter = ('puede_ver', 'puede_descargar')
    search_fields = ('usuario__username', 'documento__titulo')


@admin.register(SolicitudAcceso)
class SolicitudAccesoAdmin(admin.ModelAdmin):
    list_display = ('solicitante', 'documento', 'estado', 'fecha_solicitud', 'respondido_por')
    list_filter = ('estado',)
    search_fields = ('solicitante__username', 'documento__titulo')


@admin.register(VotoAccesoSensible)
class VotoAccesoSensibleAdmin(admin.ModelAdmin):
    list_display = ('solicitud', 'votante', 'voto', 'fecha_voto')
    list_filter = ('voto',)
