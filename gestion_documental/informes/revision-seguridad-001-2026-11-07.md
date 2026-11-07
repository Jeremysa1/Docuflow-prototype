# Revisión de seguridad: correcciones críticas y altas (spec 001)

- **Fecha:** 2026-11-07
- **Alcance:** `specs/001-fix-auditoria-criticos` (hallazgos C1–C3 y A1–A7 de la auditoría del 2026-11-06)
- **Motivo:** la constitución (flujo, paso 3) exige revisión documentada al tocar autenticación, permisos, descargas o auditoría.

## Cambios por área

| Área | Cambio | Amenaza cubierta | Prueba |
|------|--------|------------------|--------|
| Búsqueda (C2) | El resaltado construye nodos `mark` y de texto; ya no se reinsertan títulos como HTML. | XSS almacenado: un docente ejecutaba código en la sesión de la Decana (superusuaria). | `tests/test_us2_busqueda.py` |
| Auditoría (C3) | IP desde `REMOTE_ADDR`; `X-Forwarded-For` solo con `TRUSTED_PROXY_COUNT>0`, tomando la entrada del proxy confiable; validación con `ipaddress`. | Falsificar la IP de la evidencia; denegación de servicio y fuga de SQL con cabeceras inválidas. | `tests/test_us3_auditoria.py::IpConfiableTest` |
| Auditoría (A6) | 18 acciones nuevas: sesión, accesos, usuarios, `ACCESO_DENEGADO`, `VISUALIZO`, `NUEVA_VERSION`. El correo de un login fallido inexistente se guarda enmascarado. | Acciones sin trazabilidad; contraseñas tecleadas en el campo de correo quedando en el log. | `tests/test_us3_auditoria.py` |
| Sesiones (A2) | `CuentaHabilitadaMiddleware` cierra la sesión de cuentas deshabilitadas o inactivas en la siguiente petición (los superusuarios quedan exentos). | Un usuario deshabilitado seguía operando con su sesión deslizante. | `tests/test_us6_sesiones.py` |
| Descargas (A4) | Se elimina el servido de `MEDIA_ROOT` en DEBUG; nueva ruta `vista-previa` con el mismo control que la descarga (solo PDF, `inline`, `nosniff`); sin Google Docs Viewer; el historial de versiones usa la descarga protegida. | Lectura de archivos sin permiso por URL directa; envío de documentos confidenciales a un tercero. | `tests/test_us7_vista_previa.py` |
| Versiones (A1) | La versión nueva es el archivo vigente; el original se conserva como v1; un docente devuelve el documento a revisión; numeración con bloqueo de fila; auditoría. | Cambiar el contenido de una evidencia aprobada sin revisión; pérdida del original. | `tests/test_us4_versiones.py` |
| Errores (FR-010) | Mensajes fijos y `logger.exception` en documentos, permisos, usuarios y versiones; `ReglaNegocioError` para textos de negocio. | Fuga de detalles internos (SQL, rutas). | `test_regla_de_negocio_se_muestra_y_errores_internos_no` |
| Dependencias (A5) | Django 6.1 → 6.1.3, Pillow 12.3.0 → 13.0.0 (lo exige reportlab), brotli 1.2.0 → 1.2.1. | 42 vulnerabilidades conocidas. | `pip_audit -r requirements.txt`: 0 hallazgos |
| Repositorio (A7) | `.env.*` ignorado, salvo `.env.example`. | Commit accidental de respaldos con secretos. | `git status --ignored` marca `.env.bak` como `!!` |
| Pruebas | `tests/test_accesos.py` → `tests/qa_accesos.py`. | `manage.py test` mutaba la base de desarrollo al importar el script. | `manage.py test tests`: 55 pruebas OK |

## Verificación

- `manage.py check`: sin problemas.
- `makemigrations --check`: sin cambios pendientes.
- `manage.py test tests`: 55 pruebas OK.
- `pip_audit`: 0 vulnerabilidades.
- Recorrido manual en navegador:
  - la bandeja de aprobación carga;
  - el PDF se ve en línea desde `/documentos/<id>/vista-previa/`;
  - el DOCX ofrece la descarga;
  - `/media/...` devuelve 404;
  - el resaltado usa `<mark>`;
  - la auditoría registra `VISUALIZO` con la IP real.

## Riesgos residuales (fuera de alcance, ver auditoría)

- **Mensajes de error internos:** siguen en las vistas de eliminar y restaurar documento, editar metadatos y exportar Excel/PDF.
- **Metadatos de documentos sensibles:** título, descripción y autor son visibles en la búsqueda y en el detalle bloqueado para docentes sin permiso (M5).
- **Aprobaciones:** `aprobar_documento` no valida el estado ni impide que la Coordinadora apruebe sus propios documentos (M6).
- **Bloqueo de cuentas:** el bloqueo es por cuenta (3 intentos) y permite bloquear a la Decana a voluntad (M2). La recuperación de contraseña revela qué correos existen (M3).
- **Validación de archivos:** solo se revisa la extensión, no el contenido (bajo).
- **Despliegue:** si se coloca un proxy delante, hay que configurar `TRUSTED_PROXY_COUNT`; con el valor `0` se registra la IP del proxy.
