from django.contrib import admin
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin
from core.admin_mixins import AdminSimpleSubmitMixin
from apps.usuarios.models import Usuario, ProgramaAcademico


# Los grupos de Django no se usan (el acceso se controla con Usuario.rol),
# así que se ocultan del índice del admin.
admin.site.unregister(Group)


@admin.register(ProgramaAcademico)
class ProgramaAcademicoAdmin(AdminSimpleSubmitMixin, ModelAdmin):
    list_display = ('codigo', 'nombre')
    search_fields = ('nombre', 'codigo')


@admin.register(Usuario)
class UsuarioAdmin(AdminSimpleSubmitMixin, ModelAdmin):
    list_display = ('username', 'get_full_name', 'rol', 'programa_academico', 'is_active')
    list_filter = ('rol', 'programa_academico', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    # H3: los tokens de recuperación nunca se muestran ni editan en el admin
    exclude = ('token_recuperacion', 'token_expiracion', 'token_intentos')
