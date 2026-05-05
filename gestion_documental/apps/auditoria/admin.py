from django.contrib import admin
from apps.auditoria.models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'accion', 'documento', 'fecha_hora', 'ip_address')
    list_filter = ('accion', 'fecha_hora')
    search_fields = ('usuario__username', 'detalle', 'documento__titulo')
    readonly_fields = ('fecha_hora',)
