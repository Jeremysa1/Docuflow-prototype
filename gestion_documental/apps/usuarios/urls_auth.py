"""URLs de autenticación del módulo de usuarios."""
from django.urls import path
from apps.usuarios import views

app_name = 'auth'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    path('recuperar/', views.recuperar_contrasena_view, name='recuperar_contrasena'),
    path('recuperar/confirmar/', views.confirmar_email_view, name='confirmar_email'),
    path('recuperar/token/', views.validar_token_view, name='validar_token'),
    path('recuperar/reenviar/', views.reenviar_token_view, name='reenviar_token'),
    path('recuperar/nueva-contrasena/', views.nueva_contrasena_view, name='nueva_contrasena'),
]
