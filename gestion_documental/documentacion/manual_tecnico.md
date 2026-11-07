# Documentación Técnica: SIGEA

## 1. Descripción General del Sistema
**Nombre:** SIGEA
**Propósito:** Plataforma institucional para la gestión, acreditación y control de documentos universitarios. Permite la centralización de evidencias para procesos de calidad académica (CNA), con flujos estrictos de aprobación y control de acceso granular.
**Contexto de Uso:** Facultades universitarias que requieren organizar documentación por programas académicos, factores de acreditación y roles de responsabilidad.

### Stack Tecnológico
- **Framework Principal:** Django 4.2+
- **Lenguaje:** Python 3.x
- **Base de Datos:** PostgreSQL
- **Frontend:** plantillas Django + sistema de diseño SIGEA (`static/css/sigea/`, CSS propio por capas) + iconos Lucide en sprite local + JavaScript sin framework (`static/js/sigea.js`)
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
2. Se notifica a la Coordinadora de facultad (única para todos los programas, sin filtrar por programa) mediante `NotificacionService.notificar_revisores`. Si no hay Coordinadora activa, se notifica a la Decana. Lo que sube la Coordinadora lo revisa la Decana.
3. El Coordinador/Decana revisa y selecciona `APROBAR` o `RECHAZAR` (con comentario).
4. El sistema registra el cambio de estado y notifica al autor.

### Versiones
1. Una versión nueva (o restaurada) pasa a ser el **archivo vigente**: es lo que entregan la descarga y la vista previa.
2. Si el documento todavía no tenía versiones, el archivo original se guarda antes como **v1**, así nunca se pierde.
3. Si la sube un **docente** sobre un documento `APROBADO` o `RECHAZADO`, vuelve a `PENDIENTE` y se notifica a la revisora. Las versiones de la Decana o la Coordinadora mantienen el estado.
4. La numeración se calcula con la fila del documento bloqueada (`select_for_update`): no se repiten números.

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
- **Archivos solo por vistas con permiso:** `MEDIA_ROOT` no se sirve por URL directa en ningún modo, ni siquiera en `DEBUG`. Los archivos salen únicamente por `descargar_doc`, `descargar_version` y `vista_previa`, que comprueban `PermisoService.usuario_tiene_acceso`.
- **Vista previa:** solo PDF, en línea (`Content-Disposition: inline`, `X-Content-Type-Options: nosniff`). Word, Excel y PowerPoint ofrecen la descarga protegida; ningún documento se envía a servicios externos.
- **Cuentas deshabilitadas:** `core.middleware.CuentaHabilitadaMiddleware` cierra la sesión de cualquier cuenta con `esta_habilitado=False` o `is_active=False` en su siguiente petición. Los superusuarios quedan exentos para no bloquear el admin.
- **IP de auditoría:** `TRUSTED_PROXY_COUNT` (variable de entorno, por defecto `0`).
  - Con 0 se usa `REMOTE_ADDR` y se ignora `X-Forwarded-For`, que el cliente puede falsificar.
  - Detrás de un Nginx se configura en `1`.
  - Un valor que no sea una IP válida se guarda vacío y nunca bloquea la acción.
- **Errores:** los mensajes al usuario son genéricos y el detalle técnico va al log del servidor (`logger.exception`). Solo los errores de negocio (`ReglaNegocioError`) muestran su texto.

### Eventos auditados (`RegistroAuditoria.Accion`)
| Grupo | Acciones |
| :--- | :--- |
| Documentos | `SUBIO`, `EDITO_METADATOS`, `NUEVA_VERSION`, `MODIFICO` (restaurar versión), `DESCARGO`, `VISUALIZO`, `APROBO`, `RECHAZO`, `ELIMINO`, `ACTUALIZO` (restaurar de papelera) |
| Sesión | `LOGIN`, `LOGIN_FALLIDO` (correo enmascarado si no existe), `LOGOUT` |
| Accesos | `SOLICITO_ACCESO`, `VOTO_ACCESO`, `APROBO_ACCESO`, `RECHAZO_ACCESO`, `REVOCO_ACCESO`, `ACCESO_DENEGADO` |
| Usuarios | `CREO_USUARIO`, `HABILITO_USUARIO`, `DESHABILITO_USUARIO`, `ELIMINO_USUARIO`, `ACTUALIZO_USUARIO` |

---

## 8b. Sistema de diseño (spec 002)

- **Dirección:** "Matriz de autoevaluación". El avance se expresa siempre como *cantidad frente a meta* y se colorea con la gradación CNA (0 sin evidencia, 1–59 % no se cumple, 60–69 % insatisfactorio, 70–79 % aceptable, 80–89 % alto grado, ≥90 % pleno). Detalle visual en `DESIGN.md`.
- **CSS:** `static/css/sigea/main.css` importa por capas `tokens.css` (únicos colores, tamaños y espacios permitidos), `base.css`, `componentes.css` (`sg-*`), `graficos.css` (huella, matriz, pulso), `shell.css` (riel lateral y barra móvil) y `paginas.css`.
- **Plantillas:** `templates/base.html` (shell), `templates/componentes/` (banner_huella, matriz, cola_revision, tiempos, pulso, estado_vacio, chip_factor, estado_documento) y `templates/403.html`, `404.html`, `500.html`.
- **Template tags** (`{% load sigea %}`, en `core/templatetags/sigea.py`): `icono`, `chip_factor`, `chip_factor_codigo`, `estado_documento`, filtros `plural` e `iniciales`.
- **Métricas:** `apps/documentos/metricas.py` (`MetricasService`): `gradacion`, `huella_facultad`, `matriz_factor_programa`, `cola_revision`, `tiempos_revision`, `pulso_30_dias` (directivas) y `huella_personal` (docente: solo sus datos). Se cachean con `conteo_cacheado` y se invalidan con `bump_stats()`.
- **Navegación por rol:** `apps/usuarios/context_processors.navegacion`.
- **Vigilancia:** `tests/test_reglas_diseno.py` falla si una plantilla usa estilos en línea que no sean variables de datos, colores hex, emojis, o si el CSS usa colores fuera de tokens, texto menor de 12 px o `!important` fuera de `base.css`.
- **Fuentes e iconos:** Public Sans (OFL) en `static/fonts/` e iconos Lucide (ISC) en `static/icons/lucide.svg`, sin CDN. Para añadir un icono: agrega su `<symbol>` al sprite (en DEBUG, `{% icono %}` falla si no existe).

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
| `/documentos/<id>/descargar/` | GET | Descarga protegida del archivo vigente. |
| `/documentos/<id>/vista-previa/` | GET | Vista previa protegida (solo PDF). |
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
- **Previsualización de Office:** solo los PDF se ven dentro de la página; Word, Excel y PowerPoint se descargan.
- **Pruebas:** ejecutar con `manage.py test tests`. Los scripts heredados `tests/qa_*.py` trabajan sobre la base real y se ejecutan a mano con `manage.py shell`; no deben renombrarse a `test_*.py`.
- **Edición de Documentos:** Actualmente no se pueden editar los metadatos de un documento una vez subido (solo se puede subir una nueva versión).
- **Eliminación Física:** La eliminación de documentos borra el archivo del disco, pero no hay una "papelera de reciclaje" intermedia.
- **Reportes:** La exportación a CSV/PDF de estadísticas de acreditación está en fase inicial.
