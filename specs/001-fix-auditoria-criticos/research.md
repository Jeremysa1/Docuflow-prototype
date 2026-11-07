# Research: Corrección de hallazgos críticos y altos

No quedaron `NEEDS CLARIFICATION` en el contexto técnico. Estas son las decisiones de diseño.

## R1. Contador de urgentes (C1)

- **Decision**: añadir `urgentes=Count('id', filter=Q(estado='PENDIENTE', fecha_modificacion__lt=hace_3_dias))`
  al `aggregate` existente y pasar `docs_urgentes_count` y `hay_urgentes` desde ese valor.
- **Rationale**: arregla el `NameError` y ahorra la consulta `.exists()` aparte.
- **Alternatives**: definir `docs_urgentes` como queryset (una consulta más).

## R2. Resaltado seguro (C2)

- **Decision**: recorrer los nodos de texto de `.sa-highlight-target`, partir con la regex y
  construir `<mark class="highlight-amber">` con `textContent`, sin `innerHTML`. Quitar el
  `padding` horizontal de `.highlight-amber` para no separar letras.
- **Rationale**: mismo patrón que `main.js` (R3-01) ya usa en la búsqueda rápida.
- **Alternatives**: resaltar en el servidor con `escape` + `mark_safe` (más complejo).

## R3. IP confiable (C3)

- **Decision**: nuevo setting `TRUSTED_PROXY_COUNT` (env, por defecto `0`).
  - Con 0 se usa `REMOTE_ADDR`.
  - Con N > 0 se toma la entrada N-ésima desde la derecha de `X-Forwarded-For`.
  - El resultado se valida con `ipaddress.ip_address`; si es inválido, `None`.
- **Rationale**: es el patrón estándar; un cliente solo controla las entradas de la izquierda.
- **Alternatives**: confiar en `X-Real-IP` (depende de Nginx), o librerías externas (prohibido
  añadir dependencias sin necesidad).

## R4. Versiones (A1)

- **Decision**: `VersionService.crear_version` dentro de `transaction.atomic()` con
  `select_for_update()` sobre el `Documento`. Pasos:
  1. calcular el número de versión;
  2. crear la `Version`;
  3. asignar `documento.archivo = version.archivo.name`;
  4. aplicar la regla de estado (docente + APROBADO/RECHAZADO → PENDIENTE);
  5. auditar `NUEVA_VERSION`;
  6. notificar a los revisores si pasa a PENDIENTE.

  `restaurar_version` reutiliza la misma regla y notificación.
- **Rationale**: el bloqueo de fila serializa la numeración (además del `unique_together`
  existente) y deja un solo punto de verdad.
- **Alternatives**: reintentar ante `IntegrityError` (más código, mismo efecto).

## R5. Cortar sesiones (A2)

- **Decision**: `core.middleware.CuentaHabilitadaMiddleware`, ubicado después de
  `AuthenticationMiddleware`. Si el usuario autenticado no es superusuario y
  `not is_active or not esta_habilitado`, hace `logout()`, muestra un mensaje genérico y
  redirige a `auth:login`. Los superusuarios quedan exentos.
- **Rationale**: cubre todas las rutas, incluido el admin, sin tocar el backend ni las sesiones
  guardadas. La exención evita bloquear a un superusuario creado con `createsuperuser`, que nace
  con `esta_habilitado=False`. La única superusuaria actual es la Decana, que no se puede
  deshabilitar.
- **Alternatives**: borrar las sesiones al deshabilitar (requiere recorrer la tabla de sesiones
  con `cached_db` y no cubre `is_active`).

## R6. Revisores de facultad (A3)

- **Decision**: `NotificacionService.notificar_revisores(documento, mensaje, incluir_decana=False)`.
  - Destinatarios: Coordinadora(s) activas y habilitadas.
  - Si no hay ninguna, o si `incluir_decana=True`, se añade la Decana.
  - Se quitan duplicados y se excluye al actor.

  Reemplaza los tres filtros por programa.
- **Rationale**: la regla "Coordinadora única de facultad" ya rige permisos y paneles.

## R7. Vista previa (A4)

- **Decision**: nueva ruta `documentos/<id>/vista-previa/`.
  - Aplica la misma comprobación que la descarga y audita `VISUALIZO` o `ACCESO_DENEGADO`.
  - Solo acepta PDF: `FileResponse(..., content_type='application/pdf')` con
    `Content-Disposition: inline` (o `X-Accel-Redirect`); otros formatos → 404.
  - El modal usa esa ruta en un `iframe`. Para Office muestra un aviso con enlace a
    `descargar_doc`, sin Google Viewer.
  - Se quita `static(MEDIA_URL)` de `config/urls.py`, y `versiones/lista.html` enlaza a
    `descargar_version`.
- **Rationale**: Zero-Trust en desarrollo y en producción, con un solo control de acceso.

## R8. Dependencias (A5)

- **Decision**:
  - `Django==6.1.3` (último parche; `pip-audit` exige ≥ 6.1.1);
  - `brotli==1.2.1`;
  - retirar `Pillow`: ningún modelo actual usa `ImageField`, que solo aparece en las migraciones
    históricas 0004–0005 de `usuarios`, eliminado en la 0006.

  Se actualizan `requirements.txt`, `requirements.lock` y `_PINS_CRITICOS`. Verificación:
  `manage.py check`, `migrate` en la BD de pruebas y la suite, sin Pillow instalado.
- **Fallback**: si las migraciones históricas exigen Pillow, fijar `Pillow==13.0.0`.

## R9. Catálogo de acciones (A6)

- **Decision**: ampliar `RegistroAuditoria.Accion` (máx. 20 caracteres) con estas acciones:

  | Código | Etiqueta |
  |--------|----------|
  | `EDITO_METADATOS` | Editó metadatos |
  | `ACTUALIZO` | Restauró documento |
  | `NUEVA_VERSION` | Subió nueva versión |
  | `VISUALIZO` | Visualizó documento |
  | `ACCESO_DENEGADO` | Acceso denegado |
  | `LOGIN` | Inició sesión |
  | `LOGIN_FALLIDO` | Intento de sesión fallido |
  | `LOGOUT` | Cerró sesión |
  | `SOLICITO_ACCESO` | Solicitó acceso |
  | `VOTO_ACCESO` | Votó acceso sensible |
  | `APROBO_ACCESO` | Aprobó acceso |
  | `RECHAZO_ACCESO` | Rechazó acceso |
  | `REVOCO_ACCESO` | Revocó acceso |
  | `CREO_USUARIO` | Creó usuario |
  | `HABILITO_USUARIO` | Habilitó usuario |
  | `DESHABILITO_USUARIO` | Deshabilitó usuario |
  | `ELIMINO_USUARIO` | Eliminó usuario |
  | `ACTUALIZO_USUARIO` | Cambió rol o programa |

  La migración solo cambia `choices`. La vista y su filtro iteran `Accion.choices`.

  Para eventos sin documento, `detalle` lleva el usuario afectado. El login fallido usa
  `enmascarar_email` (helper extraído de `confirmar_email_recuperacion`). Los servicios de
  permisos y usuarios reciben `request` opcional para la IP.
- **Rationale**: un catálogo cerrado permite filtrar y exportar con etiquetas legibles.

## R10. Suite de pruebas segura (requisito del principio V)

- **Decision**: renombrar `tests/test_accesos.py` → `tests/qa_accesos.py` y actualizar su
  docstring.
- **Rationale**: el script ejecuta consultas y cambios contra la BD real al importarse. Con su
  nombre actual, `manage.py test` lo descubre y altera los datos de desarrollo antes de crear la
  BD de pruebas. `test_templates.py` es de solo lectura y se deja igual.
- **Alternatives**: correr siempre con etiquetas explícitas (frágil).

## R11. Mensajes de error (FR-010)

- **Decision**: en las vistas tocadas, reemplazar `f'...: {e}'` y `str(e)` por mensajes fijos
  y `logger.exception`. Las excepciones de negocio que ya traen texto para el usuario
  (`Exception("Ya tienes una solicitud…")` en permisos) se conservan, pero se capturan como una
  clase propia `ReglaNegocioError` para no exponer errores inesperados.
