"""
Context processors de usuarios.

`navegacion` arma los destinos del shell (riel lateral y barra móvil) según el rol,
con la misma regla de permisos que aplican las vistas: lo que el rol no puede abrir,
no aparece.
"""
from django.urls import reverse

# (clave, etiqueta, icono, nombre de URL, roles, grupo, en_barra_movil)
_DESTINOS = [
    ('panel', 'Panel', 'layout-dashboard', 'documentos:dashboard', None, 'trabajo', True),
    ('mis_documentos', 'Mis evidencias', 'folder-open', 'documentos:mis_documentos', None, 'trabajo', True),
    ('subir', 'Subir evidencia', 'upload', 'documentos:subir', None, 'trabajo', False),
    ('busqueda', 'Buscar', 'search', 'documentos:busqueda', None, 'trabajo', True),
    ('aprobar', 'Por revisar', 'clipboard-check', 'documentos:aprobar', ('DECANA', 'COORDINADOR'), 'revision', True),
    ('solicitudes', 'Solicitudes de acceso', 'key-round', 'permisos:solicitudes', ('DECANA', 'COORDINADOR'), 'revision', False),
    ('factores_cna', 'Factores CNA', 'grid-3x3', 'documentos:factores_cna', ('DECANA',), 'acreditacion', False),
    ('auditoria', 'Auditoría', 'shield', 'auditoria:lista', ('DECANA', 'COORDINADOR'), 'acreditacion', False),
    ('usuarios', 'Usuarios', 'users', 'usuarios:gestion_usuarios', ('DECANA',), 'acreditacion', False),
    ('papelera', 'Papelera', 'archive', 'documentos:papelera', None, 'otros', False),
]

_GRUPOS = [
    ('trabajo', 'Trabajo'),
    ('revision', 'Revisión'),
    ('acreditacion', 'Acreditación'),
    ('otros', ''),
]

# Etiquetas cortas para la barra inferior móvil (una sola línea en 375 px).
_CORTAS = {'mis_documentos': 'Evidencias', 'aprobar': 'Revisar'}

# Rutas cuyo destino activo no coincide con su propio nombre de URL.
_ALIAS_ACTIVO = {
    'lista': 'busqueda',
    'detalle': 'busqueda',
    'editar': 'mis_documentos',
    'aprobar_doc': 'aprobar',
    'gestionar_accesos': 'mis_documentos',
}


def _activo(request):
    match = getattr(request, 'resolver_match', None)
    if not match:
        return None
    if match.namespace == 'auditoria':
        return 'auditoria'
    if match.namespace == 'versiones':
        return 'mis_documentos'
    if match.namespace == 'usuarios' and match.url_name == 'gestion_usuarios':
        return 'usuarios'
    if match.url_name == 'dashboard':
        return 'panel'
    return _ALIAS_ACTIVO.get(match.url_name, match.url_name)


def navegacion(request):
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {}
    rol = getattr(user, 'rol', None)
    activo = _activo(request)

    destinos = []
    for clave, etiqueta, icono, url, roles, grupo, movil in _DESTINOS:
        if roles and rol not in roles:
            continue
        destinos.append({
            'clave': clave, 'etiqueta': etiqueta, 'icono': icono, 'url': reverse(url),
            'corta': _CORTAS.get(clave, etiqueta),
            'grupo': grupo, 'movil': movil, 'activo': clave == activo,
        })

    grupos = [
        {'titulo': titulo, 'destinos': [d for d in destinos if d['grupo'] == clave]}
        for clave, titulo in _GRUPOS
    ]
    movil = [d for d in destinos if d['movil']][:4]
    resto = [d for d in destinos if d not in movil]
    return {
        'nav_grupos': [g for g in grupos if g['destinos']],
        'nav_movil': movil,
        'nav_mas': resto,
        'nav_mas_activo': any(d['activo'] for d in resto),
    }
