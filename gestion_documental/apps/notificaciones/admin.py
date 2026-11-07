from django.contrib import admin
from unfold.admin import ModelAdmin
from core.admin_mixins import AdminSimpleSubmitMixin
from apps.notificaciones.models import Notificacion


@admin.register(Notificacion)
class NotificacionAdmin(AdminSimpleSubmitMixin, ModelAdmin):
    list_display = ('usuario', 'tipo', 'mensaje', 'leida', 'fecha_creacion')
    list_filter = ('tipo', 'leida', 'fecha_creacion')
    search_fields = ('mensaje', 'usuario__username')
    readonly_fields = ('fecha_creacion',)
