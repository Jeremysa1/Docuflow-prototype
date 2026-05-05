from django.contrib import admin
from apps.usuarios.models import Usuario, ProgramaAcademico


@admin.register(ProgramaAcademico)
class ProgramaAcademicoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre')
    search_fields = ('nombre', 'codigo')


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'get_full_name', 'rol', 'programa_academico', 'is_active')
    list_filter = ('rol', 'programa_academico', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
