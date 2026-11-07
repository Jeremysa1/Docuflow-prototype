# Tasks: Rediseño visual "Matriz de autoevaluación"

**Input**: Design documents from `/specs/002-rediseno-matriz-cna/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/tokens.md,
contracts/componentes.md, quickstart.md, `.impeccable/surfaces/gestion-documental-templates-base-html.md`

**Tests**: obligatorias (principio V). Cada historia incluye pruebas de vista por rol y la prueba de
reglas de diseño se amplía a las plantillas migradas.

**Entrega**: tres fases con revisión del usuario (aclaración del 2026-11-07).
- **Fase de entrega 1**: Phase 1–6 (base, shell, paneles de los 3 roles, pulso, errores).
- **Fase de entrega 2**: Phase 7 (pantallas de evidencias).
- **Fase de entrega 3**: Phase 8–9 (gestión, acceso, admin, retiro del CSS heredado, cierre).

Antes de cada edición de interfaz, leer `reference/craft-floor.md` de impeccable.

## Format: `[ID] [P?] [Story] Description`

Rutas relativas a la raíz del repositorio; el proyecto Django está en `gestion_documental/`.

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Descargar Public Sans (OFL, pesos 400/600/700/800) a WOFF2 en `gestion_documental/static/fonts/public-sans/` junto con su licencia `OFL.txt`
- [X] T002 [P] Crear `gestion_documental/static/icons/lucide.svg` con los iconos Lucide usados (ISC, trazo 1,75) como `<symbol id="…">`, y su licencia en `gestion_documental/static/icons/LICENSE-lucide.txt`
- [X] T003 [P] Renombrar `gestion_documental/static/css/ui-ux-pro.css` a `gestion_documental/static/css/legacy.css` sin cambiar su contenido (research R1)
- [X] T004 Crear `gestion_documental/static/css/sigea/main.css` con `@layer legacy, base, componentes, paginas;`, `@import url("../legacy.css") layer(legacy);` y los imports de tokens, base, shell, componentes y gráficos

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: todas las historias dependen de esta fase.

- [X] T005 Escribir `gestion_documental/static/css/sigea/tokens.css` exactamente con `contracts/tokens.md` (color, gradación `--sg-grad-0…5` con `--sg-grad-3: #4a6cc0`, tipografía `--sg-t-1…6`, espacio, radio, movimiento) y `@font-face` de Public Sans con `font-display: swap`
- [X] T006 Escribir `gestion_documental/static/css/sigea/base.css` en `@layer base`: reset, `html{font-size:100%}` (base 16 px), cuerpo con `--sg-fuente` y `tabular-nums`, foco visible `:focus-visible` con 2 px `--sg-accion`, enlace "saltar al contenido", `prefers-reduced-motion` que anula duraciones
- [X] T007 [P] Escribir `gestion_documental/static/css/sigea/componentes.css` en `@layer componentes`: `.sg-btn` (`--primario`, `--secundario`, `--peligro`, `aria-busy`, mínimo 44 px), `.sg-chip` de gradación y de estado (sólido, punteado, tachado, reloj, candado), `.sg-tabla` a tarjetas debajo de 768 px con `data-label`, formularios, avisos, modal de confirmación, estado vacío, paginación
- [X] T008 [P] Escribir `gestion_documental/static/css/sigea/graficos.css`: huella (12 columnas con `--altura`, borde `rgba(255,255,255,.55)`, crecimiento escalonado de 300 ms), matriz (celdas `--sg-grad-*`, desplazamiento propio), barras de cantidad frente a meta, sparkline del pulso
- [X] T009 Crear `gestion_documental/core/templatetags/__init__.py` y `gestion_documental/core/templatetags/sigea.py` con `icono`, `chip_factor`, `estado_documento`, filtros `plural` e `iniciales` según `contracts/componentes.md`
- [X] T010 Escribir `gestion_documental/tests/test_templatetags_sigea.py`: `plural` (1/2/0), `iniciales` (nombre completo, sin apellido, vacío → "?"), `icono` con y sin etiqueta, `chip_factor` con la clase de su nivel
- [X] T011 Crear `gestion_documental/apps/documentos/metricas.py` con `MetricasService.gradacion(aprobados, meta)` según research R3 (0 sin evidencia; 1–59 no se cumple; 60–69 insatisfactorio; 70–79 aceptable; 80–89 alto grado; ≥90 pleno) y mover las metas de `ReporteService.obtener_estadisticas_cna` a una constante compartida `METAS_POR_FACTOR`
- [X] T012 Escribir `gestion_documental/tests/test_metricas.py` con la tabla de umbrales de gradación (0, 1, 59, 60, 69, 70, 79, 80, 89, 90, 120 %) y meta 0
- [X] T013 Crear `gestion_documental/tests/test_reglas_diseno.py` con la lista `PLANTILLAS_MIGRADAS` (vacía al inicio) y comprobaciones de research R11: `style=` solo con variables de datos, sin hex fuera de `tokens.css`, sin `font-size` menor de 12 px ni `!important` en `static/css/sigea/`, sin emojis
- [X] T014 Reescribir `gestion_documental/templates/base.html` como shell nuevo: carga solo `css/sigea/main.css` y `js/sigea.js`; sin Google Fonts ni unpkg; riel lateral azul (destinos por rol), barra superior y barra inferior móvil con "Más", `{% block banner %}`, mensajes como avisos con icono, modal de confirmación accesible; los nombres de bloques existentes se conservan para que las páginas no migradas sigan funcionando
- [X] T015 [P] Escribir `gestion_documental/static/css/sigea/shell.css` (riel de 248 px que se contrae a 72 px, barra inferior móvil de 64 px con áreas de 44 px, hoja "Más", migas, banner)
- [X] T016 Crear `gestion_documental/static/js/sigea.js`: menú y hoja móvil, contracción del riel (preferencia en `localStorage` con try/catch), confirmación modal con foco atrapado (reemplaza `sigeaConfirm` con la misma firma), `aria-busy` en formularios al enviar; búsqueda rápida del navbar migrada desde `main.js` con nodos de texto
- [X] T017 Añadir un context processor `apps/usuarios/context_processors.navegacion` en `gestion_documental/apps/usuarios/context_processors.py` que devuelva los destinos del riel y la barra móvil por rol, y registrarlo en `TEMPLATES` de `gestion_documental/config/settings.py`

**Checkpoint**: el shell nuevo envuelve todas las páginas (las no migradas siguen con `@layer legacy`).

---

## Phase 3: User Story 1 - La Decana ve el avance de un vistazo (P1) 🎯 MVP

**Goal**: banner huella + matriz factor × programa + aviso de atascados.

**Independent Test**: entrar como Decana y leer 6 / 205, el factor más lejano y los pendientes de más de 3 días sin scroll a 1440 × 900.

### Tests for User Story 1

- [X] T018 [P] [US1] Ampliar `gestion_documental/tests/test_metricas.py`: `huella_facultad()` con 12 celdas, totales y `pendientes_envejecidos`; `matriz_factor_programa()` por programa con número fijo de consultas (`assertNumQueries`); factor que supera la meta queda en nivel 5 con la cifra real
- [X] T019 [P] [US1] Crear `gestion_documental/tests/test_paneles_rol.py` (sección Decana): el panel contiene la huella con 12 columnas, "6 / 205" con los datos de prueba, la matriz enlazada a la búsqueda filtrada, y el aviso "más de 3 días sin revisar"; facultad vacía muestra "Aún no hay evidencias aprobadas"

### Implementation for User Story 1

- [X] T020 [US1] Implementar `MetricasService.huella_facultad()` y `matriz_factor_programa()` en `gestion_documental/apps/documentos/metricas.py` con `conteo_cacheado` e invalidación por `bump_stats()` (data-model: Huella, Matriz)
- [X] T021 [US1] Crear `gestion_documental/templates/componentes/banner_huella.html` (research R7): titular por rol, cifra `--sg-t-6`, 12 columnas con `style="--altura: N%"`, `aria-label` con el resumen, franja compacta en móvil
- [X] T022 [P] [US1] Crear `gestion_documental/templates/componentes/matriz.html`: `<table>` con encabezados, celdas `chip`, enlaces a `documentos:busqueda` con `factor` y `programa`, leyenda de gradación
- [X] T023 [US1] Reescribir la rama Decana de `gestion_documental/apps/documentos/templates/documentos/dashboard.html` y `DocumentoService.stats_decana` para usar la huella, la matriz y el aviso de pendientes envejecidos (corrige "Documentos vencidos" y la tarjeta "Crecimiento" vacía); añadir la plantilla a `PLANTILLAS_MIGRADAS`

**Checkpoint**: panel de la Decana completo.

---

## Phase 4: User Story 2 - La Coordinadora vacía su cola (P1)

**Goal**: banner con pendientes y antigüedad, cola ordenada, tiempos de revisión.

**Independent Test**: con pendientes de 1, 4 y 7 días, la cola sale de 7 a 1 con envejecidos marcados y se puede aprobar o rechazar desde ahí.

### Tests for User Story 2

- [X] T024 [P] [US2] Ampliar `gestion_documental/tests/test_metricas.py`: `cola_revision()` ordenada por antigüedad con `envejecido`; `tiempos_revision()` con 4 puntos semanales calculados desde SUBIO/NUEVA_VERSION → APROBO/RECHAZO (research R4)
- [X] T025 [P] [US2] Ampliar `gestion_documental/tests/test_paneles_rol.py` (sección Coordinadora): orden de la cola, marca de envejecido, botones de aprobar y rechazar, estado vacío con texto y siguiente paso

### Implementation for User Story 2

- [X] T026 [US2] Implementar `MetricasService.cola_revision()` y `tiempos_revision()` en `gestion_documental/apps/documentos/metricas.py`
- [X] T027 [US2] Crear `gestion_documental/templates/componentes/cola_revision.html` (lista por antigüedad, chips de factor, acciones, sparkline de 4 semanas con cifras) y `gestion_documental/templates/componentes/estado_vacio.html`
- [X] T028 [US2] Reescribir la rama Coordinadora de `gestion_documental/apps/documentos/templates/documentos/dashboard.html` y `DocumentoService.stats_coordinador` con banner (pendientes y antigüedad), cola y tiempos

---

## Phase 5: User Story 3 - El docente ve dónde aporta (P1)

**Goal**: huella con sus factores resaltados, sus evidencias con estado y "Subir evidencia" accesible en móvil.

**Independent Test**: docente con evidencias en F3 y F7 en un viewport de 390 px ve F3 y F7 resaltados y el botón de subir en la primera pantalla.

### Tests for User Story 3

- [X] T029 [P] [US3] Ampliar `gestion_documental/tests/test_metricas.py` con `huella_personal(usuario)` (12 meses, conteos por estado, solo documentos propios) y `gestion_documental/tests/test_paneles_rol.py` (sección docente): banner con 12 meses y sus totales, lista de evidencias con estado y motivo de rechazo, enlace a subir, ningún dato de la facultad (sin matriz, sin pulso, sin total de facultad)

### Implementation for User Story 3

- [X] T030 [US3] Añadir `MetricasService.huella_personal(usuario)` en `gestion_documental/apps/documentos/metricas.py` (data-model: HuellaPersonal; solo `autor=usuario`)
- [X] T031 [US3] Reescribir la rama docente de `gestion_documental/apps/documentos/templates/documentos/dashboard.html` y `DocumentoService.stats_docente` (banner con su huella personal y totales, "Subir evidencia" como acción reservada, lista de evidencias con `estado_documento`); `componentes/banner_huella.html` acepta el modo personal

---

## Phase 6: User Story 5 - Pulso de actividad y seguridad (P2)

**Goal**: 30 días de descargas, accesos denegados y solicitudes para directivas.

**Independent Test**: 3 accesos denegados ayer se ven marcados y enlazan a la auditoría filtrada; el docente no ve el pulso.

- [X] T032 [P] [US5] Ampliar `gestion_documental/tests/test_metricas.py` con `pulso_30_dias()` (agrupado por fecha de `America/Bogota`, total y variación frente al período anterior; solicitudes desde `SolicitudAcceso.fecha_solicitud`) y `gestion_documental/tests/test_paneles_rol.py` con la visibilidad por rol
- [X] T033 [US5] Implementar `MetricasService.pulso_30_dias()` en `gestion_documental/apps/documentos/metricas.py` con un solo `values('accion', fecha).annotate(Count)`
- [X] T034 [US5] Crear `gestion_documental/templates/componentes/pulso.html` (3 series SVG con `<title>`, cifras visibles, enlace a `auditoria:lista?accion=…`) e incluirlo en las ramas Decana y Coordinadora del panel

### Errores (US6, entrega 1)

- [X] T035 [P] [US6] Escribir `gestion_documental/tests/test_paginas_error.py`: 403 de un docente en `/auditoria/` renderiza la página del sistema con camino de vuelta; 404 con plantilla propia; 500 con `handler500` sin depender del contexto
- [X] T036 [US6] Crear `gestion_documental/templates/403.html`, `404.html` y `500.html`; hacer que `role_required` y `document_permission_required` en `gestion_documental/core/decorators/role_required.py` lancen `PermissionDenied`; que `usuarios/error_403.html` y `error_404.html` extiendan las nuevas; actualizar `tests/test_us1_aprobacion.py` si cambia el código de estado esperado

**Checkpoint (fin de la entrega 1)**: `manage.py test tests`, detector de impeccable sobre lo migrado, capturas de los 3 paneles a 1440 y 390 en `.impeccable/review/`, y **revisión del usuario**.

---

## Phase 7: User Story 4 - Pantallas de evidencias (P2) · Entrega 2

**Goal**: mismo lenguaje en búsqueda, mis documentos, detalle, subir, editar, versiones, papelera, aprobación y Factores CNA.

**Independent Test**: en 390 px ninguna de estas pantallas tiene desplazamiento horizontal y el chip de factor es idéntico en todas.

- [X] T037 [US4] Ampliar `gestion_documental/tests/test_reglas_diseno.py` con las 10 plantillas de esta fase en `PLANTILLAS_MIGRADAS` (deben fallar hasta migrarlas)
- [X] T038 [P] [US4] Migrar `gestion_documental/apps/documentos/templates/documentos/busqueda_avanzada.html`: filtros plegables que no ocupan la primera pantalla, resultados en `sg-tabla` con chips, resaltado con `<mark>` (conservar el JS seguro de C2), avatares con `iniciales`
- [X] T039 [P] [US4] Migrar `gestion_documental/apps/documentos/templates/documentos/mis_documentos.html` y `lista.html`
- [X] T040 [P] [US4] Migrar `gestion_documental/apps/documentos/templates/documentos/detalle.html`: ficha con estado y chip, factor con su gradación en la facultad, vista previa protegida (conservar A4), historial de versiones y de auditoría, "Eliminar" como acción secundaria de peligro
- [X] T041 [P] [US4] Migrar `gestion_documental/apps/documentos/templates/documentos/subir.html` y `editar.html` (formulario en una columna en móvil, zona de archivo accesible, nombre de archivo insertado con `textContent`)
- [X] T042 [P] [US4] Migrar `gestion_documental/apps/versiones/templates/versiones/lista.html` y `crear.html`
- [X] T043 [P] [US4] Migrar `gestion_documental/apps/documentos/templates/documentos/papelera.html`
- [X] T044 [P] [US4] Migrar `gestion_documental/apps/documentos/templates/documentos/aprobar_documentos.html` con la cola, los chips y la acción reservada
- [X] T045 [P] [US4] Migrar `gestion_documental/apps/documentos/templates/documentos/factores_cna.html` con `componentes/matriz.html`, leyenda y exportaciones con `aria-busy`

**Checkpoint (fin de la entrega 2)**: pruebas, detector, capturas y **revisión del usuario**.

---

## Phase 8: User Story 4 y 6 - Gestión, acceso y voz · Entrega 3

- [X] T046 [US4] Añadir a `PLANTILLAS_MIGRADAS` en `gestion_documental/tests/test_reglas_diseno.py` las plantillas de esta fase
- [X] T047 [P] [US4] Migrar `gestion_documental/apps/permisos/templates/permisos/gestionar_accesos.html`, `solicitudes.html` y `gestionar_legacy.html` (votos como marcas 0/2 con forma)
- [X] T048 [P] [US4] Migrar `gestion_documental/apps/auditoria/templates/auditoria/lista.html` (filtros, tabla a tarjetas, badges por acción con icono, texto mínimo de 12 px)
- [X] T049 [P] [US4] Migrar `gestion_documental/apps/usuarios/templates/usuarios/gestion.html` y `perfil.html` (avatares con `iniciales`, modal de edición accesible)
- [X] T050 [P] [US4] Migrar `gestion_documental/apps/notificaciones/templates/notificaciones/lista.html`
- [X] T051 [P] [US6] Migrar `gestion_documental/apps/usuarios/templates/usuarios/login.html`, `registro.html`, `recuperar_contrasena.html`, `confirmar_email.html`, `validar_token.html` y `cambiar_contrasena.html`: la huella como plano de fondo del login, sin splash que bloquee, tuteo único
- [X] T052 [US6] Revisar todos los textos de interfaz en plantillas y en `messages.*` de `gestion_documental/apps/*/views.py`: tuteo, sin emojis, verbos claros; mensajes de servicios en `gestion_documental/apps/usuarios/services.py` ("Lo identificamos, pero no tiene acceso" → tuteo)
- [X] T053 [P] [US4] Regenerar `UNFOLD["COLORS"]["primary"]` desde `#142a59` en `gestion_documental/config/settings.py` y aplicar Public Sans en `gestion_documental/static/css/admin_unfold.css` (research R10)

---

## Phase 9: Polish & Cross-Cutting Concerns

- [X] T054 Quitar `@import` de `legacy.css` en `gestion_documental/static/css/sigea/main.css`, borrar `gestion_documental/static/css/legacy.css` y `gestion_documental/static/js/main.js`, y verificar que ninguna plantilla los referencia
- [X] T055 Ejecutar `manage.py check`, `manage.py test tests --noinput` y `impeccable detect --json` sobre `templates`, `apps` y `static/css/sigea`; corregir hallazgos
- [X] T056 Capturar las pantallas de los 3 roles a 1440 × 900 y 390 × 844 en `.impeccable/review/` y recorrer `specs/002-rediseno-matriz-cna/quickstart.md` (teclado, movimiento reducido, zoom 200 %)
- [X] T057 Lanzar el revisor final de impeccable (`impeccable-finish-reviewer`) con el contrato de dirección y las capturas; aplicar su disposición
- [X] T058 Generar `DESIGN.md` y `.impeccable/design.json` con el documentador de impeccable desde lo construido
- [X] T060 Escribir la revisión de seguridad que exige la constitución (decoradores de permisos con `PermissionDenied`, retiro de CDN, visibilidad de métricas por rol) en `gestion_documental/informes/revision-seguridad-002-2026-11-07.md`
- [X] T061 Enmendar el principio VI en `.specify/memory/constitution.md` (1.0.0 → 1.1.0) para nombrar el sistema de diseño `static/css/sigea/` y la gradación CNA como escala única
- [X] T059 [P] Actualizar `gestion_documental/documentacion/manual_tecnico.md` (sistema de diseño, componentes, métricas) y el README

---

## Dependencies & Execution Order

- Setup → Foundational → US1, US2, US3, US5 y errores (todas tocan `dashboard.html`: hacerlas en orden T023 → T028 → T031 → T034).
- Entrega 2 (Phase 7) depende de la revisión del usuario de la entrega 1.
- Entrega 3 (Phase 8) depende de la revisión de la entrega 2.
- Polish depende de todo; T054 solo cuando ninguna plantilla dependa de `legacy.css`.

### Parallel Opportunities

- T002/T003, T007/T008/T015 en Foundational.
- Pruebas de cada historia (T018, T019, T024, T025, T029, T032, T035).
- Migraciones de la entrega 2 (T038–T045) y de la entrega 3 (T047–T051, T053): archivos distintos.

## Implementation Strategy

1. **MVP**: Setup + Foundational + US1 (panel de la Decana con la huella).
2. Completar la entrega 1 (US2, US3, US5, errores) → revisión del usuario.
3. Entrega 2 → revisión. Entrega 3 → revisión, cierre de impeccable y documentación.

## Notes

- Total: 61 tareas.
- Revisar si `gestion_documental/templates/home.html` se usa; si no, eliminarlo en T054.
- No hacer commit hasta que el usuario lo pida.
- Ningún contenido del contrato de dirección se copia a plantillas, comentarios ni atributos (regla de impeccable).
