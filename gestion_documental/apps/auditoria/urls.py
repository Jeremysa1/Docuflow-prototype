"""URLs del módulo de auditoría."""
from django.urls import path
# pyrefly: ignore [missing-import]
from apps.auditoria import views

app_name = 'auditoria'

urlpatterns = [
    path('', views.lista_auditoria, name='lista'),
    path('exportar/excel/', views.exportar_auditoria_excel, name='exportar_excel'),
    path('exportar/pdf/', views.exportar_auditoria_pdf, name='exportar_pdf'),
]
