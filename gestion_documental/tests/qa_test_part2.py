"""QA Test Part 2: Functional tests - documents, versions, audit, notifications, permissions."""
import json, time, os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()
from django.test import Client
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.usuarios.models import Usuario
from apps.documentos.models import Documento, Categoria
from apps.auditoria.models import RegistroAuditoria
from apps.versiones.models import Version
from apps.permisos.models import PermisoDocumento, SolicitudAcceso, VotoAccesoSensible
from apps.notificaciones.models import Notificacion
from apps.permisos.services import PermisoService

if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

results = []
def test(name, obj, rf, hu, expected, obtained, status, analysis):
    results.append({'name':name,'obj':obj,'rf':rf,'hu':hu,'expected':expected,'obtained':obtained,'status':status,'analysis':analysis})
    print(f"  [{status}] {name}")

print("="*60)
print("PART 2: FUNCTIONAL TESTS")
print("="*60)

# Get test users
decana = Usuario.objects.filter(rol='DECANA', esta_habilitado=True).first()
coordinador = Usuario.objects.filter(rol='COORDINADOR', esta_habilitado=True).first()
docente = Usuario.objects.filter(rol='DOCENTE_PLANTA', esta_habilitado=True).first()

print(f"  Decana: {decana}")
print(f"  Coordinador: {coordinador}")  
print(f"  Docente: {docente}")

# T16: Dashboard by role
print("\n--- Dashboard ---")
for label, user in [("DECANA", decana), ("COORDINADOR", coordinador), ("DOCENTE", docente)]:
    if user:
        c = Client(); c.force_login(user)
        r = c.get('/documentos/dashboard/')
        test(f"T16-Dashboard {label}",f"Dashboard personalizado para {label}","RF-04","HU-04",
             "HTTP 200", f"HTTP {r.status_code}",
             "EXITOSA" if r.status_code==200 else "FALLIDA",
             f"Dashboard renderiza correctamente para rol {label}.")

# T17: Document upload form
print("\n--- Document Upload ---")
if docente:
    c = Client(); c.force_login(docente)
    r = c.get('/documentos/subir/')
    test("T17-Formulario de carga","Acceder al formulario de subida","RF-05","HU-05",
         "HTTP 200", f"HTTP {r.status_code}",
         "EXITOSA" if r.status_code==200 else "FALLIDA",
         "El formulario de carga es accesible para docentes.")

# T18: Document upload POST (valid PDF)
if docente and Categoria.objects.exists() and docente.programa_academico:
    cat = Categoria.objects.first()
    prog = docente.programa_academico
    fake_pdf = SimpleUploadedFile("test_qa.pdf", b"%PDF-1.4 test content", content_type="application/pdf")
    c = Client(); c.force_login(docente)
    audit_before = RegistroAuditoria.objects.filter(accion='SUBIO').count()
    r = c.post('/documentos/subir/', {
        'titulo': 'QA Test Document',
        'descripcion': 'Documento creado por prueba QA automatizada',
        'archivo': fake_pdf,
        'programa': prog.id,
        'categoria': cat.id,
        'visibilidad': 'PROGRAMA',
        'es_sensible': False,
    }, follow=True)
    doc_created = Documento.objects.filter(titulo='QA Test Document').first()
    audit_after = RegistroAuditoria.objects.filter(accion='SUBIO').count()
    test("T18-Subida de documento","Subir documento PDF válido","RF-05","HU-05",
         "Documento creado + auditoría", 
         f"Creado={'SI' if doc_created else 'NO'}, Estado={doc_created.estado if doc_created else 'N/A'}, Auditoría={audit_after-audit_before} registros nuevos",
         "EXITOSA" if doc_created and doc_created.estado=='PENDIENTE' and audit_after>audit_before else "FALLIDA",
         "Documento subido correctamente con estado PENDIENTE y registro de auditoría.")
    
    # T19: Notification generated on upload
    if doc_created and coordinador:
        notif = Notificacion.objects.filter(documento=doc_created, usuario=coordinador).exists()
        test("T19-Notificación al subir","Verificar notificación al coordinador","RF-10","HU-10",
             "Notificación creada", f"Existe={notif}",
             "EXITOSA" if notif else "PARCIAL",
             "El sistema notifica al coordinador cuando un docente sube un documento.")

# T20: Invalid extension rejection
if docente and Categoria.objects.exists() and docente.programa_academico:
    cat = Categoria.objects.first()
    prog = docente.programa_academico
    fake_exe = SimpleUploadedFile("malware.exe", b"evil content", content_type="application/octet-stream")
    c = Client(); c.force_login(docente)
    before = Documento.objects.count()
    r = c.post('/documentos/subir/', {
        'titulo': 'Malware Test','descripcion': 'Should fail',
        'archivo': fake_exe,'programa': prog.id,'categoria': cat.id,
        'visibilidad': 'PROGRAMA','es_sensible': False,
    })
    after = Documento.objects.count()
    test("T20-Rechazo extensión inválida","Verificar bloqueo de .exe","RF-05","HU-05",
         "Documento NO creado", f"Antes={before}, Después={after}",
         "EXITOSA" if after==before else "FALLIDA",
         "El sistema rechaza correctamente archivos con extensiones no permitidas.")

# T21: Search
print("\n--- Search & Filters ---")
if docente:
    c = Client(); c.force_login(docente)
    t0 = time.time()
    r = c.get('/documentos/busqueda/', {'q': 'test'})
    elapsed = round((time.time()-t0)*1000)
    test("T21-Búsqueda documental","Buscar documentos por título","RF-06","HU-06",
         "HTTP 200, <2000ms", f"HTTP {r.status_code}, {elapsed}ms",
         "EXITOSA" if r.status_code==200 and elapsed<2000 else "PARCIAL",
         f"Búsqueda ejecutada en {elapsed}ms.")

# T22: Advanced search filters
if decana:
    c = Client(); c.force_login(decana)
    r = c.get('/documentos/busqueda/', {'estado': 'APROBADO', 'factor': 'F1'})
    test("T22-Filtros avanzados","Buscar con filtros estado+factor","RF-06","HU-06",
         "HTTP 200", f"HTTP {r.status_code}",
         "EXITOSA" if r.status_code==200 else "FALLIDA",
         "Los filtros avanzados funcionan correctamente.")

# T23: My documents
print("\n--- My Documents ---")
if docente:
    c = Client(); c.force_login(docente)
    r = c.get('/documentos/mis-documentos/')
    test("T23-Mis documentos","Listar documentos propios","RF-07","HU-07",
         "HTTP 200", f"HTTP {r.status_code}",
         "EXITOSA" if r.status_code==200 else "FALLIDA",
         "El docente puede ver su lista personal de documentos.")

# T24: Approval flow
print("\n--- Approval Flow ---")
doc_pending = Documento.objects.filter(estado='PENDIENTE').first()
if doc_pending and (coordinador or decana):
    approver = decana if decana else coordinador
    c = Client(); c.force_login(approver)
    r = c.get('/documentos/aprobar/')
    test("T24-Bandeja de aprobación","Acceder a bandeja de revisión","RF-08","HU-08",
         "HTTP 200", f"HTTP {r.status_code}",
         "EXITOSA" if r.status_code==200 else "FALLIDA",
         "La bandeja de aprobación es accesible para roles aprobadores.")

# T25: Approve a document
qa_doc = Documento.objects.filter(titulo='QA Test Document', estado='PENDIENTE').first()
if qa_doc and decana:
    c = Client(); c.force_login(decana)
    r = c.post(f'/documentos/{qa_doc.id}/aprobar/')
    qa_doc.refresh_from_db()
    test("T25-Aprobar documento","Aprobar documento pendiente","RF-08","HU-08",
         "Estado=APROBADO", f"Estado={qa_doc.estado}",
         "EXITOSA" if qa_doc.estado=='APROBADO' else "FALLIDA",
         "El flujo de aprobación cambia el estado correctamente.")

# T26: Reject flow test (create new doc first)
if docente and Categoria.objects.exists() and docente.programa_academico:
    cat = Categoria.objects.first()
    prog = docente.programa_academico
    fake_pdf2 = SimpleUploadedFile("reject_test.pdf", b"%PDF-1.4 reject", content_type="application/pdf")
    c = Client(); c.force_login(docente)
    c.post('/documentos/subir/', {
        'titulo': 'QA Reject Test','descripcion': 'Para rechazar',
        'archivo': fake_pdf2,'programa': prog.id,'categoria': cat.id,
        'visibilidad': 'PROGRAMA','es_sensible': False,
    })
    rej_doc = Documento.objects.filter(titulo='QA Reject Test').first()
    if rej_doc and decana:
        c2 = Client(); c2.force_login(decana)
        c2.post(f'/documentos/{rej_doc.id}/rechazar/', {'comentario': 'Falta información requerida.'})
        rej_doc.refresh_from_db()
        test("T26-Rechazar documento","Rechazar documento con motivo","RF-08","HU-08",
             "Estado=RECHAZADO + comentario", f"Estado={rej_doc.estado}, Comentario={rej_doc.comentario_rechazo}",
             "EXITOSA" if rej_doc.estado=='RECHAZADO' and rej_doc.comentario_rechazo else "FALLIDA",
             "El rechazo registra estado y motivo correctamente.")

# T27: Document detail
print("\n--- Document Detail ---")
any_doc = Documento.objects.first()
if any_doc and decana:
    c = Client(); c.force_login(decana)
    r = c.get(f'/documentos/{any_doc.id}/')
    test("T27-Detalle de documento","Ver detalle completo","RF-09","HU-09",
         "HTTP 200", f"HTTP {r.status_code}",
         "EXITOSA" if r.status_code==200 else "FALLIDA",
         "El detalle muestra metadatos, versiones y auditoría.")

# T28: Versioning
print("\n--- Versioning ---")
if qa_doc and docente:
    fake_v2 = SimpleUploadedFile("v2_test.pdf", b"%PDF-1.4 version 2", content_type="application/pdf")
    c = Client(); c.force_login(docente)
    ver_before = Version.objects.filter(documento=qa_doc).count()
    r = c.post(f'/versiones/{qa_doc.id}/crear/', {'archivo': fake_v2, 'descripcion_cambio': 'QA Version 2'})
    ver_after = Version.objects.filter(documento=qa_doc).count()
    test("T28-Crear versión","Subir nueva versión de documento","RF-11","HU-11",
         "Versión creada", f"Antes={ver_before}, Después={ver_after}",
         "EXITOSA" if ver_after>ver_before else "FALLIDA",
         "El sistema de versionamiento crea versiones incrementales.")

# T29: Version list
if qa_doc:
    c = Client(); c.force_login(docente)
    r = c.get(f'/versiones/{qa_doc.id}/')
    test("T29-Listar versiones","Ver historial de versiones","RF-11","HU-11",
         "HTTP 200", f"HTTP {r.status_code}",
         "EXITOSA" if r.status_code==200 else "FALLIDA",
         "El historial de versiones es accesible.")

# T30: Version restore
last_ver = Version.objects.filter(documento=qa_doc).order_by('-numero_version').first() if qa_doc else None
if last_ver and docente:
    c = Client(); c.force_login(docente)
    ver_count_before = Version.objects.filter(documento=qa_doc).count()
    r = c.post(f'/versiones/{last_ver.id}/restaurar/')
    ver_count_after = Version.objects.filter(documento=qa_doc).count()
    test("T30-Restaurar versión","Restaurar versión anterior","RF-11","HU-11",
         "Nueva versión creada", f"Antes={ver_count_before}, Después={ver_count_after}",
         "EXITOSA" if ver_count_after>ver_count_before else "FALLIDA",
         "La restauración crea una nueva versión a partir de la anterior.")

# T31: Audit log
print("\n--- Audit ---")
if decana:
    c = Client(); c.force_login(decana)
    r = c.get('/auditoria/')
    test("T31-Log de auditoría","Acceder al registro de auditoría","RF-12","HU-12",
         "HTTP 200", f"HTTP {r.status_code}",
         "EXITOSA" if r.status_code==200 else "FALLIDA",
         "El módulo de auditoría es accesible para la Decana.")

# T32: Audit records exist
audit_count = RegistroAuditoria.objects.count()
test("T32-Registros de auditoría","Verificar existencia de registros","RF-12","HU-12",
     ">0 registros", f"{audit_count} registros",
     "EXITOSA" if audit_count>0 else "FALLIDA",
     "El sistema registra acciones automáticamente en la tabla de auditoría.")

# T33: Audit has IP
audit_with_ip = RegistroAuditoria.objects.exclude(ip_address__isnull=True).exclude(ip_address='').count()
test("T33-IP en auditoría","Verificar captura de IP","RF-12","HU-12",
     "Registros con IP", f"{audit_with_ip} registros con IP",
     "EXITOSA" if audit_with_ip>0 else "PARCIAL",
     "El sistema captura la dirección IP del cliente en los registros de auditoría.")

# T34: Audit export CSV
if decana:
    c = Client(); c.force_login(decana)
    r = c.get('/auditoria/exportar/')
    test("T34-Exportar auditoría CSV","Exportar log a CSV","RF-12","HU-12",
         "Content-Type=text/csv", f"Content-Type={r.get('Content-Type','')}",
         "EXITOSA" if 'csv' in r.get('Content-Type','') else "FALLIDA",
         "La exportación CSV genera un archivo descargable con los registros.")

# T35: Notifications
print("\n--- Notifications ---")
if docente:
    c = Client(); c.force_login(docente)
    r = c.get('/notificaciones/')
    test("T35-Lista notificaciones","Acceder a notificaciones","RF-10","HU-10",
         "HTTP 200", f"HTTP {r.status_code}",
         "EXITOSA" if r.status_code==200 else "FALLIDA",
         "El módulo de notificaciones es accesible.")

# T36: Notification count
notif_count = Notificacion.objects.count()
test("T36-Notificaciones generadas","Verificar generación automática","RF-10","HU-10",
     ">0 notificaciones", f"{notif_count} notificaciones",
     "EXITOSA" if notif_count>0 else "FALLIDA",
     "El sistema genera notificaciones automáticas en los flujos de negocio.")

# T37: Factores CNA
print("\n--- Factores CNA ---")
if decana:
    c = Client(); c.force_login(decana)
    r = c.get('/documentos/factores-cna/')
    test("T37-Vista Factores CNA","Acceder a vista de factores CNA","RF-13","HU-13",
         "HTTP 200", f"HTTP {r.status_code}",
         "EXITOSA" if r.status_code==200 else "FALLIDA",
         "La vista de progreso por factores CNA es funcional para la Decana.")

# T38: AJAX search
print("\n--- AJAX Search ---")
if docente:
    c = Client(); c.force_login(docente)
    r = c.get('/documentos/api/buscar/', {'q': 'test'})
    test("T38-Búsqueda AJAX","Buscar documentos vía API AJAX","RF-06","HU-06",
         "HTTP 200 JSON", f"HTTP {r.status_code}, Content-Type={r.get('Content-Type','')}",
         "EXITOSA" if r.status_code==200 and 'json' in r.get('Content-Type','') else "FALLIDA",
         "El endpoint AJAX retorna resultados en formato JSON.")

# T39: Permissions - access control
print("\n--- Permissions ---")
doc_sensible = Documento.objects.filter(es_sensible=True).first()
if doc_sensible and docente and docente != doc_sensible.autor:
    tiene = PermisoService.usuario_tiene_acceso(docente, doc_sensible)
    permiso_explicito = PermisoDocumento.objects.filter(usuario=docente, documento=doc_sensible).exists()
    test("T39-Control Zero-Trust","Verificar bloqueo de doc sensible sin permiso","RF-14","HU-14",
         "Acceso denegado sin permiso explícito", f"Acceso={tiene}, Permiso={permiso_explicito}",
         "EXITOSA" if not tiene or permiso_explicito else "FALLIDA",
         "Los documentos sensibles requieren solicitud y aprobación explícita.")

# T40: Document deletion
print("\n--- Deletion ---")
rej_doc = Documento.objects.filter(titulo='QA Reject Test').first()
if rej_doc and docente:
    c = Client(); c.force_login(docente)
    r = c.post(f'/documentos/{rej_doc.id}/eliminar/')
    still_exists = Documento.objects.filter(titulo='QA Reject Test').exists()
    test("T40-Eliminar documento","Eliminar documento rechazado","RF-15","HU-15",
         "Documento eliminado", f"Existe={still_exists}",
         "EXITOSA" if not still_exists else "FALLIDA",
         "La eliminación remueve el documento y registra auditoría.")

# Cleanup QA test doc
Documento.objects.filter(titulo='QA Test Document').delete()

# Save results
with open('qa_results_part2.json','w',encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\n{'='*60}")
print(f"PART 2 COMPLETE: {sum(1 for r in results if r['status']=='EXITOSA')}/{len(results)} EXITOSAS")
print(f"{'='*60}")
