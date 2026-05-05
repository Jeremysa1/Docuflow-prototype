"""URLs del módulo de auditoría."""
from django.urls import path
from apps.auditoria import views

app_name = 'auditoria'

urlpatterns = [
    path('', views.lista_auditoria, name='lista'),
    path('exportar/', views.exportar_auditoria, name='exportar'),
]
