# Feature Specification: Cierre de riesgos medios y bajos de la auditoría

**Feature Branch**: `004-riesgos-medios-bajos`

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: "Corrige todos los riesgos en general": los hallazgos medios M2–M9 y M11 y los bajos abiertos (redirección rota, validación de archivos solo por extensión, falta de CSP) de la auditoría del 2026-11-06.

## Decisiones tomadas (sin pregunta al usuario)

- **M5:** para quien no tiene acceso a un documento sensible, el título sigue visible (sin él no se puede pedir acceso), pero el autor y la descripción no se muestran, y las búsquedas por descripción o por autor no lo encuentran.
- **M6:** la revisión (aprobar o rechazar) exige que el documento esté en revisión y que quien decide no sea el autor. La opción de dejar aprobada una evidencia al subirla, que hoy tienen Decana y Coordinadora, se mantiene porque es una regla de producto ya decidida (spec 001).
- **M7:** si un docente edita los datos de una evidencia aprobada, vuelve a revisión. Las directivas conservan el estado (misma regla que las versiones en la spec 001). Un docente con programa asignado solo sube y edita evidencias de su programa.
- **M8:** al crear un usuario, la Decana deja la cuenta habilitada y SIGEA le envía una invitación con un enlace de un solo uso para fijar la contraseña.
- **M11:** la credencial de la base de datos es configuración del usuario; se documentan los pasos, no se cambian credenciales.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Acceso resistente a abusos (Priority: P1)

Nadie puede bloquear a otra persona escribiendo mal su contraseña, ni averiguar qué correos existen, ni crear cuentas en masa. Hay una sola política de contraseñas.

**Acceptance Scenarios**:

1. **Given** 3 contraseñas erradas para la Decana desde una IP, **When** la Decana entra desde otra IP con su contraseña correcta, **Then** entra.
2. **Given** 10 intentos fallidos desde una misma IP en 15 minutos, **When** esa IP intenta de nuevo, **Then** recibe el mismo mensaje genérico y no se evalúa la contraseña.
3. **Given** un correo inexistente en la recuperación, **When** se avanza por el flujo, **Then** las pantallas y mensajes son idénticos a los de un correo existente.
4. **Given** un registro con correo vacío o mal formado, **Then** se rechaza; **Given** más de 5 registros por hora desde una IP, **Then** se rechaza.
5. **Given** una contraseña nueva en recuperación, registro o invitación, **Then** se valida con la misma política (longitud, comunes, numérica, mayúscula y carácter especial).

### User Story 2 - Usuarios creados por la Decana pueden entrar (Priority: P1)

**Acceptance Scenarios**:

1. **Given** la Decana crea un usuario, **Then** queda habilitado y recibe un correo con un enlace para fijar su contraseña.
2. **Given** el enlace ya se usó o es inválido, **Then** se muestra que el enlace no es válido.

### User Story 3 - Revisión con controles (Priority: P1)

**Acceptance Scenarios**:

1. **Given** una evidencia ya aprobada o rechazada, **When** se intenta aprobar o rechazar, **Then** se rechaza con un mensaje claro.
2. **Given** una evidencia subida por la Coordinadora en revisión, **When** la Coordinadora intenta aprobarla, **Then** se rechaza; la Decana sí puede.
3. **Given** un docente edita una evidencia aprobada, **Then** vuelve a revisión.

### User Story 4 - Documentos sensibles discretos (Priority: P2)

**Acceptance Scenarios**:

1. **Given** un docente sin acceso a un documento sensible, **When** busca, **Then** no ve su autor y no lo encuentra por descripción ni por autor.

### User Story 5 - Defensa en profundidad (Priority: P3)

**Acceptance Scenarios**:

1. **Given** un archivo `.pdf` cuyo contenido no es PDF, **When** se sube, **Then** se rechaza.
2. **Given** cualquier página de la app, **Then** la respuesta trae una cabecera Content-Security-Policy que solo permite scripts propios.
3. **Given** un inicio de sesión que usa la redirección por defecto, **Then** llega al panel.

## Requirements *(mandatory)*

- **FR-001 (M2)**: El login MUST limitar los intentos fallidos por IP (10 en 15 min) y por par cuenta+IP (5 en 15 min), sin bloquear la cuenta para todas las IP.
- **FR-002 (M3)**: La recuperación MUST mostrar las mismas pantallas y mensajes exista o no el correo.
- **FR-003 (M4)**: Toda contraseña nueva MUST validarse con `validate_password` y un validador de complejidad común.
- **FR-004 (M5)**: Para usuarios sin acceso, los sensibles MUST ocultar autor y descripción y no coincidir por esos campos.
- **FR-005 (M6)**: Aprobar o rechazar MUST exigir estado en revisión y revisor distinto del autor.
- **FR-006 (M7)**: La edición de un docente sobre una evidencia aprobada MUST devolverla a revisión; un docente MUST subir solo a su programa.
- **FR-007 (M8)**: Crear un usuario MUST enviar una invitación con enlace de un solo uso para fijar la contraseña.
- **FR-008 (M9)**: El registro MUST validar el correo y limitar 5 registros por hora por IP.
- **FR-009**: `LOGIN_REDIRECT_URL` MUST apuntar a una ruta existente.
- **FR-010**: La subida MUST verificar la firma del contenido (PDF y Office OOXML).
- **FR-011**: Las respuestas MUST llevar CSP con `script-src 'self'`, sin scripts en línea en las plantillas propias.

## Success Criteria *(mandatory)*

- **SC-001**: Cada FR tiene al menos una prueba automatizada.
- **SC-002**: La suite completa sigue en verde.

## Assumptions

- La caché (LocMem) basta para los límites en un proceso; con varios procesos se cambia a Redis (ya documentado en settings).
- El panel de administración (Unfold) queda fuera de la CSP porque usa scripts en línea propios.
