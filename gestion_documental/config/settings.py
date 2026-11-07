"""
Django settings para la plataforma de Gestión Documental Universitaria.
"""
import os
from pathlib import Path

from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Blindaje de entorno: el proyecto solo corre con los pins de requirements.txt.
# Si se arranca con otro intérprete (ej. el Python del sistema en vez del venv),
# falla rápido aquí con un mensaje claro en vez de divergencias silenciosas.
import importlib.metadata as _metadata

_PINS_CRITICOS = {
    'Django': '6.1.3',
    'django-unfold': '0.105.0',
    'Pillow': '13.0.0',
    'psycopg2-binary': '2.9.12',
    'reportlab': '5.0.1',
}
for _dist, _pin in _PINS_CRITICOS.items():
    try:
        _instalada = _metadata.version(_dist)
    except _metadata.PackageNotFoundError:
        raise ImproperlyConfigured(
            f"Falta '{_dist}=={_pin}'. Activa el venv: "
            r".\venv\Scripts\Activate.ps1 (desde gestion_documental)"
        )
    if _instalada != _pin:
        raise ImproperlyConfigured(
            f"'{_dist}' instalado ({_instalada}) != exigido ({_pin}). "
            r"Usa el venv del proyecto: .\venv\Scripts\python.exe manage.py ..."
        )

# Cargar variables de entorno
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# H-09: sin fallback inseguro. En prod SECRET_KEY es obligatoria; en dev se permite
# DJANGO_INSECURE_DEV_KEY=1 para no romper el prototipo local.
_SECRET_KEY_ENV = os.getenv('SECRET_KEY')
if _SECRET_KEY_ENV:
    SECRET_KEY = _SECRET_KEY_ENV
elif os.getenv('DJANGO_INSECURE_DEV_KEY', '0') == '1' or os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes'):
    SECRET_KEY = 'django-insecure-solo-dev-local-no-usar-en-prod-cambiala'
else:
    raise RuntimeError('SECRET_KEY no configurada. Define SECRET_KEY en el entorno.')

# SECURITY WARNING: don't run with debug turned on in production!
# H-09: default seguro False (antes True).
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]

# H-09: cookies y HTTPS endurecidos. En dev (DEBUG=True) se relajan automáticamente.
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', '0' if DEBUG else '1') == '1'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', '0' if DEBUG else '1') == '1'
CSRF_COOKIE_HTTPONLY = False  # el JS no necesita leerla; Django la valida vía header/form
CSRF_COOKIE_SAMESITE = os.getenv('CSRF_COOKIE_SAMESITE', 'Lax')
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', '0' if DEBUG else '1') == '1'
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '0' if DEBUG else '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'


# Application definition

INSTALLED_APPS = [
    # Tema premium del admin (debe ir antes de django.contrib.admin)
    'unfold',
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',  # H-10: índices GIN/trigram (sin tablas propias)
    # Terceros
    'widget_tweaks',
    # Sistema de diseño: template tags `{% load sigea %}` (core/templatetags)
    'core',
    # Apps propias
    'apps.usuarios',
    'apps.documentos',
    'apps.versiones',
    'apps.permisos',
    'apps.notificaciones',
    'apps.auditoria',
]

# R3-03: backend con lockout compartido (frontal + /admin/login/)
AUTHENTICATION_BACKENDS = ['apps.usuarios.backends.BloqueoAdminBackend']

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Sirve estáticos comprimidos con caché agresiva (requiere collectstatic)
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # A2: expulsa cuentas deshabilitadas/inactivas (necesita auth y messages)
    'core.middleware.CuentaHabilitadaMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Content-Security-Policy (Django 6): solo scripts propios; /admin/ queda fuera
    'core.middleware.CSPSinAdminMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.notificaciones.context_processors.notificaciones_no_leidas',
                'apps.usuarios.context_processors.navegacion',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# M11: la aplicación usa un rol sin privilegios de administración (DB_USER).
# Solo migrate y test (crea la base de pruebas) usan el administrador, si está definido.
import sys  # noqa: E402
_COMANDOS_ADMIN = {'migrate', 'test', 'makemigrations', 'sqlmigrate', 'showmigrations'}
_USAR_ADMIN = os.getenv('DB_ADMIN_USER') and len(sys.argv) > 1 and sys.argv[1] in _COMANDOS_ADMIN

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'SIGEA_db'),
        'USER': os.getenv('DB_ADMIN_USER') if _USAR_ADMIN else os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_ADMIN_PASSWORD', '') if _USAR_ADMIN else os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        # H-09: reutiliza conexiones (evita handshake por request) y las
        # valida antes de usarlas. Con pgbouncer en modo transacción usar 0.
        'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '60')),
        'CONN_HEALTH_CHECKS': True,
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    # M4: mayúscula y símbolo, para que registro, recuperación e invitación usen la misma política
    {
        'NAME': 'core.validators.ComplejidadValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# En prod: archivos hasheados + Brotli/Gzip + max-age inmutable.
# En dev: almacenamiento plano (sin manifiesto) para no exigir collectstatic.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': (
            'whitenoise.storage.CompressedManifestStaticFilesStorage'
            if not DEBUG else
            'django.contrib.staticfiles.storage.StaticFilesStorage'
        ),
    },
}

# Almacenamiento local de archivos subidos
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Modelo de usuario personalizado
AUTH_USER_MODEL = 'usuarios.Usuario'

# Configuración de login
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = 'documentos:dashboard'
LOGOUT_REDIRECT_URL = '/login/'

# Formatos permitidos para subir documentos
ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.docx', '.xlsx', '.pptx']
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

# Gestión de Sesiones
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Cierra sesión al cerrar el navegador
SESSION_SAVE_EVERY_REQUEST = True       # Renueva la sesión en cada petición
SESSION_COOKIE_AGE = 900                # 15 minutos de inactividad
# H-07: sesiones cached_db (lectura desde caché, escritura necesaria para
# la expiración deslizante de 15 min). Requiere CACHES configurado.
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# Caché local explícita (H-08: conteos y estadísticas con TTL corto).
# Un proceso (runserver/gunicorn --workers 1): LocMem es suficiente.
# Multiproceso: cambiar a Redis es solo este bloque (el código no cambia):
#   'default': {'BACKEND': 'django_redis.cache.RedisCache',
#               'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')}
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'sigea-cache',
        'TIMEOUT': 300,
        'KEY_PREFIX': 'sigea',
    }
}

# Email backend (H-07/H-09: console solo en dev; en prod exigir SMTP por env)
EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', '0' if DEBUG else '1') == '1'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@docuflow.edu.co')

if not DEBUG and EMAIL_BACKEND.endswith('console.EmailBackend'):
    raise RuntimeError('EMAIL_BACKEND console no permitido en prod (expondría tokens de recuperación en logs).')

# Configuración de descargas Nginx X-Accel-Redirect
USE_X_ACCEL_REDIRECT = os.getenv('USE_X_ACCEL_REDIRECT', '0') == '1'

# C3: número de proxies inversos de confianza delante de Django. Con 0 (por
# defecto) se ignora X-Forwarded-For y la auditoría usa REMOTE_ADDR. Con Nginx
# delante, usar 1.
TRUSTED_PROXY_COUNT = int(os.getenv('TRUSTED_PROXY_COUNT', '0'))

# Fixtures
FIXTURE_DIRS = [BASE_DIR / 'apps' / 'fixtures']

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Permitir IFRAMES del mismo origen para el visor PDF inline
X_FRAME_OPTIONS = 'SAMEORIGIN'

# Content-Security-Policy. style-src admite 'unsafe-inline' solo por los atributos
# style="--variable: valor" que dibujan los gráficos; los scripts son únicamente propios.
from django.utils.csp import CSP  # noqa: E402
SECURE_CSP = {
    'default-src': [CSP.SELF],
    'script-src': [CSP.SELF],
    'style-src': [CSP.SELF, CSP.UNSAFE_INLINE],
    'img-src': [CSP.SELF, 'data:'],
    'font-src': [CSP.SELF],
    'connect-src': [CSP.SELF],
    'frame-src': [CSP.SELF],
    'frame-ancestors': [CSP.SELF],
    'object-src': [CSP.NONE],
    'base-uri': [CSP.SELF],
    'form-action': [CSP.SELF],
}
# W019 silenciado a conciencia: SAMEORIGIN es necesario para el visor PDF
# inline del detalle de documento; DENY lo rompería. No hay contenido
# enmarcable por terceros (sin embeds externos).
SILENCED_SYSTEM_CHECKS = ['security.W019']

# ═══════════════════════════════════════════════════════════════
# Django Unfold — Admin premium (Tailwind + modo oscuro/claro)
# Docs: https://unfoldadmin.com/docs/configuration/settings/
# Iconos del sidebar: Material Symbols (https://fonts.google.com/icons)
# ═══════════════════════════════════════════════════════════════
UNFOLD = {
    "SITE_TITLE": "SIGEA Admin",
    "SITE_HEADER": "SIGEA",
    "SITE_SUBHEADER": "Gestión Documental",
    "SITE_URL": "/dashboard/",
    "SITE_SYMBOL": "folder_open",
    "SITE_LOGO": lambda request: static("img/sigea_logo_p2.png"),
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/png",
            "href": lambda request: static("img/sigea_logo_p2.png"),
        },
    ],
    # Sin "THEME" fijo: Unfold muestra el conmutador claro/oscuro.
    "BORDER_RADIUS": "12px",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,  # los objetos no exponen vista pública
    "ENVIRONMENT": "config.unfold_callbacks.environment",
    "STYLES": [
        lambda request: static("css/admin_unfold.css"),
    ],
    "COLORS": {
        "base": {
            "50": "oklch(98.5% .002 247.839)",
            "100": "oklch(96.7% .003 264.542)",
            "200": "oklch(92.8% .006 264.531)",
            "300": "oklch(87.2% .01 258.338)",
            "400": "oklch(70.7% .022 261.325)",
            "500": "oklch(55.1% .027 264.364)",
            "600": "oklch(44.6% .03 256.802)",
            "700": "oklch(37.3% .034 259.733)",
            "800": "oklch(27.8% .033 256.848)",
            "900": "oklch(21% .034 264.665)",
            "950": "oklch(13% .028 261.692)",
        },
        # Escala de marca SIGEA: el 800 es exactamente #142a59 (spec 002, research R10)
        "primary": {
            "50": "oklch(97% .012 262)",
            "100": "oklch(93.5% .028 262)",
            "200": "oklch(87% .052 262)",
            "300": "oklch(77% .088 262)",
            "400": "oklch(64% .125 262)",
            "500": "oklch(52% .145 262)",
            "600": "oklch(44% .135 262)",
            "700": "oklch(36.5% .112 263)",
            "800": "oklch(30.6% .093 263)",
            "900": "oklch(25% .075 263)",
            "950": "oklch(19% .055 263)",
        },
        "font": {
            "subtle-light": "var(--color-base-500)",
            "subtle-dark": "var(--color-base-400)",
            "default-light": "var(--color-base-600)",
            "default-dark": "var(--color-base-300)",
            "important-light": "var(--color-base-900)",
            "important-dark": "var(--color-base-100)",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Principal"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Panel"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                    {
                        "title": _("Ver sitio"),
                        "icon": "open_in_new",
                        "link": "/dashboard/",
                    },
                ],
            },
            {
                "title": _("Documentos"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Documentos"),
                        "icon": "description",
                        "link": reverse_lazy("admin:documentos_documento_changelist"),
                    },
                    {
                        "title": _("Categorías"),
                        "icon": "category",
                        "link": reverse_lazy("admin:documentos_categoria_changelist"),
                    },
                    {
                        "title": _("Versiones"),
                        "icon": "history",
                        "link": reverse_lazy("admin:versiones_version_changelist"),
                    },
                ],
            },
            {
                "title": _("Accesos"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Solicitudes"),
                        "icon": "inbox",
                        "link": reverse_lazy("admin:permisos_solicitudacceso_changelist"),
                    },
                    {
                        "title": _("Permisos"),
                        "icon": "lock",
                        "link": reverse_lazy("admin:permisos_permisodocumento_changelist"),
                    },
                    {
                        "title": _("Votos sensibles"),
                        "icon": "how_to_vote",
                        "link": reverse_lazy("admin:permisos_votoaccesosensible_changelist"),
                    },
                ],
            },
            {
                "title": _("Sistema"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Usuarios"),
                        "icon": "group",
                        "link": reverse_lazy("admin:usuarios_usuario_changelist"),
                    },
                    {
                        "title": _("Programas"),
                        "icon": "school",
                        "link": reverse_lazy("admin:usuarios_programaacademico_changelist"),
                    },
                    {
                        "title": _("Notificaciones"),
                        "icon": "notifications",
                        "link": reverse_lazy("admin:notificaciones_notificacion_changelist"),
                    },
                    {
                        "title": _("Auditoría"),
                        "icon": "shield",
                        "link": reverse_lazy("admin:auditoria_registroauditoria_changelist"),
                        "permission": lambda request: getattr(request.user, "rol", None) in ("DECANA", "COORDINADOR"),
                    },
                ],
            },
        ],
    },
}
