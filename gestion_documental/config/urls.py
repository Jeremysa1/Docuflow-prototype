"""
Configuración de URLs principales del proyecto.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.generic import RedirectView
from django.conf.urls.static import static

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

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
