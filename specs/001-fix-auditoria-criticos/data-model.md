# Data Model: Corrección de hallazgos críticos y altos

Sin tablas ni columnas nuevas. Solo cambian `choices` y reglas de comportamiento.

## RegistroAuditoria (apps/auditoria)

| Campo | Cambio |
|-------|--------|
| `accion` (CharField 20) | `choices` ampliados con 18 códigos (ver research R9). Migración `AlterField` sin pérdida de datos. |
| `ip_address` (GenericIPAddressField, null) | Sin cambio de esquema. Solo recibe IPs validadas o `NULL`. |
| `usuario` (FK, null) | `NULL` en login fallido con correo inexistente. |
| `detalle` (texto) | Usuario afectado o correo enmascarado (`ye***@dominio`) en eventos sin documento. |

**Reglas**: append-only, como hoy (sin add/delete en el admin). Ninguna acción del usuario debe
fallar por un valor de IP.

## Documento (apps/documentos)

| Campo | Regla nueva |
|-------|-------------|
| `archivo` | Siempre apunta al archivo de la última versión creada o restaurada. |
| `estado` | Transición nueva: `APROBADO`/`RECHAZADO` → `PENDIENTE` cuando un `DOCENTE_PLANTA` sube o restaura una versión. Sin cambio si la sube `DECANA`/`COORDINADOR`. |

## Version (apps/versiones)

| Campo | Regla |
|-------|-------|
| `numero_version` | Único por documento (`unique_together` existente) y calculado con la fila del documento bloqueada. |

## Usuario (apps/usuarios)

| Campo | Regla nueva |
|-------|-------------|
| `esta_habilitado`, `is_active` | Si alguno es `False` y el usuario no es superusuario, su siguiente petición cierra la sesión. |

## Notificación (apps/notificaciones)

Destinatarios de revisión = Coordinadora(s) activas y habilitadas. Si no hay ninguna, la Decana.
Para solicitudes sensibles: autor, Coordinadora y Decana, sin duplicados.
