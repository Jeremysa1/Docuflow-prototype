# Feature Specification: Peso visual, iconografía y portada de acceso

**Feature Branch**: `003-peso-visual-personalidad`

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: "Mejorar la portada del login: que diga sí o sí «Sistema Integrado de Gestión de Evidencias para la Acreditación», con el logo bien ubicado y el texto «Centraliza, organiza…» bien estructurado. Las pantallas rediseñadas se sienten sin peso visual: barras flacas y desabridas, tablas con bordes externos e internos muy delgados (también en evidencias y otras pantallas). Mala estructura general: por ejemplo, el campo Programa no está alineado con los campos de al lado, y pasa en muchos espacios. Faltan iconos de PDF, Word, Excel y PowerPoint para identificar los documentos, y faltan iconos en general. El logo de SIGEA del menú lateral está mal ubicado y no está alineado. El borde de los botones es raro, sobre todo cuando un botón se queda marcado. Le falta personalidad al sitio en general."

**Contexto de diseño**: continúa la dirección de la spec 002 (`.impeccable/surfaces/gestion-documental-templates-base-html.md`, `PRODUCT.md`, `DESIGN.md`). Se mantiene el azul #142a59 y el blanco; no se retrocede al diseño anterior.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Portada de acceso con identidad (Priority: P1)

Quien llega a SIGEA ve a la izquierda el logo de SIGEA bien ubicado, el nombre completo «Sistema Integrado de Gestión de Evidencias para la Acreditación» como titular y la frase «Centraliza, organiza y protege…» debajo, todo alineado a un mismo borde, con un elemento visual que represente la plataforma (los 12 factores CNA). A la derecha, la tarjeta de ingreso.

**Independent Test**: abrir `/login/` a 1440×900 y a 375×812; el titular, el logo y la frase se leen completos y alineados, sin solaparse con el fondo.

**Acceptance Scenarios**:

1. **Given** un visitante sin sesión, **When** abre el login en escritorio, **Then** ve el logo, el nombre completo del sistema y la frase de apoyo alineados a la izquierda, y una franja inferior con tres atributos con icono.
2. **Given** un visitante en móvil, **When** abre el login, **Then** ve el logo y el nombre completo encima de la tarjeta.

### User Story 2 - Pantallas con peso visual (Priority: P1)

Las tablas, hojas, barras y botones tienen presencia: bordes más firmes, cabeceras de tabla con fondo de marca, barras de avance gruesas con su porcentaje, fondo de página gris claro para que las hojas blancas resalten, y cabeceras de página con icono.

**Independent Test**: capturas de Panel, Mis evidencias, Buscar, Factores CNA, Por revisar y Usuarios muestran bordes de 1,5 px o más, cabecera de tabla azul y barras de al menos 12 px.

**Acceptance Scenarios**:

1. **Given** cualquier tabla del sistema, **When** se muestra, **Then** tiene marco exterior visible, cabecera con fondo de marca y filas separadas con contraste suficiente.
2. **Given** la lista «Avance por factor», **When** se muestra, **Then** cada barra mide al menos 12 px de alto y muestra su porcentaje.

### User Story 3 - Documentos reconocibles por su tipo (Priority: P1)

Cada evidencia muestra un icono de tipo de archivo (PDF, Word, Excel, PowerPoint) con su color convencional y su sigla, en todas las listas y en el detalle.

**Independent Test**: en Buscar, Mis evidencias, Por revisar, Papelera, el panel y el detalle, cada fila de documento tiene el icono de su tipo.

**Acceptance Scenarios**:

1. **Given** un documento .pdf, **When** aparece en una lista, **Then** se ve el icono de documento con la sigla PDF en rojo.
2. **Given** un archivo de extensión desconocida, **When** aparece, **Then** se ve un icono neutro de archivo.

### User Story 4 - Estructura y alineación (Priority: P2)

Los campos de un formulario en la misma fila se alinean por arriba con la misma altura, los selects dicen sus opciones vacías en español, el logo del menú lateral se alinea con los iconos de navegación y los botones conservan su forma al recibir foco.

**Independent Test**: en Subir evidencia, Factor CNA y Programa empiezan a la misma altura y miden lo mismo; ningún select dice «Select an option».

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La portada de acceso MUST mostrar el logo de SIGEA, el titular «Sistema Integrado de Gestión de Evidencias para la Acreditación» y la frase «Centraliza, organiza y protege las evidencias de cada factor CNA en un solo lugar.» alineados a un mismo borde.
- **FR-002**: La portada MUST incluir un motivo visual de los 12 factores CNA y tres atributos con icono.
- **FR-003**: Hojas, tablas, campos y botones MUST usar bordes de al menos 1,5 px con el tono de renglón reforzado; las tablas MUST tener cabecera con fondo de marca.
- **FR-004**: Las barras de avance MUST medir al menos 12 px de alto y mostrar el porcentaje.
- **FR-005**: El área de contenido MUST usar fondo gris claro (papel) para que las hojas blancas resalten.
- **FR-006**: Cada página de contenido MUST mostrar un icono junto a su título; las cabeceras de hoja MUST llevar icono.
- **FR-007**: Toda fila o ficha de documento MUST mostrar un icono de tipo de archivo (PDF, Word, Excel, PowerPoint o genérico) con su sigla.
- **FR-008**: Los campos en una misma fila MUST alinearse por arriba con igual altura de control.
- **FR-009**: Las opciones vacías de los selects MUST estar en español.
- **FR-010**: El logo del menú lateral MUST alinearse con la columna de iconos de navegación.
- **FR-011**: El foco visible de un botón MUST respetar la forma del botón (mismo radio) y el estado presionado MUST ser visible sin deformarlo.
- **FR-012**: Se MUST conservar Zero-Trust (el docente no ve datos de la facultad), el contraste AA, las áreas táctiles de 44 px y las reglas de diseño (sin estilos en línea salvo variables, sin hex fuera de tokens).

### Key Entities

- **Tipo de archivo**: derivado de la extensión del archivo de la evidencia (pdf, docx, xlsx, pptx, otro).

## Success Criteria *(mandatory)*

- **SC-001**: 100 % de las listas de documentos muestran icono de tipo.
- **SC-002**: 0 selects con texto en inglés.
- **SC-003**: Las capturas de revisión no muestran campos desalineados en filas de formulario.
- **SC-004**: Todas las pruebas existentes siguen en verde.

## Assumptions

- Los colores convencionales de tipo de archivo (rojo PDF, azul Word, verde Excel, naranja PowerPoint) se admiten como excepción a la paleta azul porque identifican formatos, no estados.
- No se agregan afirmaciones institucionales nuevas en la portada.
