"""URLs del módulo de versiones."""
from django.urls import path
from apps.versiones import views

app_name = 'versiones'

urlpatterns = [
    path('<int:documento_id>/', views.lista_versiones, name='lista'),
    path('<int:documento_id>/crear/', views.crear_version, name='crear'),
    path('<int:version_id>/restaurar/', views.restaurar_version_view, name='restaurar'),
]
