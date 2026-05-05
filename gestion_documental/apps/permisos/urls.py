"""URLs del módulo de permisos."""
from django.urls import path
from apps.permisos import views

app_name = 'permisos'

urlpatterns = [
    # Gestionar accesos de un documento
    path('<int:doc_id>/accesos/', views.gestionar_accesos_view, name='gestionar_accesos'),

    # Responder solicitud (aprobar/rechazar o votar sensible)
    path('solicitud/<int:solicitud_id>/responder/', views.responder_solicitud_view, name='responder_solicitud'),

    # Revocar acceso de un usuario a un documento
    path('<int:doc_id>/usuario/<int:usuario_id>/revocar/', views.revocar_acceso_view, name='revocar_acceso'),

    # Solicitar acceso a un documento
    path('<int:doc_id>/solicitar/', views.solicitar_acceso_view, name='solicitar_acceso'),

    # Vista legacy de solicitudes pendientes
    path('solicitudes/', views.listar_solicitudes_view, name='solicitudes'),
]
