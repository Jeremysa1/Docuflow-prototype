# Tasks: Cierre de riesgos medios y bajos

## Phase 1: Foundational

- [X] T001 Validador de complejidad en gestion_documental/core/validators.py y AUTH_PASSWORD_VALIDATORS en gestion_documental/config/settings.py
- [X] T002 Validación de firma de contenido en gestion_documental/core/utils/helpers.py y su uso en gestion_documental/apps/documentos/forms.py

## Phase 2: User Story 1 - Acceso (P1)

- [X] T003 [US1] Límites por IP y por cuenta+IP en el login (M2) en gestion_documental/apps/usuarios/services.py
- [X] T004 [US1] Recuperación sin enumeración (M3) en gestion_documental/apps/usuarios/services.py y views.py
- [X] T005 [US1] cambiar_contrasena con validate_password (M4) en gestion_documental/apps/usuarios/services.py
- [X] T006 [US1] Registro con correo validado y límite por IP (M9) en gestion_documental/apps/usuarios/views.py

## Phase 3: User Story 2 - Invitación (P1)

- [X] T007 [US2] Invitación al crear usuario (M8): servicio, vista, ruta y plantilla en gestion_documental/apps/usuarios/

## Phase 4: User Story 3 - Revisión (P1)

- [X] T008 [US3] Controles de estado y autor al aprobar y rechazar (M6) en gestion_documental/apps/documentos/services.py y views.py
- [X] T009 [US3] Ocultar Aprobar en evidencias propias en gestion_documental/templates/componentes/cola_revision.html y aprobar_documentos.html
- [X] T010 [US3] Edición del docente devuelve a revisión y programa fijado (M7) en gestion_documental/apps/documentos/views.py y forms.py

## Phase 5: User Story 4 - Sensibles (P2)

- [X] T011 [US4] Búsqueda sin autor ni descripción de sensibles sin acceso (M5) en gestion_documental/apps/documentos/services.py y busqueda_avanzada.html

## Phase 6: User Story 5 - Defensa en profundidad (P3)

- [X] T012 [US5] LOGIN_REDIRECT_URL a una ruta existente en gestion_documental/config/settings.py
- [X] T013 [US5] Scripts en línea movidos a gestion_documental/static/js/sigea.js
- [X] T014 [US5] CSP con middleware que omite /admin/ en gestion_documental/core/middleware.py y settings.py

## Phase 7: Polish

- [X] T015 Pruebas de cada FR en gestion_documental/tests/test_riesgos_004.py
- [X] T016 Suite completa en verde
- [X] T017 Informe gestion_documental/informes/revision-seguridad-004-2026-11-07.md con los pasos de M11
