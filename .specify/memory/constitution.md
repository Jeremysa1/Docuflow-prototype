<!--
Sync Impact Report
==================
Version change: 1.0.0 → 1.1.0
Bump rationale: MINOR. El principio VI amplía su guía: nombra el sistema de diseño SIGEA
(static/css/sigea/) y fija la gradación CNA como escala única de color (spec 002, tarea T061).

Modified principles:
- VI. Fidelidad al dominio de acreditación CNA (guía de interfaz ampliada)

Added sections: ninguna. Removed sections: ninguna.

Templates requiring updates:
- .specify/templates/plan-template.md ✅ sin cambios (lee este archivo en tiempo de ejecución).
- .specify/templates/spec-template.md ✅ sin cambios.
- .specify/templates/tasks-template.md ✅ sin cambios.

Follow-up TODOs: ninguno. Eliminar este reporte antes de hacer commit.
-->

# SIGEA (Docuflow) Constitution

Sistema Integrado de Gestión de Evidencias para la Acreditación. Plataforma Django de gestión
documental universitaria con control de acceso Zero-Trust y auditoría completa.

## Core Principles

### I. Zero-Trust y mínimo privilegio (NO NEGOCIABLE)

- Todo acceso se deniega por defecto. Cada vista que expone datos o archivos DEBE estar
  protegida por autenticación y por `@role_required` o `@document_permission_required`
  (o un mecanismo equivalente verificado en el servidor).
- Los archivos se entregan únicamente a través de vistas que validan permisos en tiempo real
  (`FileResponse` / `X-Accel-Redirect`). En producción NO DEBE existir ninguna ruta pública
  que sirva `MEDIA_ROOT` directamente.
- Los documentos marcados `es_sensible=True` son invisibles para docentes salvo aprobación
  explícita: se requieren 2 votos a favor (Autor, Coordinador o Decana) y un solo voto en
  contra deniega la solicitud. Este flujo NO DEBE debilitarse sin enmendar esta constitución.
- Los usuarios recién registrados NO PUEDEN iniciar sesión hasta que la Decana los habilite.
- La autorización se valida siempre en el servidor; ocultar un botón en la plantilla no
  cuenta como control de acceso.

Razón: el sistema custodia evidencias institucionales y documentos confidenciales. Una sola
ruta sin control rompe la promesa central del producto.

### II. Trazabilidad y auditoría inmutable (NO NEGOCIABLE)

- Toda acción que cambie estado sobre documentos, versiones, permisos, solicitudes o
  usuarios DEBE registrar un evento de auditoría con usuario, acción, objeto, fecha/hora e IP.
  Los intentos de acceso denegados también DEBEN registrarse.
- Los registros de auditoría son de solo lectura: NO DEBEN poder crearse, editarse ni
  borrarse desde la interfaz ni desde el admin.
- Un documento nunca se sobrescribe: cada cambio de archivo crea una nueva versión y el
  historial previo se conserva y sigue siendo descargable para quien tenga permiso.
- Aprobaciones y rechazos DEBEN guardar quién decidió y, en el caso de rechazo, el motivo.

Razón: los procesos de acreditación exigen demostrar quién hizo qué y cuándo; la auditoría
es evidencia, no un log de depuración.

### III. Lógica de negocio en la capa de servicios

- La lógica de negocio vive en `apps/<app>/services.py` o `core/services/`. Las vistas se
  limitan a validar la petición, invocar servicios y renderizar o redirigir.
- Cada app de Django (`usuarios`, `documentos`, `permisos`, `versiones`, `auditoria`,
  `notificaciones`) es dueña de sus modelos. Otra app accede a ellos mediante su servicio
  público, no modificando sus tablas directamente.
- El acceso a datos usa el ORM de Django. SQL crudo solo se permite parametrizado y con una
  justificación escrita en el código.
- Las consultas de listados y paneles NO DEBEN introducir N+1: usar `select_related` /
  `prefetch_related` o agregados, y cubrirlo con pruebas cuando la vista sea crítica.

Razón: mantener reglas como el voto Zero-Trust en un único lugar las hace probables y evita
que una vista nueva las salte.

### IV. Seguridad por defecto y configuración fuera del código

- Secretos y credenciales (`SECRET_KEY`, base de datos, correo) se leen de variables de
  entorno. NUNCA se versionan `.env`, respaldos de `.env`, `media/` ni datos reales.
- `DEBUG` es `False` por defecto. Los endurecimientos de producción (HTTPS, HSTS, cookies
  seguras, `nosniff`, `X-Frame-Options`, CSRF) NO DEBEN desactivarse fuera de desarrollo.
- Las subidas se validan en el servidor: extensiones permitidas (`.pdf`, `.docx`, `.xlsx`,
  `.pptx`), tamaño máximo configurado (10 MB) y nombres de archivo saneados.
- Sesiones de 15 minutos de inactividad y bloqueo temporal tras intentos fallidos de login
  se mantienen salvo enmienda de esta constitución.
- Las dependencias se fijan con versión exacta en `requirements.txt` y su cierre transitivo
  en `requirements.lock`. Agregar una dependencia exige actualizar ambos.

Razón: el proyecto ya pasó auditorías de seguridad (`gestion_documental/informes/`); cada
cambio debe preservar ese nivel en lugar de reabrir hallazgos cerrados.

### V. Pruebas automatizadas como puerta de calidad

- Toda funcionalidad nueva o corrección de error DEBE incluir pruebas con `django.test`
  (`TestCase` o `Client`) ejecutables con `python manage.py test`.
- Son obligatorias las pruebas para cambios en: control de acceso y permisos, flujo de
  aprobación, votación Zero-Trust, versionado, auditoría y autenticación. Deben cubrir el
  caso permitido y al menos un caso denegado.
- Un cambio no se integra si `python manage.py check` o la suite de pruebas fallan.
- Los scripts de QA ejecutados con `manage.py shell` (`scripts/qa/qa_test_part*.py`,
  `scripts/qa/qa_accesos.py`) son herramientas heredadas; no sustituyen pruebas automatizadas nuevas.

Razón: los flujos de seguridad fallan en silencio; solo una prueba que verifica el rechazo
demuestra que el control existe.

### VI. Fidelidad al dominio de acreditación CNA

- Todo documento de evidencia DEBE clasificarse por factor CNA, programa académico y estado;
  los metadatos obligatorios se validan al subir.
- Los roles del dominio son `DECANA`, `COORDINADOR` y `DOCENTE_PLANTA`. Añadir o cambiar un
  rol requiere especificación propia y revisión de todas las reglas de permiso afectadas.
- La interfaz, mensajes y documentación de usuario se escriben en español (`es-co`), con
  zona horaria `America/Bogota`.
- La interfaz usa el sistema de diseño SIGEA (`static/css/sigea/`, tokens en `tokens.css`,
  azul de marca `#142a59` y blanco) y los componentes de `templates/componentes/` con el tag
  `{% load sigea %}`; no se introducen frameworks de UI paralelos ni colores, tamaños o estilos
  en línea fuera de los tokens (lo vigila `tests/test_reglas_diseno.py`).
- La gradación de cumplimiento CNA (sin evidencia, no se cumple, insatisfactorio, aceptable,
  alto grado, pleno) es la única escala de color para el avance, y significa lo mismo en toda la
  interfaz.

Razón: el valor del sistema es organizar evidencias para la acreditación; los datos mal
clasificados no sirven como evidencia.

## Restricciones técnicas y de dominio

- **Stack**: Python 3.12, Django 6.1, PostgreSQL (driver `psycopg2`), WhiteNoise para
  estáticos, `django-unfold` para el admin, plantillas Django con CSS y JavaScript sin
  framework.
- **Base de datos**: PostgreSQL es el único motor soportado. Cada cambio de modelo incluye su
  migración en el mismo cambio; las migraciones que borran datos requieren plan de respaldo.
- **Almacenamiento**: archivos en `MEDIA_ROOT`, organizados por programa y categoría,
  servidos solo por vistas con verificación de permisos (Principio I).
- **Rendimiento**: los paneles y la búsqueda DEBEN responder sin consultas N+1; las cachés
  existentes se invalidan explícitamente cuando cambian los datos que muestran.
- **Exportaciones**: reportes en Excel (`openpyxl`) y PDF (`reportlab`) respetan los mismos
  permisos que la vista que los origina.

## Flujo de desarrollo y puertas de calidad

1. Las funcionalidades nuevas siguen el flujo Spec Kit: `/speckit-specify` →
   `/speckit-plan` → `/speckit-tasks` → `/speckit-implement`. El plan DEBE pasar el
   "Constitution Check" antes de implementar.
2. Antes de integrar un cambio se ejecutan `python manage.py check`,
   `python manage.py makemigrations --check` y `python manage.py test`; todos DEBEN pasar.
3. Los cambios en autenticación, permisos, descargas o auditoría requieren una revisión de
   seguridad explícita y documentada (en la descripción del PR o en `informes/`).
4. La documentación técnica (`gestion_documental/documentacion/manual_tecnico.md`) se
   actualiza en el mismo cambio cuando se modifica un flujo, rol, endpoint o validación.
5. Los commits no incluyen secretos, archivos de `media/`, entornos virtuales ni artefactos
   generados.

## Governance

- Esta constitución prevalece sobre cualquier otra práctica o guía del repositorio. Si una
  guía la contradice, se corrige la guía.
- **Enmiendas**: se proponen mediante un cambio a `.specify/memory/constitution.md` con su
  justificación y el plan de migración del código afectado; las aprueba el responsable del
  proyecto.
- **Versionado** (SemVer): MAJOR al eliminar o redefinir un principio de forma incompatible;
  MINOR al añadir un principio o sección, o ampliar materialmente una guía; PATCH para
  aclaraciones y redacción.
- **Cumplimiento**: cada plan (`/speckit-plan`) y cada revisión de código verifican estos
  principios. Cualquier excepción se documenta en la tabla "Complexity Tracking" del plan con
  su justificación y alternativa descartada.
- **Guía de ejecución**: para detalles operativos consultar
  `gestion_documental/documentacion/manual_tecnico.md`.

**Version**: 1.1.0 | **Ratified**: 2026-11-06 | **Last Amended**: 2026-11-07
