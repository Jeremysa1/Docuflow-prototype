"""URLs de gestión de usuarios."""
from django.urls import path
from apps.usuarios import views

app_name = 'usuarios'

urlpatterns = [
    path('perfil/', views.perfil_view, name='perfil'),
    path('gestion/', views.gestion_usuarios_view, name='gestion_usuarios'),
    path('gestion/agregar/', views.agregar_usuario_view, name='agregar_usuario'),
    path('gestion/<int:uid>/habilitar/', views.habilitar_usuario_view, name='habilitar_usuario'),
    path('gestion/<int:uid>/deshabilitar/', views.deshabilitar_usuario_view, name='deshabilitar_usuario'),
    path('gestion/<int:uid>/eliminar/', views.eliminar_usuario_view, name='eliminar_usuario'),
    path('gestion/<int:uid>/editar/', views.editar_usuario_view, name='editar_usuario'),
]
