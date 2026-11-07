# Feature Specification: Rediseño visual "Matriz de autoevaluación"

**Feature Branch**: `002-rediseno-matriz-cna`

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: "Rediseño visual completo de SIGEA con la dirección «Matriz de autoevaluación». Mantener azul #142a59 y blanco; reemplazar la estética genérica; sistema de diseño con tokens; shell nuevo; panel por rol con métricas y gráficos (matriz factor × programa, cola de revisión con tiempos, mis evidencias, pulso de actividad y seguridad); rediseño de todas las pantallas; iconos, textos, estados, páginas de error, móvil, accesibilidad, admin con la misma paleta; corregir bugs visuales. Además: un banner con impacto que represente la plataforma, y recordar que el sistema tiene 3 roles."

**Contexto de diseño**: la dirección visual elegida está en
`.impeccable/surfaces/gestion-documental-templates-base-html.md` (contrato) y `PRODUCT.md`.

## Clarifications

### Session 2026-11-07

- Q: ¿Con qué umbrales se colorea la gradación? → A: Equivalente a la escala CNA en porcentaje de aprobadas frente a la meta: 0 % sin evidencia; 1–59 % no se cumple; 60–69 % insatisfactorio; 70–79 % aceptable; 80–89 % alto grado; 90 % o más pleno.
- Q: ¿Qué muestra el banner del docente? → A: Solo su propia actividad, nunca datos de la facultad (el docente no tiene acceso a Factores CNA ni a la matriz): 12 columnas con sus últimos 12 meses, cada una con lo que subió ese mes dividido por estado.
- Q: ¿Cómo se entrega el rediseño? → A: Por fases: (1) sistema de diseño, shell y los 3 paneles con el banner; (2) pantallas de evidencias; (3) gestión, auditoría y acceso; revisión del usuario entre fases.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - La Decana ve el avance de la acreditación de un vistazo (Priority: P1)

Al entrar, la Decana ve un banner con la "huella de acreditación" de la facultad (12 factores en
la escala de gradación), el avance global como cantidad frente a meta y lo que está atascado.
Debajo, la matriz factor × programa le dice dónde falta evidencia.

**Why this priority**: es la pregunta central del producto ("¿cuánto falta y qué está atascado?")
y hoy la primera pantalla está ocupada por decoración.

**Independent Test**: entrar como Decana y responder, sin hacer scroll en escritorio, cuántas
evidencias aprobadas hay frente a la meta, qué factor está más lejos y cuántos documentos llevan
más de 3 días sin revisar.

**Acceptance Scenarios**:

1. **Given** la facultad con 6 de 205 evidencias aprobadas, **When** la Decana abre su panel,
   **Then** el banner muestra "6 / 205" y una huella con los 12 factores coloreados según su
   gradación.
2. **Given** un documento pendiente desde hace 4 días, **When** abre el panel, **Then** ve el
   aviso "1 evidencia lleva más de 3 días sin revisar" con acceso directo a revisarla.
3. **Given** la matriz factor × programa, **When** pasa sobre una celda o la toca, **Then** ve
   "n / meta", la gradación en palabras y puede ir a esas evidencias.

---

### User Story 2 - La Coordinadora vacía su cola de revisión (Priority: P1)

La Coordinadora ve en su banner cuántas evidencias esperan revisión y cuánto lleva esperando la
más antigua; su panel lista la cola de la más antigua a la más nueva, con tiempos de revisión.

**Why this priority**: sin revisión no hay evidencia aprobada; es el cuello de botella.

**Independent Test**: entrar como Coordinadora con 3 pendientes de distintas fechas y comprobar
el orden, la antigüedad visible y que puede aprobar o rechazar desde ahí.

**Acceptance Scenarios**:

1. **Given** 3 pendientes de 1, 4 y 7 días, **When** abre su panel, **Then** aparecen ordenados
   de 7 a 1 y los de más de 3 días se marcan como envejecidos.
2. **Given** el último mes, **When** mira el indicador de tiempos, **Then** ve el tiempo medio de
   revisión y su tendencia de las últimas semanas.
3. **Given** la cola vacía, **When** abre su panel, **Then** ve un estado vacío que lo dice con
   claridad y sugiere el siguiente paso.

---

### User Story 3 - El docente sigue el estado de sus evidencias (Priority: P1)

El docente ve en su banner su propia actividad: 12 columnas con sus últimos 12 meses (lo que subió
cada mes, dividido en aprobadas, en revisión y rechazadas), sus totales y su acción principal:
subir evidencia. No ve datos de la facultad ni de otros docentes.

**Why this priority**: es el rol que alimenta el sistema y entra mucho desde el celular.

**Independent Test**: entrar como docente en un celular, ver el estado de sus evidencias y subir una
sin hacer zoom; comprobar que no aparece ningún dato de la facultad.

**Acceptance Scenarios**:

1. **Given** un docente con 4 evidencias aprobadas y 1 en revisión subidas este año, **When** abre
   su panel, **Then** el banner muestra esas cifras y las columnas de los meses en que subió, por
   estado, sin ningún dato de la facultad.
2. **Given** una evidencia rechazada, **When** la ve en su lista, **Then** el estado se
   distingue por forma y color y muestra el motivo.
3. **Given** un celular de 390 px, **When** abre el panel, **Then** el botón de subir evidencia
   está visible en la primera pantalla con un área táctil de al menos 44 px.

---

### User Story 4 - Un sistema visual coherente en todas las pantallas (Priority: P2)

Cualquier usuario reconoce el mismo lenguaje en búsqueda, detalle, aprobación, accesos,
auditoría, usuarios, notificaciones, subir, versiones, papelera, perfil y login: mismos colores
con el mismo significado, misma tipografía, mismos iconos y componentes.

**Why this priority**: la auditoría encontró 132 colores y 52 tamaños de letra distintos; sin un
sistema único el rediseño se vuelve a degradar.

**Independent Test**: revisar todas las pantallas y comprobar que solo usan los colores,
tamaños e iconos definidos en el sistema de diseño.

**Acceptance Scenarios**:

1. **Given** cualquier pantalla, **When** se muestra un estado de documento, **Then** usa el mismo
   color y la misma forma que en el resto del sistema.
2. **Given** la búsqueda en móvil, **When** hay resultados, **Then** se muestran como tarjetas
   legibles, sin desplazamiento horizontal.
3. **Given** el factor de una evidencia, **When** aparece en cualquier pantalla, **Then** se
   muestra con el mismo chip de gradación que en la matriz.

---

### User Story 5 - Pulso de actividad y seguridad (Priority: P2)

La Decana y la Coordinadora ven un pulso de los últimos 30 días: descargas, accesos denegados y
solicitudes de acceso, con la tendencia marcada cuando algo cambia.

**Why this priority**: es la tercera métrica que el usuario confirmó que usa para decidir.

**Independent Test**: generar accesos denegados en los últimos días y comprobar que el pulso los
muestra y lleva a la auditoría filtrada.

**Acceptance Scenarios**:

1. **Given** 3 accesos denegados ayer, **When** la Decana abre su panel, **Then** el pulso marca
   ese día y enlaza a la auditoría filtrada por "Acceso denegado".
2. **Given** un docente, **When** abre su panel, **Then** no ve el pulso de seguridad.

---

### User Story 6 - Textos, estados y errores con una sola voz (Priority: P3)

Todos los textos usan el tuteo, son claros y en español; vacío, carga, error y éxito tienen
estados diseñados; 403, 404 y 500 tienen páginas propias.

**Why this priority**: la auditoría encontró mezcla de tú y usted, emojis y errores en texto
plano.

**Independent Test**: provocar un 403, un 404, un error de formulario y una lista vacía y
comprobar diseño, tono y una salida clara en cada caso.

**Acceptance Scenarios**:

1. **Given** un docente sin permiso, **When** abre una ruta de directivas, **Then** ve la página
   403 del sistema con un camino de vuelta, no un texto plano.
2. **Given** una acción que tarda (exportar, subir), **When** está en curso, **Then** el botón
   muestra que está trabajando y no se puede pulsar dos veces.

### Edge Cases

- Facultad sin evidencias: la huella se dibuja como 12 columnas vacías con el texto "Aún no hay
  evidencias aprobadas", no como un banner roto.
- Factor que supera su meta: la celda queda en "pleno" y muestra la cifra real (por ejemplo
  23 / 20).
- Usuario sin programa asignado: su panel no falla; la matriz muestra la fila de facultad.
- Muchos programas: la matriz permite desplazamiento horizontal propio en escritorio y pasa a
  lista por factor en móvil.
- Nombres o títulos muy largos: se recortan con puntos suspensivos y muestran el texto completo
  al enfocarlos.
- Usuario con movimiento reducido: no hay animaciones de entrada.
- Pantallas de 320 px: nada se corta ni obliga a desplazamiento horizontal de la página.

## Requirements *(mandatory)*

### Functional Requirements

**Sistema de diseño**

- **FR-001**: El sistema MUST definir un único conjunto de tokens: azul de marca #142a59, blanco,
  neutros, un neutro para "sin evidencia" y una escala de 5 azules para la gradación CNA
  (no se cumple, insatisfactorio, aceptable, alto grado, pleno), un color de acción reservado, y colores de estado (aprobado,
  pendiente, rechazado, envejecido, sensible).
- **FR-002**: Ninguna pantalla MUST usar colores, tamaños de letra o espaciados fuera de los
  tokens; los estilos en línea quedan prohibidos salvo valores calculados de datos (anchos de
  barras, alturas de la huella).
- **FR-003**: La tipografía MUST tener una escala de 5 pasos con base de 16 px y cifras
  tabulares; ningún texto funcional por debajo de 12 px.
- **FR-004**: Cada estado de documento MUST distinguirse por forma además de por color (sólido,
  borde punteado, tachado, marca de reloj, candado).
- **FR-005**: El color de acción MUST reservarse para la acción principal pendiente del usuario en
  cada pantalla.
- **FR-006**: La iconografía MUST usar una sola familia de iconos de línea, con el mismo grosor y
  sin fondos de color ni emojis.

**Banner "huella de acreditación" y paneles por rol**

- **FR-007**: Cada panel MUST abrir con un banner azul a lo ancho de 12 columnas con datos reales.
  Para Decana y Coordinadora es la huella de acreditación (una columna por factor, altura y tono
  según la gradación de la facultad). Para el docente es su huella personal (sus últimos 12 meses,
  cada columna dividida por estado de sus evidencias), sin datos de la facultad.
- **FR-008**: El banner MUST mostrar un titular y una acción distintos por rol: Decana (avance
  global "n / meta" y atascados), Coordinadora (pendientes y antigüedad de la más antigua),
  docente (sus totales por estado y "Subir evidencia").
- **FR-009**: El panel de la Decana MUST mostrar la matriz factor × programa con "n / meta" y la
  gradación en cada celda, navegable hasta las evidencias.
- **FR-010**: El panel de la Coordinadora MUST listar la cola de revisión de la más antigua a la
  más nueva, marcar las de más de 3 días y mostrar el tiempo medio de revisión de los últimos 30
  días con su tendencia semanal.
- **FR-011**: El panel del docente MUST listar sus evidencias con estado, factor y motivo de
  rechazo cuando aplique.
- **FR-012**: Decana y Coordinadora MUST ver el pulso de 30 días (descargas, accesos denegados,
  solicitudes) con enlace a la auditoría filtrada; el docente no lo ve.
- **FR-013**: La página de Factores CNA MUST mostrar la matriz completa con leyenda de gradación y
  exportaciones.

**Pantallas**

- **FR-014**: Todas las pantallas autenticadas y las de acceso (login, registro, recuperación)
  MUST usar el nuevo shell y los componentes del sistema.
- **FR-015**: El shell MUST tener un riel lateral azul en escritorio y una navegación accesible con
  el pulgar en móvil, con los destinos según el rol.
- **FR-016**: Las tablas MUST convertirse en tarjetas por debajo de 768 px, sin desplazamiento
  horizontal de la página.
- **FR-017**: Toda lista MUST tener estados de vacío, carga y error diseñados; toda acción, una
  confirmación de éxito visible.
- **FR-018**: El sistema MUST tener páginas propias para 403, 404 y 500 con un camino de vuelta.
- **FR-019**: Todos los textos de la interfaz MUST usar el tuteo, sin emojis, con verbos claros en
  botones.
- **FR-020**: El admin MUST usar la misma paleta y la misma marca.
- **FR-021**: Se MUST corregir: la tarjeta "Crecimiento" vacía con valor 0, el plural "1 docs", el
  aviso de "vencidos" (son pendientes de más de 3 días) y los avatares vacíos (iniciales).

**Accesibilidad**

- **FR-022**: Texto y controles MUST cumplir contraste WCAG 2.1 AA, foco visible en todo elemento
  interactivo y áreas táctiles de al menos 44 × 44 px.
- **FR-023**: Las animaciones MUST respetar la preferencia de movimiento reducido y nunca ocultar
  contenido.
- **FR-024**: Los gráficos MUST tener una alternativa textual (cifras visibles o descripción
  accesible).

### Key Entities

- **Gradación de cumplimiento**: nivel de un factor (o de una celda factor × programa) según
  evidencias aprobadas frente a la meta: sin evidencia (0 %), no se cumple (1–59 %), insatisfactorio (60–69 %),
  aceptable (70–79 %), alto grado (80–89 %), pleno (90 % o más).
- **Huella de acreditación**: representación de los 12 factores de la facultad según su
  gradación; base del banner.
- **Tiempo de revisión**: tiempo entre que una evidencia queda pendiente y su aprobación o
  rechazo.
- **Pulso de actividad**: conteo diario de 30 días de descargas, accesos denegados y solicitudes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: La Decana responde "cuánto falta" y "qué está atascado" en menos de 10 segundos
  desde que abre su panel, sin hacer scroll en escritorio.
- **SC-002**: El sistema usa como máximo 24 colores definidos y 6 tamaños de letra, frente a 132 y
  52 hoy; 0 estilos en línea salvo valores de datos.
- **SC-003**: 0 textos funcionales por debajo de 12 px y 100 % de los pares texto/fondo cumplen
  WCAG AA.
- **SC-004**: En un celular de 390 px, 0 pantallas con desplazamiento horizontal y todas las
  acciones principales alcanzables con el pulgar.
- **SC-005**: Las 27 plantillas de las apps y las páginas de error del proyecto usan el mismo shell y componentes.
- **SC-006**: Un docente sube una evidencia desde el celular en menos de 1 minuto.
- **SC-007**: En una revisión con los 3 roles, cada uno identifica su siguiente acción en la
  primera pantalla.

## Assumptions

- La entrega es por fases con revisión del usuario entre cada una (ver Clarifications).
- No hay metas por programa: la matriz usa la meta de facultad del factor en cada celda hasta que
  existan.
- El tiempo de revisión se deriva de la auditoría (subida → aprobación o rechazo); no hace falta
  un modelo nuevo.
- Se mantienen la funcionalidad, las rutas y los permisos actuales; es un rediseño de
  presentación más las métricas nuevas.
- El logo actual se conserva; la marca es solo SIGEA, sin identidad de la universidad.
- Las dependencias de terceros para gráficos no son necesarias: los gráficos se dibujan con el
  propio sistema.
