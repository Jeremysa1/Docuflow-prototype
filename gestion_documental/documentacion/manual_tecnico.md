# Documentación Técnica: SIGEA

## 1. Descripción General del Sistema
**Nombre:** SIGEA
**Propósito:** Plataforma institucional para la gestión, acreditación y control de documentos universitarios. Permite la centralización de evidencias para procesos de calidad académica (CNA), con flujos estrictos de aprobación y control de acceso granular.
**Contexto de Uso:** Facultades universitarias que requieren organizar documentación por programas académicos, factores de acreditación y roles de responsabilidad.

### Stack Tecnológico
- **Framework Principal:** Django 4.2+
- **Lenguaje:** Python 3.x
- **Base de Datos:** PostgreSQL
- **Frontend:** Django Templates + Tailwind CSS + Lucide Icons
- **Dependencias Clave:**
  - `psycopg2-binary`: Driver para PostgreSQL.
  - `python-dotenv`: Gestión de variables de entorno.
  - `Pillow`: Procesamiento de imágenes (fotos de perfil).
  - `django-widget-tweaks`: Mejora de renderizado de formularios.

---

## 2. Arquitectura del Sistema
El sistema sigue el patrón **MVT (Model-View-Template)** de Django, reforzado con una **Capa de Servicios (Service Layer)** para desacoplar la lógica de negocio de las vistas.

### Estructura de Carpetas
- `config/`: Configuración global del proyecto (settings, urls, wsgi).
- `apps/`: Contiene las aplicaciones modulares del sistema.
  - `usuarios/`: Gestión de identidades, roles y perfiles.
  - `documentos/`: Núcleo de gestión de archivos y categorías.
  - `permisos/`: Sistema Zero-Trust y solicitudes de acceso.
  - `versiones/`: Historial de cambios y versionado de archivos.
  - `auditoria/`: Logs de actividad y trazabilidad.
  - `notificaciones/`: Alertas internas para usuarios.
- `core/`: Utilidades transversales (decoradores, servicios de almacenamiento).
- `templates/`: Plantillas HTML base y componentes globales.
- `static/`: Activos estáticos (CSS, JS, Imágenes).
- `media/`: Directorio de almacenamiento de archivos subidos (no versionado).

### Flujo de una Solicitud
1. **URL:** El `urls.py` enruta la petición a una vista.
2. **Vista:** Valida la sesión y los permisos (decoradores). Recibe datos del formulario.
3. **Servicio:** La vista llama a un método estático de un `Service` (ej. `DocumentoService.crear_documento`).
4. **Modelo:** El servicio interactúa con los modelos, aplica lógica de negocio y guarda en la BD.
5. **Respuesta:** La vista retorna un template renderizado o una redirección con mensajes.

---

## 3. Módulos y Apps

### 🔑 usuarios
- **Modelos:**
  - `Usuario`: Extiende `AbstractUser`. Campos: `rol` (choices), `programa_academico` (FK), `esta_habilitado` (bool), `intentos_fallidos`, `foto_perfil`, tokens de recuperación.
  - `ProgramaAcademico`: Catálogo de programas (Nombre, Código).
- **Servicios:** `UsuarioService` maneja autenticación, bloqueo de cuentas y recuperación.

### 📄 documentos
- **Modelos:**
  - `Documento`: Entidad principal. Campos: `titulo`, `archivo`, `estado` (PENDIENTE, APROBADO, RECHAZADO), `visibilidad` (INSTITUCIONAL, PROGRAMA), `es_sensible` (bool), `factor_cna` (F1-F12), `autor` (FK), `programa` (FK).
  - `Categoria`: Catálogo de tipos de documentos.
- **Servicios:** `DocumentoService` centraliza la carga, aprobación, rechazo y búsqueda avanzada.

### 🛡️ permisos (Zero-Trust)
- **Modelos:**
  - `PermisoDocumento`: Relación usuario-documento con flags `puede_ver` y `puede_descargar`.
  - `SolicitudAcceso`: Peticiones de acceso con `motivo` y `estado`.
  - `VotoAccesoSensible`: Registro de votos para documentos marcados como sensibles.
- **Servicios:** `PermisoService` verifica acceso en tiempo real y gestiona el flujo de votación.

---

## 4. Base de Datos
El esquema es relacional, optimizado con índices en búsquedas frecuentes (títulos, fechas).

| Entidad | Relaciones Clave | Restricciones |
| :--- | :--- | :--- |
| `Usuario` | FK a `ProgramaAcademico` | Email único, Username único. |
| `Documento` | FK a `Usuario`, `Categoria`, `Programa` | Título requerido, Archivo máx 500 caracteres de ruta. |
| `SolicitudAcceso` | FK a `Usuario`, `Documento` | `unique_together` (solicitante, documento). |
| `VotoAccesoSensible`| FK a `SolicitudAcceso`, `Usuario` | `unique_together` (solicitud, votante). |

**Datos Precargados (Fixtures):**
El archivo `datos_iniciales.json` incluye:
- Programas: Ingeniería Civil, Software, Mecánica.
- Categorías: Autoevaluación, Laboratorios, Estadísticas, etc. (13 en total).
- Usuarios base: `decana`, `coordinador`, `docente`.

---

## 5. Autenticación y Control de Acceso
- **Mecanismo:** Autenticación por Email/Password mediante el backend de Django personalizado en `UsuarioService`.
- **Habilitación Obligatoria:** Los usuarios registrados no pueden entrar hasta que la **Decana** los habilite manualmente (`esta_habilitado=True`).
- **Sistema de Roles:**
  - `DECANA`: Acceso total, gestión de usuarios, auditoría global.
  - `COORDINADOR`: Gestión de documentos y solicitudes de su programa.
  - `DOCENTE_PLANTA`: Carga de documentos, visualización de documentos permitidos.
- **Decoradores:**
  - `@role_required('ROL')`: Restringe vistas por jerarquía.
  - `@document_permission_required('tipo')`: Verifica permiso granular sobre un ID de documento.

---

## 6. Flujos de Negocio Principales

### Carga y Aprobación
1. El Docente sube un archivo. El estado queda en `PENDIENTE`.
2. Si el Docente es de planta, se notifica al Coordinador de su programa.
3. El Coordinador/Decana revisa y selecciona `APROBAR` o `RECHAZAR` (con comentario).
4. El sistema registra el cambio de estado y notifica al autor.

### Control Zero-Trust (Documentos Sensibles)
1. Si un documento se marca como `es_sensible=True`, ningún docente puede verlo por defecto.
2. El docente solicita acceso justificando el motivo.
3. **Votación:** Se requiere que **2 miembros** (Autor, Coordinador o Decana) voten a favor.
4. Un solo voto en **RECHAZADO** deniega la solicitud inmediatamente.

---

## 7. Validaciones Implementadas
- **Archivos:** Extensiones permitidas: `.pdf`, `.docx`, `.xlsx`, `.pptx`. Tamaño máximo: **10MB**.
- **Seguridad de Password:** Validadores estándar de Django activos (longitud, similitud, tipos de caracteres).
- **Sesión:** Expira tras **15 minutos** de inactividad (`SESSION_COOKIE_AGE = 900`).
- **Bloqueo:** Tras múltiples intentos fallidos (lógica en `UsuarioService`), la cuenta se bloquea temporalmente.

---

## 8. Seguridad
- **CSRF:** Protección activa en todos los formularios.
- **XSS:** Escape automático de templates de Django.
- **Clickjacking:** `XFrameOptionsMiddleware` activo.
- **Inyección SQL:** Uso estricto del ORM de Django.
- **Almacenamiento:** Los archivos se guardan con nombres saneados y rutas estructuradas por programa/categoría.

---

## 9. Endpoints Principales (URLs)

| Ruta | Método | Descripción |
| :--- | :--- | :--- |
| `/login/` | GET/POST | Inicio de sesión. |
| `/usuarios/registro/` | GET/POST | Registro público (requiere habilitación posterior). |
| `/documentos/dashboard/` | GET | Panel principal según rol. |
| `/documentos/subir/` | GET/POST | Carga de nuevos archivos. |
| `/documentos/busqueda/` | GET | Búsqueda con filtros avanzados. |
| `/documentos/aprobar/` | GET | Bandeja de entrada para revisores. |
| `/permisos/solicitar/<id>/` | POST | Iniciar flujo Zero-Trust. |
| `/auditoria/` | GET | Visualización de logs (Solo Decana). |

---

## 10. Estado Actual del Sistema

### ✅ Implementado
- Autenticación completa con bloqueo de seguridad y recuperación por token.
- Dashboard dinámico para 3 roles con estadísticas reales.
- Carga de documentos con metadatos (CNA) y almacenamiento organizado.
- Flujo de aprobación/rechazo funcional.
- Sistema Zero-Trust con votación ponderada (2 votos para aprobación).
- Trazabilidad total mediante logs de auditoría.
- Notificaciones internas por acciones clave.

### ⚠️ Limitaciones / Pendientes
- **Previsualización Inline:** Los documentos se descargan directamente al darle click en visualizar archivo, no hay un visor de PDF integrado en la misma página 
- **Edición de Documentos:** Actualmente no se pueden editar los metadatos de un documento una vez subido (solo se puede subir una nueva versión).
- **Eliminación Física:** La eliminación de documentos borra el archivo del disco, pero no hay una "papelera de reciclaje" intermedia.
- **Reportes:** La exportación a CSV/PDF de estadísticas de acreditación está en fase inicial.
