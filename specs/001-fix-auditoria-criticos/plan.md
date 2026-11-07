# Implementation Plan: Corrección de hallazgos críticos y altos de la auditoría

**Branch**: `001-fix-auditoria-criticos` | **Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-fix-auditoria-criticos/spec.md`

## Summary

Se corrigen 10 hallazgos (C1–C3, A1–A7) sin cambiar el modelo de negocio:

- se repara la bandeja de aprobación;
- se elimina el XSS del resaltado de búsqueda;
- la IP de auditoría se obtiene de forma confiable y se amplía el catálogo de eventos auditados;
- las versiones reemplazan el archivo vigente con numeración serializada;
- un middleware cierra la sesión de usuarios deshabilitados;
- las notificaciones a revisores salen de un helper único de facultad;
- la vista previa se sirve por una vista protegida, solo para PDF;
- se actualizan dependencias y se ignoran respaldos de `.env`.

Cada corrección lleva pruebas `django.test` con el caso permitido y el denegado.

## Technical Context

**Language/Version**: Python 3.12.5

**Primary Dependencies**: Django 6.1 → 6.1.3, django-unfold 0.105.0, WhiteNoise 6.12, openpyxl,
reportlab; se retira Pillow (sin uso, ver research R8)

**Storage**: PostgreSQL (psycopg2); archivos en `MEDIA_ROOT` servidos solo por vistas con permiso

**Testing**: `python manage.py test <etiquetas>` (`django.test.TestCase` + `Client`)

**Target Platform**: servidor Linux/Windows detrás de Nginx opcional (`X-Accel-Redirect`)

**Project Type**: aplicación web Django monolítica (MVT + capa de servicios)

**Performance Goals**: sin regresión; las pruebas de `tests/test_performance.py` deben seguir
pasando (sin N+1 nuevos)

**Constraints**: sin dependencias nuevas; migraciones solo de `choices` (sin pérdida de datos);
mensajes de error genéricos al usuario

**Scale/Scope**: 1 facultad, ~10 usuarios, cientos de documentos; 6 apps tocadas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple el plan | Estado |
|-----------|------------------------|--------|
| I. Zero-Trust | La vista previa pasa a una vista con `usuario_tiene_acceso`; se elimina el servido directo de `/media/` incluso en DEBUG; los enlaces de versiones usan la descarga protegida. | ✅ |
| II. Auditoría inmutable | La IP sale de una fuente confiable y validada; el catálogo queda con 18 acciones nuevas o etiquetadas; los accesos denegados se registran; el admin sigue de solo lectura. | ✅ |
| III. Capa de servicios | Lógica nueva en servicios (`VersionService`, `NotificacionService.notificar_revisores`, `AuditService`); las vistas solo orquestan. Sin SQL crudo. | ✅ |
| IV. Seguridad por defecto | Dependencias sin CVE y pins actualizados en `requirements.txt`, `requirements.lock` y `_PINS_CRITICOS`; `.env*` ignorado; `TRUSTED_PROXY_COUNT=0` por defecto. | ✅ |
| V. Pruebas | Nuevo módulo de pruebas por historia; `check`, `makemigrations --check` y la suite pasan. Se renombra el script heredado que muta datos al importarse (research R10). | ✅ |
| VI. Dominio CNA | Roles y flujos sin cambios; textos en español. | ✅ |

Sin violaciones: no hace falta "Complexity Tracking".

**Re-check post-diseño**: ✅. El diseño de Phase 1 no introduce dependencias ni excepciones
nuevas. Los cambios de modelo se limitan a `choices` de `RegistroAuditoria.accion`.

## Project Structure

### Documentation (this feature)

```text
specs/001-fix-auditoria-criticos/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── rutas.md
├── checklists/requirements.md
└── tasks.md            # /speckit-tasks
```

### Source Code (repository root)

```text
gestion_documental/
├── .gitignore                         # A7
├── requirements.txt / requirements.lock   # A5
├── config/
│   ├── settings.py                    # A5 pins, A2 middleware, C3 TRUSTED_PROXY_COUNT
│   └── urls.py                        # A4 quitar static(MEDIA_URL)
├── core/
│   ├── middleware.py                  # A2 (nuevo)
│   ├── services/audit_service.py      # C3, A6
│   └── utils/helpers.py               # enmascarar_email, mensaje genérico
├── apps/
│   ├── auditoria/models.py + migración  # A6 choices
│   ├── auditoria/templates/auditoria/lista.html   # A6 filtro y badges
│   ├── documentos/views.py, urls.py, services.py  # C1, A3, A4, A6
│   ├── documentos/templates/documentos/busqueda_avanzada.html  # C2
│   ├── documentos/templates/documentos/detalle.html            # A4
│   ├── notificaciones/services.py     # A3 notificar_revisores
│   ├── permisos/services.py, views.py # A3, A6
│   ├── usuarios/services.py, views.py # A6
│   ├── versiones/services.py, views.py, templates/versiones/lista.html  # A1, A4, A6
└── tests/
    ├── qa_accesos.py                  # renombrado desde test_accesos.py (R10)
    └── test_correcciones_auditoria.py # pruebas nuevas
```

**Structure Decision**: se mantiene la estructura Django existente (apps + `core/`). Solo se
añaden `core/middleware.py`, una migración de `auditoria` y un módulo de pruebas.

## Complexity Tracking

Sin violaciones de la constitución.
