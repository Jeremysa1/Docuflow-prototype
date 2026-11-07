from django.contrib import admin
from unfold.admin import ModelAdmin
from core.admin_mixins import AdminSimpleSubmitMixin
from apps.auditoria.models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(AdminSimpleSubmitMixin, ModelAdmin):
    list_display = ('usuario', 'accion', 'documento', 'fecha_hora', 'ip_address')
    list_filter = ('accion', 'fecha_hora')
    search_fields = ('usuario__username', 'detalle', 'documento__titulo')
    readonly_fields = ('usuario', 'accion', 'documento', 'fecha_hora', 'ip_address', 'detalle')

    # H3: el log de auditoría es append-only
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
