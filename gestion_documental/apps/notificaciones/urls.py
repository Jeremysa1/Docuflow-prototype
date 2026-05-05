"""URLs del módulo de notificaciones."""
from django.urls import path
from apps.notificaciones import views

app_name = 'notificaciones'

urlpatterns = [
    path('', views.lista_notificaciones, name='lista'),
    path('<int:notificacion_id>/leida/', views.marcar_leida, name='marcar_leida'),
    path('marcar-todas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
]
