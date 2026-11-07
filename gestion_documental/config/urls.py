"""
Configuración de URLs principales del proyecto.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/login/', permanent=False), name='index'),
    path('admin/', admin.site.urls),

    # Auth — solo login, logout y recuperación
    path('login/', include('apps.usuarios.urls_auth')),

    # Usuarios — perfil y gestión
    path('usuarios/', include('apps.usuarios.urls_usuarios')),

    # Resto de apps
    path('documentos/', include('apps.documentos.urls')),
    path('versiones/', include('apps.versiones.urls')),
    path('permisos/', include('apps.permisos.urls')),
    path('notificaciones/', include('apps.notificaciones.urls')),
    path('auditoria/', include('apps.auditoria.urls')),

]

# A4 (Zero-Trust): MEDIA_ROOT no se sirve nunca por URL directa, ni en DEBUG.
# Los archivos solo salen por las vistas de descarga y vista previa, que validan permisos.
