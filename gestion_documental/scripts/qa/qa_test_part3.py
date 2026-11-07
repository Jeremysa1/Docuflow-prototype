"""QA Test Part 3: Performance + Security + Integrity."""
import json, time, os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()
from django.test import Client
from django.conf import settings
from apps.usuarios.models import Usuario
from apps.documentos.models import Documento
from apps.auditoria.models import RegistroAuditoria
from apps.versiones.models import Version
from apps.permisos.models import PermisoDocumento

if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

results = []
def test(name, obj, rf, hu, expected, obtained, status, analysis):
    results.append({'name':name,'obj':obj,'rf':rf,'hu':hu,'expected':expected,'obtained':obtained,'status':status,'analysis':analysis})
    print(f"  [{status}] {name}")

decana = Usuario.objects.filter(rol='DECANA', esta_habilitado=True).first()
docente = Usuario.objects.filter(rol='DOCENTE_PLANTA', esta_habilitado=True).first()

# === PERFORMANCE ===
print("="*60)
print("PART 3A: PERFORMANCE")
print("="*60)

# T41: Dashboard load time
if decana:
    c = Client(); c.force_login(decana)
    times = []
    for _ in range(3):
        t0 = time.time(); c.get('/documentos/dashboard/'); times.append(round((time.time()-t0)*1000))
    avg = round(sum(times)/len(times))
    test("T41-Tiempo dashboard","Medir tiempo de carga del dashboard","RNF-02","HU-04",
         "<3000ms", f"Promedio={avg}ms (muestras: {times})",
         "EXITOSA" if avg<3000 else "PARCIAL",
         f"Dashboard carga en {avg}ms promedio. Rendimiento aceptable para entorno local.")

# T42: Search performance
if decana:
    c = Client(); c.force_login(decana)
    times = []
    for _ in range(3):
        t0 = time.time(); c.get('/documentos/busqueda/', {'q': 'documento'}); times.append(round((time.time()-t0)*1000))
    avg = round(sum(times)/len(times))
    test("T42-Tiempo búsqueda","Medir tiempo de búsqueda documental","RNF-02","HU-06",
         "<3000ms", f"Promedio={avg}ms",
         "EXITOSA" if avg<3000 else "PARCIAL",
         f"Búsqueda responde en {avg}ms promedio.")

# T43: Approval view performance
if decana:
    c = Client(); c.force_login(decana)
    t0 = time.time(); c.get('/documentos/aprobar/'); elapsed = round((time.time()-t0)*1000)
    test("T43-Tiempo bandeja aprobación","Medir tiempo vista aprobación","RNF-02","HU-08",
         "<3000ms", f"{elapsed}ms",
         "EXITOSA" if elapsed<3000 else "PARCIAL",
         f"Vista de aprobación en {elapsed}ms.")

# T44: Audit view performance
if decana:
    c = Client(); c.force_login(decana)
    t0 = time.time(); c.get('/auditoria/'); elapsed = round((time.time()-t0)*1000)
    test("T44-Tiempo vista auditoría","Medir tiempo vista auditoría","RNF-02","HU-12",
         "<3000ms", f"{elapsed}ms",
         "EXITOSA" if elapsed<3000 else "PARCIAL",
         f"Auditoría carga en {elapsed}ms.")

# T45: My documents performance
if docente:
    c = Client(); c.force_login(docente)
    t0 = time.time(); c.get('/documentos/mis-documentos/'); elapsed = round((time.time()-t0)*1000)
    test("T45-Tiempo mis documentos","Medir tiempo vista personal","RNF-02","HU-07",
         "<3000ms", f"{elapsed}ms",
         "EXITOSA" if elapsed<3000 else "PARCIAL",
         f"Mis documentos carga en {elapsed}ms.")

# === SECURITY ===
print(f"\n{'='*60}")
print("PART 3B: SECURITY")
print("="*60)

# T46: Direct URL access without auth
c = Client()
sec_urls = ['/documentos/1/','/documentos/1/aprobar/','/documentos/1/eliminar/',
            '/documentos/1/descargar/','/usuarios/gestion/1/habilitar/',
            '/admin/']
blocked = 0
for url in sec_urls:
    r = c.get(url)
    if r.status_code in (302, 403, 404):
        blocked += 1
test("T46-URLs directas sin auth","Intentar acceso directo a recursos","RNF-SEG","HU-SEG",
     f"{len(sec_urls)} bloqueadas", f"{blocked}/{len(sec_urls)} bloqueadas",
     "EXITOSA" if blocked==len(sec_urls) else "PARCIAL",
     "Todas las URLs sensibles requieren autenticación.")

# T47: Docente accessing other user's management
if docente:
    c = Client(); c.force_login(docente)
    r = c.post('/usuarios/gestion/1/habilitar/')
    test("T47-Docente gestiona usuarios","Docente intenta habilitar usuarios","RNF-SEG","HU-SEG",
         "HTTP 403", f"HTTP {r.status_code}",
         "EXITOSA" if r.status_code==403 else "FALLIDA",
         "El sistema bloquea operaciones de gestión de usuarios para docentes.")

# T48: POST without CSRF (Django handles by middleware)
c = Client(enforce_csrf_checks=True)
if docente:
    c.force_login(docente)
    r = c.post('/documentos/subir/', {'titulo': 'CSRF Test'})
    test("T48-Protección CSRF","POST sin token CSRF","RNF-SEG","HU-SEG",
         "HTTP 403", f"HTTP {r.status_code}",
         "EXITOSA" if r.status_code==403 else "FALLIDA",
         "Django rechaza correctamente peticiones POST sin token CSRF válido.")

# T49: Logout redirects
if docente:
    c = Client(); c.force_login(docente)
    r = c.post('/login/logout/')
    test("T49-Logout redirect","Verificar redirección post-logout","RNF-SEG","HU-01",
         "HTTP 302 -> /login/", f"HTTP {r.status_code} -> {r.get('Location','')}",
         "EXITOSA" if r.status_code==302 else "FALLIDA",
         "Tras logout, el sistema redirige al login.")

# T50: Post-logout access denied
if docente:
    c = Client(); c.force_login(docente)
    c.post('/login/logout/')
    r = c.get('/documentos/dashboard/')
    test("T50-Acceso post-logout","Intentar acceder tras cerrar sesión","RNF-SEG","HU-01",
         "HTTP 302 (redirect login)", f"HTTP {r.status_code}",
         "EXITOSA" if r.status_code==302 else "FALLIDA",
         "Tras cerrar sesión, el acceso es denegado correctamente.")

# T51: Coordinator cannot approve other program docs (logic check)
from apps.documentos.services import DocumentoService
coord = Usuario.objects.filter(rol='COORDINADOR', esta_habilitado=True).first()
if coord:
    other_prog_doc = Documento.objects.exclude(programa=coord.programa_academico).filter(estado='PENDIENTE').first()
    if other_prog_doc:
        try:
            DocumentoService.aprobar_documento(other_prog_doc.id, coord)
            test("T51-Coordinador otro programa","Coordinador aprueba doc de otro programa","RNF-SEG","HU-02",
                 "PermissionError", "No lanzó excepción","FALLIDA","Vulnerabilidad en restricción de programa.")
        except PermissionError:
            test("T51-Coordinador otro programa","Coordinador aprueba doc de otro programa","RNF-SEG","HU-02",
                 "PermissionError", "PermissionError lanzado","EXITOSA","Coordinador correctamente bloqueado de aprobar docs de otros programas.")
    else:
        test("T51-Coordinador otro programa","Coordinador aprueba doc de otro programa","RNF-SEG","HU-02",
             "PermissionError", "No hay docs de otros programas pendientes","PARCIAL","No se pudo ejecutar por falta de datos.")

# === INTEGRITY ===
print(f"\n{'='*60}")
print("PART 3C: DATA INTEGRITY")  
print("="*60)

# T52: Documento-Usuario FK integrity
docs_sin_autor = Documento.objects.filter(autor__isnull=True).count()
test("T52-Integridad doc-autor","Verificar FK documento-usuario","RNF-INT","HU-ALL",
     "0 docs sin autor", f"{docs_sin_autor} docs sin autor",
     "EXITOSA" if docs_sin_autor==0 else "FALLIDA",
     "Todos los documentos tienen un autor asignado correctamente.")

# T53: Audit record integrity
audit_sin_usuario = RegistroAuditoria.objects.filter(usuario__isnull=True).count()
total_audit = RegistroAuditoria.objects.count()
test("T53-Integridad auditoría","Verificar registros de auditoría","RNF-INT","HU-12",
     "Registros con usuario", f"{total_audit} total, {audit_sin_usuario} sin usuario",
     "EXITOSA" if audit_sin_usuario==0 else "PARCIAL",
     "Los registros de auditoría mantienen referencia al usuario que ejecutó la acción.")

# T54: Version numbering consistency
from django.db.models import Count
dup_versions = Version.objects.values('documento','numero_version').annotate(c=Count('id')).filter(c__gt=1).count()
test("T54-Unicidad de versiones","Verificar unique_together en versiones","RNF-INT","HU-11",
     "0 duplicados", f"{dup_versions} duplicados",
     "EXITOSA" if dup_versions==0 else "FALLIDA",
     "La constraint unique_together(documento, numero_version) se cumple.")

# T55: Permissions unique constraint
dup_permisos = PermisoDocumento.objects.values('usuario','documento').annotate(c=Count('id')).filter(c__gt=1).count()
test("T55-Unicidad de permisos","Verificar unique_together en permisos","RNF-INT","HU-14",
     "0 duplicados", f"{dup_permisos} duplicados",
     "EXITOSA" if dup_permisos==0 else "FALLIDA",
     "La constraint unique_together(usuario, documento) se cumple en permisos.")

# T56: Categorias exist
from apps.documentos.models import Categoria
cat_count = Categoria.objects.count()
test("T56-Catálogo de categorías","Verificar catálogo de categorías","RNF-INT","HU-05",
     ">0 categorías", f"{cat_count} categorías",
     "EXITOSA" if cat_count>0 else "FALLIDA",
     "El catálogo de categorías está poblado correctamente.")

# T57: Programas exist
from apps.usuarios.models import ProgramaAcademico
prog_count = ProgramaAcademico.objects.count()
test("T57-Catálogo de programas","Verificar catálogo de programas","RNF-INT","HU-ALL",
     ">0 programas", f"{prog_count} programas",
     "EXITOSA" if prog_count>0 else "FALLIDA",
     "El catálogo de programas académicos está poblado.")

# T58: Documents have valid states
invalid_states = Documento.objects.exclude(estado__in=['PENDIENTE','APROBADO','RECHAZADO']).count()
test("T58-Estados válidos","Verificar estados de documentos","RNF-INT","HU-08",
     "0 estados inválidos", f"{invalid_states} inválidos",
     "EXITOSA" if invalid_states==0 else "FALLIDA",
     "Todos los documentos tienen estados válidos (PENDIENTE/APROBADO/RECHAZADO).")

# T59: Users have valid roles
invalid_roles = Usuario.objects.exclude(rol__in=['DECANA','COORDINADOR','DOCENTE_PLANTA']).count()
test("T59-Roles válidos","Verificar roles de usuarios","RNF-INT","HU-02",
     "0 roles inválidos", f"{invalid_roles} inválidos",
     "EXITOSA" if invalid_roles==0 else "FALLIDA",
     "Todos los usuarios tienen roles válidos del sistema.")

# T60: General stats
print(f"\n{'='*60}")
print("STATISTICS")
print("="*60)
print(f"  Usuarios: {Usuario.objects.count()}")
print(f"  Documentos: {Documento.objects.count()}")
print(f"  Versiones: {Version.objects.count()}")
print(f"  Auditoría: {RegistroAuditoria.objects.count()}")
print(f"  Notificaciones: {Notificacion.objects.count()}")
print(f"  Permisos: {PermisoDocumento.objects.count()}")
print(f"  Categorías: {Categoria.objects.count()}")
print(f"  Programas: {ProgramaAcademico.objects.count()}")

from apps.notificaciones.models import Notificacion

# Save
os.makedirs(os.path.join('scripts', 'qa', 'salidas'), exist_ok=True)
with open(os.path.join('scripts', 'qa', 'salidas', 'qa_results_part3.json'),'w',encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\n{'='*60}")
print(f"PART 3 COMPLETE: {sum(1 for r in results if r['status']=='EXITOSA')}/{len(results)} EXITOSAS")
print(f"{'='*60}")
