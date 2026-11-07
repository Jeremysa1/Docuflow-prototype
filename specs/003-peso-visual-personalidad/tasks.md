# Tasks: Peso visual, iconografía y portada de acceso

**Input**: `specs/003-peso-visual-personalidad/` (spec.md, plan.md)

## Phase 1: Setup

- [X] T001 Recortar el emblema del logo a su contorno real en gestion_documental/static/img/sigea_emblema.png

## Phase 2: Foundational

- [X] T002 Reforzar tokens de borde, renglón, sombra y tipos de archivo en gestion_documental/static/css/sigea/tokens.css
- [X] T003 Foco que respeta el radio y estado presionado en gestion_documental/static/css/sigea/base.css
- [X] T004 Hojas, tablas, botones, campos y chips con más peso en gestion_documental/static/css/sigea/componentes.css

## Phase 3: User Story 2 - Peso visual (P1)

- [X] T005 [US2] Barras de 12 px con porcentaje y huella más firme en gestion_documental/static/css/sigea/graficos.css y gestion_documental/apps/documentos/templates/documentos/factores_cna.html
- [X] T006 [US2] Fondo papel del contenido en gestion_documental/static/css/sigea/shell.css
- [X] T007 [US2] Icono de título en las 15 cabeceras de página (apps/*/templates/**) con la clase sg-titulo-icono
- [X] T008 [US2] Iconos en cabeceras de hoja del panel y componentes en gestion_documental/templates/componentes/ y gestion_documental/apps/documentos/templates/documentos/dashboard.html

## Phase 4: User Story 3 - Tipo de archivo (P1)

- [X] T009 [US3] Template tag tipo_archivo en gestion_documental/core/templatetags/sigea.py y gestion_documental/templates/componentes/tipo_archivo.html
- [X] T010 [US3] Usar tipo_archivo en busqueda_avanzada, mis_documentos, aprobar_documentos, papelera, detalle, dashboard y cola_revision
- [X] T011 [US3] Prueba del tag tipo_archivo en gestion_documental/tests/test_tipo_archivo.py

## Phase 5: User Story 1 - Portada de acceso (P1)

- [X] T012 [US1] Reestructurar la portada en gestion_documental/apps/usuarios/templates/usuarios/_acceso.html
- [X] T013 [US1] Estilos de la portada en gestion_documental/static/css/sigea/paginas.css

## Phase 6: User Story 4 - Estructura y alineación (P2)

- [X] T014 [US4] Etiquetas vacías en español en gestion_documental/apps/documentos/forms.py
- [X] T015 [US4] Logo del riel alineado con la columna de iconos en gestion_documental/templates/base.html y shell.css

## Phase 7: Polish

- [X] T016 Pruebas completas y reglas de diseño (manage.py test tests)
- [X] T017 Capturas de revisión escritorio y móvil, y corrección de lo que muestren

## Dependencies

T001 → T015; T002 → T003–T008; T009 → T010 → T011; las fases 3–6 son independientes entre sí tras la fase 2.
