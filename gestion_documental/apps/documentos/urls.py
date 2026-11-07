"""URLs del módulo de documentos."""
from django.urls import path
from . import views

app_name = 'documentos'

urlpatterns = [
    path('', views.busqueda_avanzada_view, name='lista'), # Alias for compatibility
    path('busqueda/', views.busqueda_avanzada_view, name='busqueda'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('mis-documentos/', views.mis_documentos_view, name='mis_documentos'),
    path('aprobar/', views.aprobar_documentos_view, name='aprobar'),
    path('subir/', views.subir_documento, name='subir'),
    path('aprobar-lote/', views.aprobar_documentos_lote, name='aprobar_lote'),
    path('papelera/', views.papelera_documentos, name='papelera'),
    path('<int:documento_id>/restaurar/', views.restaurar_documento, name='restaurar_doc'),
    path('<int:documento_id>/', views.detalle_documento, name='detalle'),
    path('<int:documento_id>/editar/', views.editar_documento, name='editar'),
    path('<int:documento_id>/eliminar/', views.eliminar_documento, name='eliminar'),
    path('<int:documento_id>/aprobar/', views.aprobar_documento, name='aprobar_doc'),
    path('<int:documento_id>/rechazar/', views.rechazar_documento, name='rechazar_doc'), # Kept param name as in views.py but changed name
    path('<int:documento_id>/descargar/', views.descargar_documento_view, name='descargar_doc'),
    path('<int:documento_id>/vista-previa/', views.previsualizar_documento, name='vista_previa'),
    path('version/<int:ver_id>/descargar/', views.descargar_version_view, name='descargar_version'),
    path('factores-cna/', views.factores_cna_view, name='factores_cna'),
    path('factores-cna/exportar/excel/', views.exportar_factores_excel, name='exportar_factores_excel'),
    path('factores-cna/exportar/pdf/', views.exportar_factores_pdf, name='exportar_factores_pdf'),
    path('api/buscar/', views.buscar_documentos_ajax, name='buscar_ajax'),
]
