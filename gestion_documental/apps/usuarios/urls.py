"""URLs del módulo de usuarios."""
from django.urls import path
from apps.usuarios import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('recuperar/', views.recuperar_contrasena_view, name='recuperar_contrasena'),
    path('recuperar/confirmar/', views.confirmar_email_view, name='confirmar_email'),
    path('recuperar/token/', views.validar_token_view, name='validar_token'),
    path('recuperar/reenviar/', views.reenviar_token_view, name='reenviar_token'),
    path('recuperar/nueva-contrasena/', views.nueva_contrasena_view, name='nueva_contrasena'),
    path('gestion/', views.gestion_usuarios_view, name='gestion_usuarios'),
    # H5: ruta 'cambiar_estado' eliminada — apuntaba a una vista inexistente
    # (cambiar_estado_usuario_view). La gestión usa habilitar/deshabilitar/eliminar/editar.
]
