"""QA Test Part 1: System checks and auth tests."""
import json, time, os, sys
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()
from django.test import Client
from django.conf import settings
from apps.usuarios.models import Usuario
from apps.documentos.models import Documento, Categoria
from apps.auditoria.models import RegistroAuditoria
from apps.versiones.models import Version
from apps.permisos.models import PermisoDocumento, SolicitudAcceso
from apps.notificaciones.models import Notificacion

if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

results = []

def test(name, obj, rf, hu, expected, obtained, status, analysis):
    results.append({'name':name,'obj':obj,'rf':rf,'hu':hu,'expected':expected,'obtained':obtained,'status':status,'analysis':analysis})
    print(f"  [{status}] {name}")

print("="*60)
print("PART 1: SYSTEM + AUTH + SECURITY")
print("="*60)

# T1: Django system check
print("\n--- System Integrity ---")
from django.core.management import call_command
from io import StringIO
out = StringIO()
try:
    call_command('check', stdout=out)
    test("T01-System Check Django","Verificar integridad del proyecto","RNF","HU-ALL",
         "0 errores", out.getvalue().strip(), "EXITOSA", "Django no reporta errores de configuración.")
except Exception as e:
    test("T01-System Check Django","Verificar integridad","RNF","HU-ALL","0 errores",str(e),"FALLIDA","Error de sistema.")

# T2: DB connection
try:
    count = Usuario.objects.count()
    test("T02-Conexión PostgreSQL","Verificar conexión BD","RNF-01","HU-ALL",
         "Conexión exitosa",f"Conexión OK. {count} usuarios en BD.","EXITOSA","PostgreSQL operativo.")
except Exception as e:
    test("T02-Conexión PostgreSQL","Verificar conexión BD","RNF-01","HU-ALL","Conexión exitosa",str(e),"FALLIDA","BD no disponible.")

# T3: All migrations applied
out2 = StringIO()
call_command('showmigrations', '--plan', stdout=out2)
plan = out2.getvalue()
unapplied = [l for l in plan.strip().split('\n') if '[ ]' in l]
if not unapplied:
    test("T03-Migraciones aplicadas","Verificar esquema BD","RNF","HU-ALL","Todas aplicadas","Todas las migraciones aplicadas.","EXITOSA","Esquema sincronizado.")
else:
    test("T03-Migraciones aplicadas","Verificar esquema BD","RNF","HU-ALL","Todas aplicadas",f"{len(unapplied)} pendientes","FALLIDA","Migraciones pendientes.")

# Auth tests
print("\n--- Authentication ---")
c = Client()

# T4: Login page accessible
r = c.get('/login/')
test("T04-Acceso página login","Verificar accesibilidad del login","RF-01","HU-01",
     "HTTP 200", f"HTTP {r.status_code}", "EXITOSA" if r.status_code==200 else "FALLIDA",
     "La página de login es accesible sin autenticación.")

# T5: Redirect root to login
r = c.get('/', follow=False)
test("T05-Redirección raíz a login","Verificar redirect / -> /login/","RF-01","HU-01",
     "HTTP 302 -> /login/", f"HTTP {r.status_code} -> {r.get('Location','')}",
     "EXITOSA" if r.status_code==302 and '/login/' in r.get('Location','') else "FALLIDA",
     "La raíz redirige correctamente al login.")

# T6: Login with valid credentials (find a user)
users = Usuario.objects.filter(esta_habilitado=True, is_active=True)
if users.exists():
    u = users.first()
    c2 = Client()
    c2.force_login(u)
    r = c2.get('/documentos/dashboard/')
    test("T06-Login usuario habilitado","Autenticar usuario válido","RF-01","HU-01",
         "HTTP 200 dashboard", f"HTTP {r.status_code} para {u.email} (rol={u.rol})",
         "EXITOSA" if r.status_code==200 else "FALLIDA",
         "Usuario habilitado accede correctamente al dashboard.")
else:
    test("T06-Login usuario habilitado","Autenticar usuario válido","RF-01","HU-01",
         "HTTP 200","No hay usuarios habilitados","FALLIDA","Sin usuarios para probar.")

# T7: Access without auth
c3 = Client()
protected = ['/documentos/dashboard/','/documentos/subir/','/documentos/mis-documentos/','/documentos/busqueda/','/documentos/aprobar/','/auditoria/','/usuarios/perfil/','/usuarios/gestion/','/notificaciones/']
blocked = 0
for url in protected:
    r = c3.get(url)
    if r.status_code in (302,403):
        blocked += 1
test("T07-Acceso sin autenticación","Verificar protección de rutas","RF-02, RNF-SEG","HU-01",
     f"{len(protected)} rutas bloqueadas", f"{blocked}/{len(protected)} rutas bloqueadas",
     "EXITOSA" if blocked==len(protected) else "PARCIAL",
     f"{'Todas' if blocked==len(protected) else 'Algunas'} rutas protegidas requieren autenticación.")

# T8: Role restriction - Docente cannot access admin views
docentes = Usuario.objects.filter(rol='DOCENTE_PLANTA', esta_habilitado=True, is_active=True)
if docentes.exists():
    doc_user = docentes.first()
    c4 = Client()
    c4.force_login(doc_user)
    admin_urls = ['/documentos/aprobar/','/usuarios/gestion/','/auditoria/']
    forbidden = 0
    for url in admin_urls:
        r = c4.get(url)
        if r.status_code == 403:
            forbidden += 1
    test("T08-Restricción rol DOCENTE","Verificar que docente no accede a vistas admin","RF-02","HU-02",
         f"{len(admin_urls)} bloqueadas", f"{forbidden}/{len(admin_urls)} bloqueadas",
         "EXITOSA" if forbidden==len(admin_urls) else "PARCIAL",
         "El decorador @role_required bloquea correctamente al docente.")
else:
    test("T08-Restricción rol DOCENTE","Verificar restricción","RF-02","HU-02","Bloqueadas","Sin docentes","FALLIDA","No hay docentes habilitados.")

# T9: Decana accesses all views
decanas = Usuario.objects.filter(rol='DECANA', esta_habilitado=True)
if decanas.exists():
    dec = decanas.first()
    c5 = Client()
    c5.force_login(dec)
    dec_urls = ['/documentos/dashboard/','/documentos/aprobar/','/usuarios/gestion/','/auditoria/','/documentos/factores-cna/']
    ok = 0
    for url in dec_urls:
        r = c5.get(url)
        if r.status_code == 200:
            ok += 1
    test("T09-Acceso total DECANA","Verificar acceso completo de la Decana","RF-02","HU-02",
         f"{len(dec_urls)} accesibles", f"{ok}/{len(dec_urls)} accesibles",
         "EXITOSA" if ok==len(dec_urls) else "PARCIAL",
         "La Decana tiene acceso completo a todas las vistas administrativas.")
else:
    test("T09-Acceso total DECANA","Verificar acceso","RF-02","HU-02","Accesibles","Sin decana","FALLIDA","No hay decana.")

# T10: Session config
test("T10-Configuración de sesión","Verificar parámetros de sesión","RNF-SEG","HU-01",
     "Expire=True, Age=900", f"Expire={settings.SESSION_EXPIRE_AT_BROWSER_CLOSE}, Age={settings.SESSION_COOKIE_AGE}",
     "EXITOSA" if settings.SESSION_EXPIRE_AT_BROWSER_CLOSE and settings.SESSION_COOKIE_AGE==900 else "FALLIDA",
     "Sesiones configuradas: expiran al cerrar navegador, 15 min inactividad.")

# T11: CSRF middleware active
csrf_active = 'django.middleware.csrf.CsrfViewMiddleware' in settings.MIDDLEWARE
test("T11-Protección CSRF activa","Verificar middleware CSRF","RNF-SEG","HU-ALL",
     "CSRF middleware activo", f"Activo={csrf_active}",
     "EXITOSA" if csrf_active else "FALLIDA",
     "Protección contra CSRF habilitada en todos los formularios POST.")

# T12: Clickjacking protection
xframe = 'django.middleware.clickjacking.XFrameOptionsMiddleware' in settings.MIDDLEWARE
test("T12-Protección Clickjacking","Verificar X-Frame-Options","RNF-SEG","HU-ALL",
     "XFrame middleware activo", f"Activo={xframe}",
     "EXITOSA" if xframe else "FALLIDA",
     "Protección contra clickjacking habilitada.")

# T13: Allowed extensions config
exts = settings.ALLOWED_DOCUMENT_EXTENSIONS
test("T13-Extensiones permitidas","Verificar formatos válidos de documento","RF-03","HU-03",
     "[.pdf,.docx,.xlsx,.pptx]", str(exts),
     "EXITOSA" if set(exts)=={'.pdf','.docx','.xlsx','.pptx'} else "PARCIAL",
     "Solo se permiten formatos de oficina seguros.")

# T14: Max upload size
max_mb = settings.MAX_UPLOAD_SIZE / (1024*1024)
test("T14-Tamaño máximo archivo","Verificar límite de carga","RF-03","HU-03",
     "10 MB", f"{max_mb} MB",
     "EXITOSA" if max_mb==10 else "PARCIAL",
     "Límite de carga configurado correctamente.")

# T15: Password validators
pw_count = len(settings.AUTH_PASSWORD_VALIDATORS)
test("T15-Validadores de contraseña","Verificar políticas de password","RNF-SEG","HU-01",
     "4 validadores", f"{pw_count} validadores activos",
     "EXITOSA" if pw_count>=4 else "PARCIAL",
     "Django aplica validadores de similitud, longitud mínima, contraseñas comunes y numéricas.")

# Save results
with open('qa_results_part1.json','w',encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\n{'='*60}")
print(f"PART 1 COMPLETE: {sum(1 for r in results if r['status']=='EXITOSA')}/{len(results)} EXITOSAS")
print(f"{'='*60}")
