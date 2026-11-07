# Feature Specification: Corrección de hallazgos críticos y altos de la auditoría

**Feature Branch**: `001-fix-auditoria-criticos`

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: "Corregir los hallazgos críticos y altos de la auditoría de SIGEA. C1: la bandeja /documentos/aprobar/ responde 500. C2: XSS almacenado en la búsqueda avanzada. C3: la IP de auditoría se toma de X-Forwarded-For sin validar. A1: crear una versión nueva no actualiza el archivo vigente, no devuelve el documento a revisión ni se audita. A2: un usuario deshabilitado conserva su sesión. A3: la coordinadora (única de facultad) no recibe notificaciones de revisión. A4: la vista previa usa la URL directa de /media/ y envía documentos Office a Google Docs Viewer. A5: dependencias vulnerables (Django, Pillow, brotli). A6: la auditoría no registra inicios de sesión, solicitudes/votos/revocaciones, gestión de usuarios ni accesos denegados. A7: .env.bak no está ignorado por git."

## Clarifications

### Session 2026-11-07

- Q: Cuando la Decana o la Coordinadora suben una versión nueva de un documento aprobado, ¿vuelve a revisión? → A: No; se mantiene aprobado. Solo las versiones subidas por docentes devuelven el documento a "Pendiente". La versión se audita igual.
- Q: ¿Cómo se ve un documento Word, Excel o PowerPoint al pulsar "Visualizar archivo"? → A: Se muestra un aviso con botón de descarga protegida; solo los PDF se ven dentro de la página.
- Q: En un inicio de sesión fallido con un correo inexistente, ¿qué se guarda del correo escrito? → A: El correo enmascarado (por ejemplo "ye***@gmail.com") más la IP, nunca el texto completo.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Revisar y aprobar documentos sin errores (Priority: P1)

La Decana o la Coordinadora abre la bandeja "Aprobar documentos" para revisar lo pendiente,
aprobar o rechazar. Hoy la página falla por completo, así que nadie puede revisar evidencias
desde la interfaz.

**Why this priority**: es el flujo central del sistema; sin él no se valida ninguna evidencia.

**Independent Test**: entrar como Decana y como Coordinadora a la bandeja, filtrar por estado y
por urgentes, y aprobar o rechazar un documento.

**Acceptance Scenarios**:

1. **Given** una Decana o Coordinadora con sesión iniciada, **When** abre la bandeja de
   aprobación, **Then** la página carga y muestra los contadores de pendientes, aprobados hoy,
   rechazados hoy y urgentes.
2. **Given** existen documentos pendientes con más de 3 días, **When** filtra "urgentes",
   **Then** solo ve esos documentos y el contador de urgentes coincide con la lista.
3. **Given** un docente con sesión iniciada, **When** intenta abrir la bandeja, **Then** se le
   niega el acceso.

---

### User Story 2 - Búsqueda segura frente a contenido malicioso (Priority: P1)

Un usuario busca documentos y ve los términos resaltados en los resultados. Si un título o
descripción contiene código, este debe mostrarse como texto y nunca ejecutarse.

**Why this priority**: hoy un docente puede ejecutar código en la sesión de la Decana, que es
superusuaria.

**Independent Test**: crear un documento cuyo título contenga marcado HTML con un manejador de
eventos, buscarlo y comprobar que se ve como texto literal y que no se ejecuta nada.

**Acceptance Scenarios**:

1. **Given** un documento titulado con marcado HTML ejecutable, **When** la Decana busca un
   término que coincide, **Then** el título se muestra literalmente y no se ejecuta código.
2. **Given** una búsqueda normal, **When** se muestran los resultados, **Then** los términos
   buscados siguen resaltados sin partir las palabras.

---

### User Story 3 - Auditoría confiable y completa (Priority: P1)

La Decana consulta el registro de auditoría para demostrar quién hizo qué, cuándo y desde dónde.
Hoy la IP se puede falsificar, un valor inválido bloquea la acción y deja ver errores internos, y
muchos eventos relevantes no se registran.

**Why this priority**: la auditoría es evidencia para la acreditación (principio II de la
constitución).

**Independent Test**: realizar cada evento listado en los requisitos y comprobar que aparece en
el registro con usuario, acción, fecha e IP real; enviar cabeceras de IP falsas o inválidas y
comprobar que no alteran el registro ni bloquean la acción.

**Acceptance Scenarios**:

1. **Given** una petición con una cabecera de IP reenviada falsa y el sistema sin proxy de
   confianza configurado, **When** el usuario descarga un documento, **Then** se registra la IP
   real de la conexión, no la enviada en la cabecera.
2. **Given** una cabecera de IP reenviada con un valor que no es una IP, **When** el usuario
   realiza cualquier acción auditada, **Then** la acción se completa y el usuario no ve ningún
   mensaje técnico.
3. **Given** un intento de inicio de sesión exitoso o fallido, **When** la Decana revisa la
   auditoría, **Then** ve el evento con el correo intentado, el resultado y la IP.
4. **Given** una solicitud de acceso, un voto, una aprobación, un rechazo o una revocación,
   **When** ocurre, **Then** queda registrada con su actor y documento.
5. **Given** la Decana habilita, deshabilita, elimina o cambia el rol de un usuario, **When**
   revisa la auditoría, **Then** ve el evento con el usuario afectado y el cambio realizado.
6. **Given** un usuario intenta ver o descargar un documento sin permiso, **When** se le niega,
   **Then** el intento queda registrado.
7. **Given** registros de edición de metadatos o restauración, **When** se listan o exportan,
   **Then** muestran una etiqueta legible en español.

---

### User Story 4 - Versiones que reemplazan la evidencia vigente (Priority: P2)

El autor sube una versión corregida de un documento. Esa versión debe pasar a ser el archivo que
se descarga y se previsualiza, y si el documento ya estaba aprobado debe volver a revisión.

**Why this priority**: hoy la versión nueva no se entrega al descargar y un cambio de contenido
puede saltarse la revisión.

**Independent Test**: subir una versión nueva de un documento aprobado y comprobar el archivo
descargado, el estado, la notificación al revisor y el registro de auditoría.

**Acceptance Scenarios**:

1. **Given** un documento con versión 1, **When** el autor sube la versión 2, **Then** al
   descargar el documento se entrega el archivo de la versión 2.
2. **Given** un documento aprobado de un docente, **When** se sube una versión nueva, **Then** el
   documento vuelve a "Pendiente" y la Coordinadora recibe una notificación.
3. **Given** cualquier versión nueva, **When** se crea, **Then** queda registrada en auditoría.
4. **Given** dos subidas simultáneas de versión, **When** se guardan, **Then** reciben números de
   versión distintos.

---

### User Story 5 - Revisores siempre notificados (Priority: P2)

Un docente sube un documento o pide acceso a uno sensible. La Coordinadora, que es única para
toda la facultad, debe recibir el aviso aunque no tenga un programa asignado.

**Why this priority**: hoy los documentos de los docentes quedan pendientes sin que nadie se
entere.

**Independent Test**: con una Coordinadora sin programa, subir un documento como docente de
cualquier programa y comprobar que la Coordinadora recibe la notificación.

**Acceptance Scenarios**:

1. **Given** una Coordinadora activa sin programa, **When** un docente de cualquier programa sube
   un documento, **Then** la Coordinadora recibe la notificación de revisión.
2. **Given** una solicitud de acceso a un documento sensible, **When** se crea, **Then** reciben
   aviso el autor, la Coordinadora activa y la Decana, sin duplicados.
3. **Given** una versión restaurada de un documento pendiente, **When** se restaura, **Then** la
   Coordinadora recibe el aviso.

---

### User Story 6 - Sesiones cortadas al deshabilitar (Priority: P2)

La Decana deshabilita a un usuario. Ese usuario debe perder el acceso de inmediato, aunque tenga
una sesión abierta.

**Why this priority**: hoy un usuario deshabilitado sigue dentro mientras siga activo.

**Independent Test**: abrir sesión como docente, deshabilitarlo desde otra sesión y comprobar que
su siguiente petición lo saca del sistema.

**Acceptance Scenarios**:

1. **Given** un docente con sesión abierta, **When** la Decana lo deshabilita, **Then** en su
   siguiente petición se cierra su sesión y vuelve al inicio de sesión.
2. **Given** un usuario eliminado o inactivo con sesión abierta, **When** hace otra petición,
   **Then** tampoco conserva el acceso.

---

### User Story 7 - Vista previa protegida (Priority: P2)

Un usuario con permiso previsualiza un documento desde su detalle. La vista previa debe pasar por
el mismo control de permisos que la descarga y no enviar archivos a servicios externos.

**Why this priority**: hoy la vista previa expone el archivo sin control en desarrollo, no
funciona en producción y manda documentos Office a un tercero.

**Independent Test**: previsualizar un PDF con y sin permiso, y abrir la vista previa de un
documento Office comprobando que no se contacta ningún servicio externo.

**Acceptance Scenarios**:

1. **Given** un usuario con acceso a un PDF, **When** abre la vista previa, **Then** el PDF se
   muestra dentro de la página.
2. **Given** un usuario sin acceso, **When** solicita la vista previa directamente, **Then** se le
   niega y el intento se audita.
3. **Given** un documento Word, Excel o PowerPoint, **When** se pide la vista previa, **Then** se
   ofrece descargarlo, sin enviarlo a servicios externos.
4. **Given** el sistema en producción, **When** se abre la vista previa de un PDF permitido,
   **Then** funciona igual que en desarrollo.

---

### User Story 8 - Base técnica sin vulnerabilidades conocidas ni secretos expuestos (Priority: P3)

El responsable del proyecto necesita que las dependencias no tengan vulnerabilidades conocidas y
que ningún respaldo de configuración con secretos pueda terminar en el repositorio.

**Why this priority**: reduce el riesgo de explotación y de filtración, sin cambiar funciones
visibles.

**Independent Test**: ejecutar el análisis de vulnerabilidades de dependencias y comprobar que
devuelve cero hallazgos; comprobar que los respaldos de configuración aparecen como ignorados en
el control de versiones.

**Acceptance Scenarios**:

1. **Given** las dependencias actualizadas, **When** se ejecuta el análisis de vulnerabilidades,
   **Then** no reporta hallazgos.
2. **Given** el sistema con las dependencias nuevas, **When** se ejecutan la verificación y las
   pruebas del proyecto, **Then** todo pasa y la aplicación arranca.
3. **Given** un archivo de respaldo de configuración en la carpeta del proyecto, **When** se
   revisa el estado del repositorio, **Then** el archivo aparece ignorado, y la plantilla de
   ejemplo sigue versionada.

### Edge Cases

- Bandeja de aprobación sin documentos: muestra contadores en cero y el estado vacío, sin error.
- Títulos con caracteres especiales legítimos (comillas, `<`, `&`, tildes): se ven tal cual.
- Cabecera de IP reenviada con varias IPs o con espacios: solo se usa si hay un proxy de confianza
  configurado y el valor es una IP válida; en otro caso se usa la IP de la conexión.
- Usuario sin dirección IP detectable: el evento se registra igual, con IP vacía.
- Inicio de sesión con un correo inexistente: se audita el intento con el correo enmascarado y la
  IP, sin revelar al usuario si el correo existe.
- Versión nueva de un documento rechazado: vuelve a "Pendiente".
- No existe ninguna Coordinadora activa: los avisos llegan a la Decana para que nada quede sin
  revisor.
- El usuario se deshabilita a sí mismo o a la Decana: el sistema ya lo impide; se mantiene.
- Archivo físico de la vista previa faltante: mensaje amable, sin detalles técnicos.
- Un error inesperado al registrar la auditoría no debe mostrar detalles internos al usuario.

## Requirements *(mandatory)*

### Functional Requirements

**Bandeja de aprobación (C1)**

- **FR-001**: La bandeja de aprobación MUST cargar para Decana y Coordinadora con cualquier
  combinación de filtros de estado y urgencia.
- **FR-002**: La bandeja MUST mostrar el número de documentos urgentes (pendientes con más de 3
  días sin cambios).

**Búsqueda (C2)**

- **FR-003**: El resaltado de términos MUST tratar títulos y descripciones como texto plano; ningún
  contenido de usuario puede interpretarse como marcado o código.
- **FR-004**: El resaltado MUST conservar la palabra completa visualmente unida.

**Auditoría (C3, A6)**

- **FR-005**: La IP registrada MUST ser la de la conexión, salvo que se configure explícitamente un
  número de proxies de confianza; solo entonces se toma la IP correspondiente de la cabecera
  reenviada.
- **FR-006**: Un valor de IP inválido MUST descartarse sin impedir la acción del usuario.
- **FR-007**: El sistema MUST registrar: inicio de sesión exitoso, inicio de sesión fallido
  (incluidos bloqueos), cierre de sesión, solicitud de acceso, voto sobre acceso sensible,
  aprobación y rechazo de solicitudes, revocación de acceso, creación, habilitación,
  deshabilitación, eliminación y cambio de rol o programa de usuarios, acceso denegado a ver,
  descargar o previsualizar un documento, creación y restauración de versiones.
- **FR-008**: Todas las acciones registradas MUST tener una etiqueta legible en español en la
  lista y en las exportaciones.
- **FR-009**: Los eventos que no involucran un documento MUST poder registrarse indicando en el
  detalle el usuario afectado. Para inicios de sesión fallidos, el correo escrito MUST guardarse
  enmascarado (primeros 2 caracteres, `***` y el dominio), nunca completo.
- **FR-010**: Los mensajes mostrados al usuario tras un error MUST ser genéricos; el detalle
  técnico va solo al log del servidor.

**Versiones (A1)**

- **FR-011**: Al crear una versión, el archivo vigente del documento MUST pasar a ser el de esa
  versión.
- **FR-012**: Si el documento estaba aprobado o rechazado y quien sube la versión es docente, el
  documento MUST volver a "Pendiente" y notificar a la Coordinadora. Si la sube la Decana o la
  Coordinadora, el estado MUST mantenerse.
- **FR-013**: La numeración de versiones MUST ser única por documento aun con subidas
  simultáneas.

**Notificaciones (A3)**

- **FR-014**: Las notificaciones de revisión y de solicitudes sensibles MUST enviarse a la
  Coordinadora activa de la facultad, sin filtrar por programa.
- **FR-015**: Si no hay Coordinadora activa, las notificaciones de revisión MUST enviarse a la
  Decana.

**Sesiones (A2)**

- **FR-016**: Un usuario deshabilitado, inactivo o eliminado MUST perder el acceso en su siguiente
  petición, con su sesión cerrada.

**Vista previa (A4)**

- **FR-017**: La vista previa MUST servirse por una ruta que aplica la misma regla de acceso que la
  descarga y audita los rechazos.
- **FR-018**: Los PDF MUST mostrarse dentro de la página; Word, Excel y PowerPoint MUST mostrar un
  aviso con botón de descarga protegida, sin conversión en el servidor.
- **FR-019**: Los documentos MUST NOT enviarse a servicios externos para previsualizarse.
- **FR-020**: La interfaz MUST NOT exponer la ruta directa del archivo almacenado.

**Dependencias y repositorio (A5, A7)**

- **FR-021**: Las dependencias directas MUST quedar en versiones sin vulnerabilidades conocidas; las
  dependencias sin uso MUST eliminarse.
- **FR-022**: La verificación de versiones exigidas al arrancar MUST coincidir con las versiones
  nuevas.
- **FR-023**: Los archivos de configuración con secretos y sus respaldos MUST estar ignorados por
  el control de versiones, manteniendo versionada la plantilla de ejemplo.

### Key Entities

- **Registro de auditoría**: evento con actor, acción, documento opcional, detalle, fecha e IP.
  Se amplía el catálogo de acciones.
- **Documento**: evidencia con archivo vigente, estado de revisión y versiones.
- **Versión**: copia numerada del archivo de un documento, con autor y descripción del cambio.
- **Usuario**: persona con rol, programa, estado de habilitación y sesión.
- **Notificación**: aviso dirigido a un usuario sobre un documento.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: La bandeja de aprobación carga sin error en el 100 % de las combinaciones de rol
  directivo y filtro probadas.
- **SC-002**: 0 ejecuciones de código al mostrar títulos o descripciones con marcado malicioso en
  búsqueda.
- **SC-003**: El 100 % de los eventos listados en FR-007 aparecen en la auditoría tras realizarlos.
- **SC-004**: 0 registros de auditoría con una IP tomada de una cabecera no confiable, y 0 acciones
  bloqueadas por cabeceras inválidas.
- **SC-005**: Tras subir una versión, la descarga entrega el archivo nuevo en el 100 % de los
  casos.
- **SC-006**: La Coordinadora recibe el 100 % de las notificaciones de revisión de documentos de
  docentes, de cualquier programa.
- **SC-007**: Un usuario deshabilitado pierde el acceso en su primera petición posterior.
- **SC-008**: El análisis de dependencias reporta 0 vulnerabilidades conocidas.
- **SC-009**: Ningún mensaje visible al usuario contiene texto de errores internos o de base de
  datos en los flujos tocados.

## Assumptions

- La facultad tiene una sola Coordinadora y una sola Decana activas, como ya exige el sistema.
- En producción el sistema puede ir detrás de un proxy; el número de proxies de confianza se
  configura por entorno y por defecto es cero.
- Pillow no se usa en el código; si se confirma, se elimina en lugar de actualizarse.
- Las pruebas nuevas usan el ejecutor de pruebas estándar del proyecto, como exige el principio V.
- Los hallazgos medios y bajos de la auditoría (por ejemplo la exposición de metadatos de
  documentos sensibles) quedan fuera de esta especificación.
