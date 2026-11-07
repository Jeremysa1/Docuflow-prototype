import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
"""
Test completo - ejecutar con: py manage.py shell -c "exec(open('scripts/qa/qa_accesos.py').read())"
"""
from django.test import Client
from django.conf import settings
from django.contrib.auth import authenticate
from apps.usuarios.models import Usuario
from apps.documentos.models import Documento
from apps.permisos.models import PermisoDocumento, SolicitudAcceso, VotoAccesoSensible
from apps.permisos.services import PermisoService
from apps.notificaciones.models import Notificacion

if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

results = {}

def make_client(email, password):
    """Crea un Client autenticado usando force_login."""
    c = Client()
    user = Usuario.objects.get(email=email)
    c.force_login(user)
    return c

# PASO 0
print("=" * 60)
print("PASO 0 - RECONOCIMIENTO")
print("=" * 60)

jeremy = Usuario.objects.get(email='jeremy.sanchez@campusucc.edu.co')
test_user = Usuario.objects.get(email='test@campusucc.edu.co')
decana = Usuario.objects.get(email='decana@campusucc.edu.co')

docs = Documento.objects.filter(autor=jeremy)
for doc in docs:
    print("  ID=%d | %s | vis=%s | sensible=%s | estado=%s" % (doc.id, doc.titulo, doc.visibilidad, doc.es_sensible, doc.estado))

docs_normales = list(docs.filter(es_sensible=False).order_by('id'))
docs_sensibles = list(docs.filter(es_sensible=True).order_by('id'))
doc_aprobar = docs_normales[0] if docs_normales else None
doc_sensible = docs_sensibles[0] if docs_sensibles else None
doc_sensible2 = docs_sensibles[1] if len(docs_sensibles) > 1 else None

print("  doc_aprobar: %s" % (("ID=%d %s" % (doc_aprobar.id, doc_aprobar.titulo)) if doc_aprobar else "NINGUNO"))
print("  doc_sensible: %s" % (("ID=%d %s" % (doc_sensible.id, doc_sensible.titulo)) if doc_sensible else "NINGUNO"))
print("  jeremy prog: %s" % jeremy.programa_academico)
print("  test prog: %s" % test_user.programa_academico)
print("  mismo prog: %s" % (jeremy.programa_academico == test_user.programa_academico))

SolicitudAcceso.objects.all().delete()
PermisoDocumento.objects.filter(usuario=test_user).delete()
VotoAccesoSensible.objects.all().delete()
print("  Estado limpio: OK")

# PASO 1
print("\n" + "=" * 60)
print("PASO 1 - VISIBILIDAD EN BUSQUEDA")
print("=" * 60)
c = make_client('test@campusucc.edu.co', 'Admin123!')
resp = c.get('/documentos/busqueda/')
print("  Busqueda status: %d" % resp.status_code)
for doc in docs:
    tiene = PermisoService.usuario_tiene_acceso(test_user, doc)
    print("  %s: acceso=%s vis=%s" % (doc.titulo, tiene, doc.visibilidad))
results['paso1'] = resp.status_code == 200
print("  RESULTADO: %s" % ("OK" if results['paso1'] else "FALLO"))

# PASO 2
print("\n" + "=" * 60)
print("PASO 2 - SOLICITUD DOC NORMAL")
print("=" * 60)
if doc_aprobar:
    c = make_client('test@campusucc.edu.co', 'Admin123!')
    resp = c.post('/permisos/%d/solicitar/' % doc_aprobar.id, {'motivo': 'Necesito este doc para acreditacion.'})
    print("  POST status: %d redirect: %s" % (resp.status_code, resp.get('Location', 'N/A')))
    sol = SolicitudAcceso.objects.filter(documento=doc_aprobar, solicitante=test_user).first()
    if sol:
        print("  Solicitud: ID=%d estado=%s" % (sol.id, sol.estado))
        results['paso2'] = True
    else:
        print("  ERROR: No se creo solicitud")
        results['paso2'] = False
    notif = Notificacion.objects.filter(usuario=jeremy, documento=doc_aprobar).order_by('-fecha_creacion').first()
    print("  Notif jeremy: %s" % ("SI - %s" % notif.mensaje if notif else "NO"))
else:
    print("  SKIP: No hay doc normal")
    results['paso2'] = False
print("  RESULTADO: %s" % ("OK" if results['paso2'] else "FALLO"))

# PASO 3
print("\n" + "=" * 60)
print("PASO 3 - JEREMY APRUEBA")
print("=" * 60)
if doc_aprobar:
    sol = SolicitudAcceso.objects.filter(documento=doc_aprobar, solicitante=test_user, estado='PENDIENTE').first()
    if sol:
        c = make_client('jeremy.sanchez@campusucc.edu.co', 'Admin1234!')
        resp_get = c.get('/permisos/%d/accesos/' % doc_aprobar.id)
        print("  Gestionar accesos: %d" % resp_get.status_code)
        resp = c.post('/permisos/solicitud/%d/responder/' % sol.id, {'decision': 'APROBADA'})
        print("  Aprobacion POST: %d" % resp.status_code)
        permiso = PermisoDocumento.objects.filter(usuario=test_user, documento=doc_aprobar).first()
        sol.refresh_from_db()
        print("  Estado solicitud: %s" % sol.estado)
        if permiso:
            print("  Permiso: ver=%s descargar=%s" % (permiso.puede_ver, permiso.puede_descargar))
        else:
            print("  Permiso: NO CREADO")
        results['paso3'] = sol.estado == 'APROBADA' and permiso is not None
    else:
        print("  ERROR: No hay solicitud pendiente")
        results['paso3'] = False
else:
    results['paso3'] = False
print("  RESULTADO: %s" % ("OK" if results['paso3'] else "FALLO"))

# PASO 4
print("\n" + "=" * 60)
print("PASO 4 - TEST VE DOC APROBADO")
print("=" * 60)
if doc_aprobar:
    tiene = PermisoService.usuario_tiene_acceso(test_user, doc_aprobar)
    print("  Servicio acceso: %s" % tiene)
    c = make_client('test@campusucc.edu.co', 'Admin123!')
    resp = c.get('/documentos/%d/' % doc_aprobar.id)
    print("  Detalle: %d" % resp.status_code)
    results['paso4'] = tiene and resp.status_code == 200
else:
    results['paso4'] = False
print("  RESULTADO: %s" % ("OK" if results['paso4'] else "FALLO"))

# PASO 5
print("\n" + "=" * 60)
print("PASO 5 - RECHAZO DE SOLICITUD")
print("=" * 60)
doc_rechazar = doc_sensible2 if doc_sensible2 else doc_sensible
if doc_rechazar:
    orig_sensible = doc_rechazar.es_sensible
    doc_rechazar.es_sensible = False
    doc_rechazar.save(update_fields=['es_sensible'])
    print("  Doc: %s (ID=%d) temp no-sensible" % (doc_rechazar.titulo, doc_rechazar.id))
    SolicitudAcceso.objects.filter(solicitante=test_user, documento=doc_rechazar).delete()
    c = make_client('test@campusucc.edu.co', 'Admin123!')
    c.post('/permisos/%d/solicitar/' % doc_rechazar.id, {'motivo': 'Prueba rechazo.'})
    sol = SolicitudAcceso.objects.filter(documento=doc_rechazar, solicitante=test_user, estado='PENDIENTE').first()
    print("  Solicitud: %s" % ("ID=%d" % sol.id if sol else "NO"))
    if sol:
        c2 = make_client('jeremy.sanchez@campusucc.edu.co', 'Admin1234!')
        c2.post('/permisos/solicitud/%d/responder/' % sol.id, {'decision': 'RECHAZADA', 'motivo_rechazo': 'No puede ser compartido.'})
        sol.refresh_from_db()
        print("  Estado: %s motivo: %s" % (sol.estado, sol.motivo_rechazo))
        perm = PermisoDocumento.objects.filter(usuario=test_user, documento=doc_rechazar).exists()
        print("  Permiso: %s (debe ser False)" % perm)
        results['paso5'] = sol.estado == 'RECHAZADA' and not perm
    else:
        results['paso5'] = False
    doc_rechazar.es_sensible = orig_sensible
    doc_rechazar.save(update_fields=['es_sensible'])
else:
    results['paso5'] = False
print("  RESULTADO: %s" % ("OK" if results['paso5'] else "FALLO"))

# PASO 6
print("\n" + "=" * 60)
print("PASO 6 - SENSIBLE: 2/3 APROBACIONES")
print("=" * 60)
if doc_sensible:
    print("  Doc: %s (ID=%d)" % (doc_sensible.titulo, doc_sensible.id))
    SolicitudAcceso.objects.filter(documento=doc_sensible).delete()
    PermisoDocumento.objects.filter(usuario=test_user, documento=doc_sensible).delete()
    VotoAccesoSensible.objects.all().delete()
    c = make_client('test@campusucc.edu.co', 'Admin123!')
    c.post('/permisos/%d/solicitar/' % doc_sensible.id, {'motivo': 'Acceso sensible acreditacion.'})
    sol = SolicitudAcceso.objects.filter(documento=doc_sensible, solicitante=test_user).first()
    print("  Solicitud: %s" % ("ID=%d estado=%s" % (sol.id, sol.estado) if sol else "NO"))
    if sol:
        c1 = make_client('jeremy.sanchez@campusucc.edu.co', 'Admin1234!')
        c1.post('/permisos/solicitud/%d/responder/' % sol.id, {'decision': 'APROBADA'})
        v = VotoAccesoSensible.objects.filter(solicitud=sol).count()
        sol.refresh_from_db()
        p = PermisoDocumento.objects.filter(usuario=test_user, documento=doc_sensible).exists()
        print("  Voto1 jeremy: votos=%d estado=%s permiso=%s" % (v, sol.estado, p))
        c2 = make_client('decana@campusucc.edu.co', 'Admin123!')
        c2.post('/permisos/solicitud/%d/responder/' % sol.id, {'decision': 'APROBADA'})
        v = VotoAccesoSensible.objects.filter(solicitud=sol).count()
        sol.refresh_from_db()
        p = PermisoDocumento.objects.filter(usuario=test_user, documento=doc_sensible).first()
        print("  Voto2 decana: votos=%d estado=%s permiso=%s" % (v, sol.estado, "SI" if p else "NO"))
        results['paso6'] = sol.estado == 'APROBADA' and p is not None
    else:
        results['paso6'] = False
else:
    results['paso6'] = False
print("  RESULTADO: %s" % ("OK" if results['paso6'] else "FALLO"))

# PASO 7
print("\n" + "=" * 60)
print("PASO 7 - SENSIBLE: RECHAZO INMEDIATO")
print("=" * 60)
if doc_sensible:
    SolicitudAcceso.objects.filter(documento=doc_sensible).delete()
    PermisoDocumento.objects.filter(usuario=test_user, documento=doc_sensible).delete()
    VotoAccesoSensible.objects.all().delete()
    c = make_client('test@campusucc.edu.co', 'Admin123!')
    c.post('/permisos/%d/solicitar/' % doc_sensible.id, {'motivo': 'Prueba rechazo sensible.'})
    sol = SolicitudAcceso.objects.filter(documento=doc_sensible, solicitante=test_user, estado='PENDIENTE').first()
    print("  Solicitud: %s" % ("ID=%d" % sol.id if sol else "NO"))
    if sol:
        c1 = make_client('jeremy.sanchez@campusucc.edu.co', 'Admin1234!')
        c1.post('/permisos/solicitud/%d/responder/' % sol.id, {'decision': 'APROBADA'})
        sol.refresh_from_db()
        print("  Tras jeremy aprueba: %s" % sol.estado)
        c2 = make_client('decana@campusucc.edu.co', 'Admin123!')
        c2.post('/permisos/solicitud/%d/responder/' % sol.id, {'decision': 'RECHAZADA', 'motivo_rechazo': 'Politicas institucionales.'})
        sol.refresh_from_db()
        p = PermisoDocumento.objects.filter(usuario=test_user, documento=doc_sensible).exists()
        print("  Tras decana rechaza: estado=%s permiso=%s" % (sol.estado, p))
        results['paso7'] = sol.estado == 'RECHAZADA' and not p
    else:
        results['paso7'] = False
else:
    results['paso7'] = False
print("  RESULTADO: %s" % ("OK" if results['paso7'] else "FALLO"))

# PASO 8
print("\n" + "=" * 60)
print("PASO 8 - REVOCACION DE ACCESO")
print("=" * 60)
if doc_aprobar:
    PermisoDocumento.objects.get_or_create(usuario=test_user, documento=doc_aprobar, defaults={'puede_ver': True, 'puede_descargar': True, 'otorgado_por': jeremy})
    print("  Permiso existe: SI")
    c = make_client('jeremy.sanchez@campusucc.edu.co', 'Admin1234!')
    resp = c.post('/permisos/%d/usuario/%d/revocar/' % (doc_aprobar.id, test_user.id))
    print("  Revocacion: %d" % resp.status_code)
    p = PermisoDocumento.objects.filter(usuario=test_user, documento=doc_aprobar).exists()
    print("  Permiso post: %s" % p)
    results['paso8'] = not p
else:
    results['paso8'] = False
print("  RESULTADO: %s" % ("OK" if results['paso8'] else "FALLO"))

# PASO 9
print("\n" + "=" * 60)
print("PASO 9 - SEGURIDAD")
print("=" * 60)
paso9 = True
if doc_sensible:
    SolicitudAcceso.objects.filter(documento=doc_sensible).delete()
    VotoAccesoSensible.objects.all().delete()
    c = make_client('test@campusucc.edu.co', 'Admin123!')
    c.post('/permisos/%d/solicitar/' % doc_sensible.id, {'motivo': 'Prueba doble voto.'})
    sol = SolicitudAcceso.objects.filter(documento=doc_sensible, solicitante=test_user, estado='PENDIENTE').first()
    if sol:
        c1 = make_client('jeremy.sanchez@campusucc.edu.co', 'Admin1234!')
        c1.post('/permisos/solicitud/%d/responder/' % sol.id, {'decision': 'APROBADA'})
        c1.post('/permisos/solicitud/%d/responder/' % sol.id, {'decision': 'APROBADA'})
        votos = VotoAccesoSensible.objects.filter(solicitud=sol, votante=jeremy).count()
        print("  Doble voto jeremy: %d (debe ser 1)" % votos)
        if votos != 1:
            paso9 = False
results['paso9'] = paso9
print("  RESULTADO: %s" % ("OK" if results['paso9'] else "FALLO"))

# REPORTE
print("\n" + "=" * 60)
print("REPORTE FINAL")
print("=" * 60)
labels = {'paso1': 'Visibilidad busqueda', 'paso2': 'Solicitud normal', 'paso3': 'Jeremy aprueba', 'paso4': 'Test ve doc', 'paso5': 'Rechazo solicitud', 'paso6': 'Sensible 2/3', 'paso7': 'Sensible rechazo', 'paso8': 'Revocacion', 'paso9': 'Seguridad'}
total = 0
for k in sorted(results.keys()):
    s = "OK" if results[k] else "FALLO"
    if results[k]:
        total += 1
    print("  %-30s %s" % (labels.get(k, k), s))
print("\nTOTAL: %d/%d pruebas pasaron" % (total, len(results)))
if total < len(results):
    print("\nERRORES:")
    for k in sorted(results.keys()):
        if not results[k]:
            print("  - %s" % labels.get(k, k))
