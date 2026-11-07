# Implementation Plan: Cierre de riesgos medios y bajos

**Branch**: `004-riesgos-medios-bajos` | **Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

## Technical Context

Django 6.1.3 (CSP nativa en `django.middleware.csp`), PostgreSQL, caché LocMem, `throttle_fijo` y `obtener_ip_cliente` ya existentes en `core/utils/helpers.py`.

## Constitution Check

- Zero-Trust: M5 y M6 reducen exposición y privilegios. ✅
- Revisión de seguridad documentada: `informes/revision-seguridad-004-2026-11-07.md`. ✅
- Sin dependencias nuevas. ✅

## Design

| Hallazgo | Dónde | Cómo |
|---|---|---|
| M2 | `apps/usuarios/services.py` | Contadores en caché por IP y por cuenta+IP; se retira el bloqueo global por cuenta |
| M3 | `services.py`, `views.py` | La confirmación enmascara el correo escrito; errores de código genéricos |
| M4 | `core/validators.py`, `settings.py` | `ComplejidadValidator` (mayúscula y carácter especial) en `AUTH_PASSWORD_VALIDATORS`; `cambiar_contrasena` usa `validate_password` |
| M5 | `apps/documentos/services.py`, `busqueda_avanzada.html` | Filtros que excluyen sensibles sin acceso al buscar por descripción o autor; autor oculto |
| M6 | `DocumentoService.aprobar_documento` / `rechazar_documento` | `ReglaNegocioError` si no está en revisión o si el revisor es el autor; las vistas muestran el mensaje; la cola oculta la acción en las propias |
| M7 | `views.editar_documento`, `subir_documento`, `forms.py` | Vuelta a revisión; programa fijado al del docente |
| M8 | `services.crear_usuario`, vista y plantilla de invitación | `default_token_generator` + enlace `/login/invitacion/<uid>/<token>/` |
| M9 | `views.registro_view` | `EmailValidator` + `throttle_fijo` por IP |
| Bajo | `settings.py` | `LOGIN_REDIRECT_URL = 'documentos:dashboard'` |
| Bajo | `core/utils/helpers.py` | Firma `%PDF-` y ZIP OOXML con su carpeta (`word/`, `xl/`, `ppt/`) |
| Bajo | `settings.py`, `core/middleware.py`, `static/js/sigea.js` | `SECURE_CSP`, middleware que omite `/admin/`, scripts en línea movidos a `sigea.js` |
