# Revisión de seguridad: cierre de riesgos medios y bajos (spec 004)

- **Fecha:** 2026-11-07
- **Alcance:** `specs/004-riesgos-medios-bajos`. Cubre los hallazgos medios M2–M9 y M11 (aplicado) y los bajos que seguían abiertos de la auditoría del 2026-11-06. M1 y M10 ya se cerraron en las specs 001 y 002.
- **Motivo:** la constitución exige una revisión documentada al tocar autenticación, permisos o subida de archivos.

## Cambios por hallazgo

| Hallazgo | Cambio | Prueba (`tests/test_riesgos_004.py`) |
|---|---|---|
| **M2.** Bloqueo de la Decana a voluntad | Se elimina el bloqueo global por cuenta. Ahora se limitan los intentos fallidos: 10 por IP y 5 por cuenta e IP, cada uno en ventanas de 15 minutos. Pasado el límite no se evalúa la contraseña y la respuesta es la misma de siempre. | `LoginLimitesTest` |
| **M3.** Enumeración en la recuperación | La confirmación enmascara el correo tal como se escribió, sin consultar la base de datos. Todos los fallos del código muestran un mensaje único y no indican cuántos intentos quedan. La comparación del código se hace en tiempo constante. | `RecuperacionSinEnumeracionTest` |
| **M4.** Dos políticas de contraseña | `core.validators.ComplejidadValidator` (mayúscula y símbolo) se suma a `AUTH_PASSWORD_VALIDATORS`. Registro, recuperación e invitación usan `validate_password`. | `PoliticaUnicaTest` |
| **M5.** Metadatos de sensibles | Sin acceso, un sensible no se encuentra por descripción ni por autor, y la búsqueda muestra «Reservado» en lugar del autor. El título sigue visible para poder pedir acceso. | `SensiblesDiscretosTest` |
| **M6.** Aprobación sin controles | `_validar_revision` exige el estado «en revisión» y que quien revisa no sea el autor. Las vistas muestran el motivo. La cola y la bandeja no ofrecen aprobar lo propio. | `RevisionConControlesTest` |
| **M7.** La edición no reinicia la revisión | Si un docente edita una evidencia aprobada, vuelve a revisión. Un docente con programa asignado solo puede elegir su programa. | `EdicionYProgramaTest` |
| **M8.** Usuarios creados que no pueden entrar | La cuenta queda habilitada y se envía una invitación con un enlace de un solo uso (`default_token_generator`, vence en 3 días) para crear la contraseña. | `InvitacionTest` |
| **M9.** Registro sin validar | Se valida el correo con `validate_email`, se exige el nombre y se permiten como máximo 5 registros por hora por IP. | `RegistroTest` |
| **Bajo.** Redirección rota | `LOGIN_REDIRECT_URL = 'documentos:dashboard'`. | `test_redireccion_por_defecto_existe` |
| **Bajo.** Validación solo por extensión | Se revisa la firma real: `%PDF` para PDF, y para docx, xlsx y pptx un ZIP con `[Content_Types].xml` y su carpeta (`word/`, `xl/`, `ppt/`). Se aplica al subir, al crear versiones y al restaurarlas. | `test_firma_de_contenido` |
| **Bajo.** Sin CSP | CSP nativa de Django 6 mediante `core.middleware.CSPSinAdminMiddleware`. `script-src` solo admite `'self'`; los dos scripts en línea pasaron a `static/js/sigea.js`. El panel `/admin/` (Unfold) queda fuera porque usa scripts en línea propios. | `test_csp_en_la_app_y_no_en_admin`, `test_sin_scripts_en_linea_en_plantillas_propias` |

## Verificación

- `manage.py check`: sin problemas.
- `makemigrations --check`: sin cambios pendientes.
- `manage.py test tests`: 109 pruebas OK (19 nuevas).
- Navegador:
  - las respuestas de panel, búsqueda, Por revisar, Factores CNA, detalle y login traen la cabecera CSP;
  - la consola no muestra violaciones;
  - el resaltado de búsqueda funciona desde `sigea.js`.

## M11: usuario de base de datos con permisos mínimos (aplicado)

- La aplicación conecta como `sigea_app`, que no es superusuario y no puede crear bases, roles ni tablas. Solo puede leer, insertar, actualizar y borrar filas.
- `migrate` y `test` usan automáticamente el administrador (`DB_ADMIN_USER` y `DB_ADMIN_PASSWORD` en `.env`). `settings.py` lo decide según el comando.
- Los privilegios por defecto dan acceso a `sigea_app` a las tablas que creen las migraciones futuras.
- Se quitó el permiso `CREATE` del esquema `public` a `PUBLIC`.
- La clave de `sigea_app` es aleatoria (32 bytes) y solo está en `.env`. Hay un respaldo del `.env` anterior en `.env.bak-m11`, que git ignora; bórralo cuando ya no lo necesites.
- Verificación:
  - la app lee y escribe como `sigea_app`;
  - crear una tabla falla;
  - las 109 pruebas pasan con el administrador.

## Riesgos residuales

- **Aprobación al subir:** Decana y Coordinadora pueden dejar aprobada una evidencia propia en el momento de subirla. Es una regla de producto decidida en la spec 001. Si se quiere control de cuatro ojos completo, hay que quitar esa opción.
- **Límites en caché local:** los límites de intentos viven en la caché del proceso (LocMem). Con varios procesos o servidores, hay que pasar la caché a Redis; el bloque ya está documentado en `settings.py`.
- **CSP de estilos:** `style-src` admite `'unsafe-inline'` solo por los atributos `style="--variable: valor"` que dibujan los gráficos. Los scripts siguen restringidos a archivos propios.
- **Campos sin uso:** los campos `intentos_fallidos` y `bloqueado_hasta` del modelo ya no bloquean. Se conservan para no migrar; pueden retirarse más adelante.
