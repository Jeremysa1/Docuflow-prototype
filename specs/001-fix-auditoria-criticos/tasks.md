# Tasks: Corrección de hallazgos críticos y altos de la auditoría

**Input**: Design documents from `/specs/001-fix-auditoria-criticos/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/rutas.md, quickstart.md

**Tests**: obligatorias por el principio V de la constitución. Cada historia incluye el caso
permitido y al menos un caso denegado.

**Organization**: tareas agrupadas por historia de usuario (US1–US8 de spec.md).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: historia de usuario a la que pertenece

## Path Conventions

Rutas relativas a la raíz del repositorio. El proyecto Django vive en `gestion_documental/`.
Las pruebas se ejecutan desde `gestion_documental/` con `./venv/Scripts/python.exe manage.py test`.

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Renombrar `gestion_documental/tests/test_accesos.py` a `gestion_documental/tests/qa_accesos.py` y actualizar el comando del docstring, para que `manage.py test` no lo importe y mutile la BD de desarrollo (research R10)
- [X] T002 [P] Crear `gestion_documental/tests/factories.py` con helpers `crear_programa()`, `crear_usuario(rol, programa=None, habilitado=True)`, `crear_categoria()`, `crear_documento(autor, estado='PENDIENTE', es_sensible=False, nombre='doc.pdf')` usando `SimpleUploadedFile` y un `MEDIA_ROOT` temporal (patrón de `tests/test_performance.py`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: las historias US3–US7 dependen de estas tareas.

- [X] T003 Ampliar `RegistroAuditoria.Accion` en `gestion_documental/apps/auditoria/models.py` con los 18 códigos de research R9 (`max_length=20`, etiquetas en español: EDITO_METADATOS "Editó metadatos", ACTUALIZO "Restauró documento", NUEVA_VERSION "Subió nueva versión", VISUALIZO "Visualizó documento", ACCESO_DENEGADO "Acceso denegado", LOGIN "Inició sesión", LOGIN_FALLIDO "Intento de sesión fallido", LOGOUT "Cerró sesión", SOLICITO_ACCESO "Solicitó acceso", VOTO_ACCESO "Votó acceso sensible", APROBO_ACCESO "Aprobó acceso", RECHAZO_ACCESO "Rechazó acceso", REVOCO_ACCESO "Revocó acceso", CREO_USUARIO "Creó usuario", HABILITO_USUARIO "Habilitó usuario", DESHABILITO_USUARIO "Deshabilitó usuario", ELIMINO_USUARIO "Eliminó usuario", ACTUALIZO_USUARIO "Cambió rol o programa")
- [X] T004 Generar la migración de `choices` con `manage.py makemigrations auditoria` en `gestion_documental/apps/auditoria/migrations/` y aplicarla
- [X] T005 [P] Añadir en `gestion_documental/core/utils/helpers.py` la función `enmascarar_email(email)` (primeros 2 caracteres + `***` + `@dominio`; 1 carácter si el local tiene ≤2; `***` si no hay `@`) y la excepción `ReglaNegocioError(Exception)`; hacer que `UsuarioService.confirmar_email_recuperacion` en `gestion_documental/apps/usuarios/services.py` use `enmascarar_email`
- [X] T006 [P] Añadir `NotificacionService.notificar_revisores(documento, mensaje, actor=None, incluir_decana=False, extra=None)` en `gestion_documental/apps/notificaciones/services.py`: destinatarios = usuarios `rol='COORDINADOR', is_active=True, esta_habilitado=True`; si no hay ninguno o `incluir_decana`, añadir `rol='DECANA'` activas; añadir `extra` (iterable); sin duplicados; excluir `actor`

**Checkpoint**: catálogo de auditoría, helpers y notificación a revisores listos.

---

## Phase 3: User Story 1 - Revisar y aprobar documentos sin errores (P1) 🎯 MVP

**Goal**: la bandeja `/documentos/aprobar/` carga para directivas con todos los filtros (C1).

**Independent Test**: Decana y Coordinadora abren la bandeja con y sin `?urgente=1`; un docente recibe 403.

### Tests for User Story 1

- [X] T007 [P] [US1] Escribir `gestion_documental/tests/test_us1_aprobacion.py`: 200 para DECANA y COORDINADOR en `/documentos/aprobar/`, `?estado=APROBADO` y `?urgente=1`; `docs_urgentes_count` igual al número de pendientes con `fecha_modificacion` de hace más de 3 días; 403 para DOCENTE_PLANTA

### Implementation for User Story 1

- [X] T008 [US1] En `aprobar_documentos_view` de `gestion_documental/apps/documentos/views.py`, añadir `urgentes=Count('id', filter=Q(estado='PENDIENTE', fecha_modificacion__lt=hace_3_dias))` al `aggregate`, derivar `hay_urgentes` de ese valor, eliminar la consulta `.exists()` y pasar `docs_urgentes_count=conteo['urgentes']`
- [X] T009 [US1] En las vistas `aprobar_documento`, `aprobar_documentos_lote` y `rechazar_documento` de `gestion_documental/apps/documentos/views.py`, reemplazar `f'Error ...: {e}'` por mensajes fijos y `logger.exception` (research R11)

**Checkpoint**: US1 funcional y probada.

---

## Phase 4: User Story 2 - Búsqueda segura frente a contenido malicioso (P1)

**Goal**: el resaltado nunca interpreta HTML (C2).

**Independent Test**: documento con título `<img src=x onerror=alert(1)>`; la página de búsqueda lo contiene escapado y el script de resaltado no usa `innerHTML`.

### Tests for User Story 2

- [X] T010 [P] [US2] Escribir `gestion_documental/tests/test_us2_busqueda.py`: la respuesta de `/documentos/busqueda/?q=img` contiene `&lt;img src=x onerror=alert(1)&gt;` y no `<img src=x onerror`; la plantilla renderizada no contiene `innerHTML` dentro del bloque de resaltado

### Implementation for User Story 2

- [X] T011 [US2] Reescribir el resaltado en `gestion_documental/apps/documentos/templates/documentos/busqueda_avanzada.html` (líneas ~322-334): recorrer los nodos de texto de cada `.sa-highlight-target`, partir con la regex escapada y construir nodos `mark.highlight-amber` y nodos de texto, sin `innerHTML`
- [X] T012 [P] [US2] Quitar el `padding` horizontal de `.highlight-amber` en `gestion_documental/static/css/ui-ux-pro.css` (línea ~3731) para que la palabra no se separe

**Checkpoint**: US2 funcional y probada.

---

## Phase 5: User Story 3 - Auditoría confiable y completa (P1)

**Goal**: IP confiable y catálogo completo de eventos auditados (C3, A6).

**Independent Test**: cada evento de FR-007 deja un registro; las cabeceras `X-Forwarded-For` falsas o inválidas no alteran la IP ni bloquean la acción.

### Tests for User Story 3

- [X] T013 [P] [US3] Escribir `gestion_documental/tests/test_us3_auditoria.py`, sección IP: con `TRUSTED_PROXY_COUNT=0` y `X-Forwarded-For: 8.8.8.8` se registra `127.0.0.1`; con `no-es-una-ip` la descarga responde con el archivo y se registra la IP real; con `override_settings(TRUSTED_PROXY_COUNT=1)` y `X-Forwarded-For: 1.1.1.1, 9.9.9.9` se registra `9.9.9.9`
- [X] T014 [US3] Ampliar `gestion_documental/tests/test_us3_auditoria.py`, sección eventos: LOGIN, LOGIN_FALLIDO con correo inexistente (detalle `ab***@dominio`, `usuario` nulo), LOGOUT, SOLICITO_ACCESO, VOTO_ACCESO, APROBO_ACCESO, RECHAZO_ACCESO, REVOCO_ACCESO, CREO/HABILITO/DESHABILITO/ELIMINO/ACTUALIZO_USUARIO, ACCESO_DENEGADO en detalle y en descarga; `get_accion_display()` devuelve la etiqueta en español para EDITO_METADATOS y ACTUALIZO

### Implementation for User Story 3

- [X] T015 [US3] Añadir `TRUSTED_PROXY_COUNT = int(os.getenv('TRUSTED_PROXY_COUNT', '0'))` en `gestion_documental/config/settings.py` y documentarlo en `gestion_documental/.env.example`
- [X] T016 [US3] Reescribir `AuditService._get_client_ip` en `gestion_documental/core/services/audit_service.py`: con `TRUSTED_PROXY_COUNT=0` usar `REMOTE_ADDR`; con N>0 tomar la entrada N-ésima desde la derecha de `X-Forwarded-For` (o `REMOTE_ADDR` si faltan entradas); validar con `ipaddress.ip_address`; devolver `None` si es inválida
- [X] T017 [US3] Auditar LOGIN, LOGIN_FALLIDO (con `enmascarar_email` cuando el correo no existe y el correo del usuario cuando sí existe; incluir bloqueos) y LOGOUT en `UsuarioService.autenticar_usuario` y `cerrar_sesion` de `gestion_documental/apps/usuarios/services.py`
- [X] T018 [US3] Añadir el parámetro `request=None` a `crear_usuario`, `habilitar_usuario`, `deshabilitar_usuario`, `eliminar_usuario` y `actualizar_usuario` en `gestion_documental/apps/usuarios/services.py`, auditar CREO/HABILITO/DESHABILITO/ELIMINO/ACTUALIZO_USUARIO con el correo del usuario afectado en `detalle`, y pasar `request` y `actor` desde `gestion_documental/apps/usuarios/views.py`; reemplazar `str(e)` por `ReglaNegocioError` + mensaje fijo
- [X] T019 [US3] Añadir `request=None` a `solicitar_acceso`, `responder_solicitud_normal`, `votar_acceso_sensible` y `revocar_acceso` en `gestion_documental/apps/permisos/services.py`, auditar SOLICITO_ACCESO, APROBO_ACCESO/RECHAZO_ACCESO, VOTO_ACCESO (más APROBO/RECHAZO_ACCESO al resolverse) y REVOCO_ACCESO, y lanzar `ReglaNegocioError` en lugar de `Exception` para los errores de negocio
- [X] T020 [US3] Actualizar `gestion_documental/apps/permisos/views.py`: pasar `request`, mostrar el texto solo de `ReglaNegocioError` y un mensaje fijo + `logger.exception` para el resto
- [X] T021 [US3] Auditar ACCESO_DENEGADO en `detalle_documento` (rama `PermissionError`) y en `descargar_documento_view` / `descargar_version_view` de `gestion_documental/apps/documentos/views.py`, y en `lista_versiones` / `crear_version` / `restaurar_version_view` de `gestion_documental/apps/versiones/views.py`; reemplazar `f'Error ...: {e}'` por mensajes fijos y `logger.exception`
- [X] T022 [US3] En `gestion_documental/apps/auditoria/templates/auditoria/lista.html`, generar el `<select name="accion">` desde `Accion.choices` (pasado por `gestion_documental/apps/auditoria/views.py`) y añadir badges para LOGIN_FALLIDO y ACCESO_DENEGADO (peligro) y para LOGIN/LOGOUT (neutral)

**Checkpoint**: US3 funcional y probada.

---

## Phase 6: User Story 4 - Versiones que reemplazan la evidencia vigente (P2)

**Goal**: la versión nueva es la vigente, con revisión y auditoría (A1).

**Independent Test**: un docente sube v2 de un documento aprobado: la descarga entrega v2, el estado es PENDIENTE, la Coordinadora está notificada y existe NUEVA_VERSION.

### Tests for User Story 4

- [X] T023 [P] [US4] Escribir `gestion_documental/tests/test_us4_versiones.py`: docente + APROBADO → PENDIENTE y notificación a la Coordinadora; COORDINADOR + APROBADO → sigue APROBADO; RECHAZADO + docente → PENDIENTE; la descarga devuelve el contenido de v2; registro NUEVA_VERSION; en un documento sin versiones, la primera subida crea la v1 con el archivo original (descargable) y la nueva como v2; dos subidas seguidas producen números consecutivos sin repetir; restaurar actualiza el archivo vigente y audita

### Implementation for User Story 4

- [X] T024 [US4] Reescribir `VersionService.crear_version` en `gestion_documental/apps/versiones/services.py` dentro de `transaction.atomic()` con `Documento.objects.select_for_update().get(pk=...)`: si el documento no tiene ninguna `Version`, crear primero la versión 1 con una copia del archivo original (descripción "Versión inicial cargada por el autor", autor = autor del documento); numerar, crear la `Version` nueva, asignar `documento.archivo = version.archivo.name`, aplicar la regla de estado (solo `DOCENTE_PLANTA` y estado `APROBADO`/`RECHAZADO` → `PENDIENTE`), guardar, auditar `NUEVA_VERSION`, `bump_stats()` y llamar a `notificar_revisores` si pasó a PENDIENTE
- [X] T025 [US4] Ajustar `VersionService.restaurar_version` en `gestion_documental/apps/versiones/services.py` para usar la misma transacción, regla de estado y `notificar_revisores` en vez del filtro por programa

**Checkpoint**: US4 funcional y probada.

---

## Phase 7: User Story 5 - Revisores siempre notificados (P2)

**Goal**: la Coordinadora de facultad recibe todos los avisos (A3).

**Independent Test**: con la Coordinadora sin programa, un docente de cualquier programa sube un documento y ella recibe la notificación.

### Tests for User Story 5

- [X] T026 [P] [US5] Escribir `gestion_documental/tests/test_us5_notificaciones.py`: Coordinadora con `programa_academico=None` notificada al subir un docente de otro programa; sin Coordinadora activa → notifica a la Decana; solicitud sensible → autor, Coordinadora y Decana una sola vez cada uno; restaurar una versión de un documento que queda pendiente → la Coordinadora recibe aviso

### Implementation for User Story 5

- [X] T027 [US5] Reemplazar el filtro por programa en `DocumentoService.crear_documento` de `gestion_documental/apps/documentos/services.py` por `notificar_revisores` (docente → Coordinadora; Coordinadora → Decana con `incluir_decana=True`)
- [X] T028 [US5] Reemplazar el bloque de destinatarios sensibles en `PermisoService.solicitar_acceso` de `gestion_documental/apps/permisos/services.py` por `notificar_revisores(documento, mensaje, actor=solicitante, incluir_decana=True, extra=[documento.autor])`

**Checkpoint**: US5 funcional y probada.

---

## Phase 8: User Story 6 - Sesiones cortadas al deshabilitar (P2)

**Goal**: un usuario deshabilitado o inactivo pierde el acceso en su siguiente petición (A2).

**Independent Test**: cliente con sesión de docente; se deshabilita; la siguiente petición redirige a `/login/` y la sesión queda vacía.

### Tests for User Story 6

- [X] T029 [P] [US6] Escribir `gestion_documental/tests/test_us6_sesiones.py`: docente deshabilitado → 302 a `/login/` y `_auth_user_id` ausente de la sesión; `is_active=False` → igual; superusuario con `esta_habilitado=False` → conserva el acceso; usuario habilitado → 200

### Implementation for User Story 6

- [X] T030 [US6] Crear `gestion_documental/core/middleware.py` con `CuentaHabilitadaMiddleware` (si `user.is_authenticated`, no es superusuario y `not is_active or not esta_habilitado`: `logout`, `messages.error` con texto fijo y `redirect('auth:login')`)
- [X] T031 [US6] Registrar `core.middleware.CuentaHabilitadaMiddleware` después de `MessageMiddleware` (que a su vez va después de `AuthenticationMiddleware`) en `MIDDLEWARE` de `gestion_documental/config/settings.py`

**Checkpoint**: US6 funcional y probada.

---

## Phase 9: User Story 7 - Vista previa protegida (P2)

**Goal**: la vista previa pasa por el control de acceso, solo para PDF, sin terceros (A4).

**Independent Test**: PDF permitido → 200 inline; sin acceso → 403 + ACCESO_DENEGADO; DOCX → 404; `/media/...` → 404 en DEBUG.

### Tests for User Story 7

- [X] T032 [P] [US7] Escribir `gestion_documental/tests/test_us7_vista_previa.py`: `/documentos/<id>/vista-previa/` devuelve `application/pdf`, `Content-Disposition` con `inline` y `X-Content-Type-Options: nosniff` para el autor; 403 y registro ACCESO_DENEGADO para un docente sin permiso; registro VISUALIZO cuando se permite; 404 para un `.docx`; 404 con mensaje genérico (sin rutas ni trazas) si el archivo físico no existe; `override_settings(DEBUG=True)` + GET de la ruta `/media/` real → 404; el HTML de detalle no contiene `/media/` ni `docs.google.com`

### Implementation for User Story 7

- [X] T033 [US7] Añadir `previsualizar_documento(request, documento_id)` en `gestion_documental/apps/documentos/views.py`, que delega en un nuevo `DocumentoService.archivo_para_vista_previa(documento_id, usuario, request)` de `gestion_documental/apps/documentos/services.py` (valida acceso, audita VISUALIZO o ACCESO_DENEGADO, exige extensión `.pdf`; si el archivo físico falta, `Http404` con texto genérico); responder con `FileResponse(content_type='application/pdf', as_attachment=False)` o `X-Accel-Redirect` si `USE_X_ACCEL_REDIRECT`
- [X] T034 [US7] Registrar `path('<int:documento_id>/vista-previa/', views.previsualizar_documento, name='vista_previa')` en `gestion_documental/apps/documentos/urls.py`
- [X] T035 [US7] En `gestion_documental/apps/documentos/templates/documentos/detalle.html`, hacer que el botón "Visualizar archivo" pase `{% url 'documentos:vista_previa' documento.id %}` y la extensión; en `openDocumentModal`, crear el `iframe` con `document.createElement` para PDF y, para Office, mostrar el aviso con enlace a `{% url 'documentos:descargar_doc' documento.id %}`; eliminar Google Docs Viewer
- [X] T036 [P] [US7] En `gestion_documental/apps/versiones/templates/versiones/lista.html`, reemplazar `{{ version.archivo.url }}` por `{% url 'documentos:descargar_version' version.id %}`
- [X] T037 [US7] Eliminar `static(settings.MEDIA_URL, ...)` y sus imports en `gestion_documental/config/urls.py`

**Checkpoint**: US7 funcional y probada.

---

## Phase 10: User Story 8 - Base técnica sin vulnerabilidades ni secretos expuestos (P3)

**Goal**: dependencias sin CVE y respaldos de `.env` ignorados (A5, A7).

**Independent Test**: `pip_audit` sin hallazgos; `git status --ignored` marca `.env.bak` como ignorado.

### Implementation for User Story 8

- [X] T038 [P] [US8] Añadir `.env.*` y `!.env.example` en la sección "Environment variables" de `gestion_documental/.gitignore`
- [X] T039 [US8] Actualizar `gestion_documental/requirements.txt` (`Django==6.1.3`, `brotli==1.2.1`, quitar `Pillow`), `gestion_documental/requirements.lock` (mismas versiones; quitar `pillow`) y `_PINS_CRITICOS` en `gestion_documental/config/settings.py` (Django 6.1.3, sin Pillow)
- [X] T040 [US8] Instalar en el venv (`pip install -r requirements.txt` y `pip uninstall -y pillow`), ejecutar `manage.py check` y la suite; si las migraciones históricas de `usuarios` exigen Pillow, aplicar el fallback `Pillow==13.0.0` en los tres sitios (research R8)
- [X] T041 [US8] Ejecutar `pip_audit -r requirements.txt` y confirmar 0 vulnerabilidades

**Checkpoint**: US8 completa.

---

## Phase 11: Polish & Cross-Cutting Concerns

- [X] T042 Ejecutar `manage.py check`, `makemigrations --check --dry-run` y `manage.py test tests --noinput` desde `gestion_documental/`; todo debe pasar
- [X] T043 [P] Actualizar `gestion_documental/documentacion/manual_tecnico.md`: vista previa (solo PDF, ruta protegida), `TRUSTED_PROXY_COUNT`, eventos auditados, regla de estado de versiones, middleware de cuentas
- [X] T044 Recorrer los escenarios manuales de `specs/001-fix-auditoria-criticos/quickstart.md` en el navegador con el servidor de desarrollo
- [X] T045 Escribir la revisión de seguridad exigida por la constitución (flujo, paso 3) en `gestion_documental/informes/revision-seguridad-001-2026-11-07.md`: cambios en autenticación, sesiones, permisos, descargas y auditoría; amenazas cubiertas; pruebas que lo demuestran; riesgos residuales

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias.
- **Foundational (Phase 2)**: depende de Setup; bloquea US3–US7.
- **US1, US2**: solo dependen de Setup (T002).
- **US3**: depende de T003–T005.
- **US4, US5**: dependen de T003 y T006.
- **US6**: depende de Setup.
- **US7**: depende de T003 (acciones VISUALIZO/ACCESO_DENEGADO).
- **US8**: independiente; conviene al final porque cambia el entorno de ejecución.
- **Polish**: depende de todas.

### User Story Dependencies

- US3 y US7 tocan `documentos/views.py`: hacer T021 antes que T033.
- US3 y US5 tocan `permisos/services.py`: hacer T019 antes que T028.
- US1 y US3 tocan `documentos/views.py`: hacer T008–T009 antes que T021.

### Within Each User Story

Primero las pruebas (deben fallar), después los servicios, las vistas y las plantillas.

### Parallel Opportunities

- T002, T005, T006 en paralelo tras T001.
- Los archivos de prueba T007, T010, T013, T023, T026, T029, T032 son independientes entre sí.
- T012, T036, T038 tocan archivos sin otras tareas pendientes.

## Parallel Example: User Story 7

```text
T032 tests/test_us7_vista_previa.py
T036 versiones/templates/versiones/lista.html
```

## Implementation Strategy

### MVP First

US1 + US2 (los críticos C1 y C2), validar y luego US3 (C3).

### Incremental Delivery

1. Setup + Foundational.
2. US1 → US2 → US3: críticos cerrados.
3. US4 → US5 → US6 → US7: altos funcionales.
4. US8: dependencias y repositorio.
5. Polish: suite completa, manual y recorrido manual.

## Notes

- Total: 45 tareas.
- Fuera de alcance (pendiente): mensajes de error internos en las vistas de eliminar, restaurar y exportar no tocadas aquí (FR-010 se limita a los flujos tocados).
- No hacer commit hasta que el usuario lo pida.
- Nunca ejecutar `manage.py test` antes de T001.
