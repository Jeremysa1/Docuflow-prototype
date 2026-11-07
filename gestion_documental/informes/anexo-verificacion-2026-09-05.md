# Anexo de verificación post-hardening — 2026-09-05

## 1. Incidente: `documentos/services.py` sobrescrito por el plan v3
El plan v3 reescribió `apps/documentos/services.py` y se perdieron 3 fixes ya aplicados:
H-02 (`eliminar`/`restaurar` sin control) y regla facultad en `aprobar`/`rechazar`/`puede_gestionar_accesos`.
**Re-aplicados y verificados** (`manage.py check` limpio). Lección: un solo responsable por archivo por turno;
revisar `git diff` antes de dar por cerrado un plan multi-agente.

## 2. Bug de descarga `detalle null` (reportado en prueba funcional)
Causa: v3 agregó `detalle=None` a `registrar_descarga`; la columna es `NOT NULL`.
Fix: default `''` + `detalle or ''` en `documentos/services.py:291`,
`core/services/audit_service.py` y `apps/auditoria/services.py`. El permiso sí funcionaba;
fallaba solo el INSERT del log. Usuario confirma descarga OK tras el fix.

## 3. Regla facultad H-08 (aclaración del dueño)
1 Decana + 1 Coordinadora para toda la Facultad de Ingeniería (civil, software, mecánica).
COORDINADOR = acceso total, igual que DECANA. Aplicado en:
`aprobar`/`rechazar`, `eliminar`/`restaurar`, `versiones` crear/restaurar/listar,
`gestionar_accesos`, `votar_acceso_sensible`, `listar_solicitudes`, `buscar_ajax`,
`aprobar_documentos_view`, `stats_coordinador`. Comentarios en código indican
dónde re-amarrar por programa si a futuro hay un coordinador por programa.

## 4. Tests `tests/test_accesos.py` — 6/9 OK
Flujos tocados por el hardening (solicitud, aprobación, detalle, revocación,
doble-voto) pasan. Los 3 FALLO (rechazo, sensible 2/3, sensible rechazo) son
por datos: no existe documento sensible de `jeremy` en la BD local
(`doc_sensible: NINGUNO`), no por regresión. Crear un doc sensible de prueba
y re-correr para 9/9.

## 5. Guards de prod
`DEBUG=False manage.py check` → limpio (SECRET_KEY presente, SMTP real por defecto).
El `RuntimeError` de console-backend solo salta si se fuerza
`EMAIL_BACKEND=console` en prod (verificado por diseño).

## 6. `requirements.lock` — aprobado
12 paquetes, solo transitivos legítimos, sin paquetes Windows ni dev-tools.
Congelar con `pip install -r requirements.lock` en prod.

## Pendientes del dueño (no automatizables por el agente)
- Rotar `DB_PASSWORD` en Postgres + `.env` (hacerlo el dueño).
- Bloque Nginx `/internal_media/` + `USE_X_ACCEL_REDIRECT=1` en prod.
- SMTP real (`EMAIL_HOST/PORT/USER/PASSWORD`) en prod.
- Re-correr `test_accesos` con doc sensible para 9/9.

## 7. Segunda verificación (Antigravity + re-test con sensibles) — 2026-09-05
- **DB rotada: SÍ.** `DB_PASSWORD` difiere de `.env.bak` y la app conecta a
  PostgreSQL con la clave actual. `.env` sigue ignorado por git.
- **SMTP real: código listo**, valores por entorno (`EMAIL_HOST/PORT/USER/PASSWORD`,
  `DEFAULT_FROM_EMAIL` en `settings.py`); en local dev sigue console, en prod SMTP.
- **Nginx/X-Accel: código listo** (`USE_X_ACCEL_REDIRECT` en settings,
  bifurcación en ambas vistas de descarga, `static()` solo con `DEBUG`).
  El bloque `location /internal_media/` es infra de prod y no se verifica desde el repo.
- **Tests: 9/9 OK** tras subir Sensi2/Sensi3 (rechazo, sensible 2 votos,
  rechazo inmediato, revocación y anti doble-voto pasan).
- **Re-verificación global:** H-01 (decoradores PDF), H-03 (sin `|safe`),
  H-02 (check eliminar en servicio), H-06 (`url_has_allowed_host`),
  H-09 (guard `SECRET_KEY`) y arranque `DEBUG=False` → todo limpio.
- Estado: en espera de órdenes para la siguiente fase.

## 8. Corrección run 2 (R2-01..R2-05) — 2026-09-05
- **R2-01:** `recovery_email_validado` ligado al email + limpieza de flags en
  `recuperar/`/`confirmar`/`reenviar/` + igualdad estricta en `nueva_contrasena_view`.
  Test `tests/test_recovery_guards.py` (2 tests OK: ataque bloqueado, flujo legítimo OK).
- **R2-03:** `actualizar_usuario` con actor, anti auto-rol, unicidad DECANA/COORDINADORA,
  sync `is_staff/is_superuser`; unicidad también en `crear_usuario`.
- **R2-04:** `restaurar_version` valida extensión+tamaño (`validar_archivo_subido`).
- **R2-02:** `votante==solicitante` rechazado + `transaction.atomic()` con
  `select_for_update()` (método `_aplicar_voto`).
- **R2-05:** helper `redirect_back_seguro` (allowlist) en las 3 ramas `Referer`
  (además corrige fallback inválido `'documentos:busqueda'` literal en versiones).
- Verificación: `manage.py check` limpio, `test_accesos` 9/9, recovery guards 2/2.

## 9. Hardening restante — 2026-09-05
- **H1** Excel: `sanear_celda_excel` (prefija `'` ante `=,+,-,@`) en export auditoría
  (email/nombre/programa/título); el CNA solo usa datos estáticos.
- **H2** Descargas: `Content-Disposition` con nombre saneado + `filename*` RFC5987,
  `FileResponse(..., filename=...)` explícito y rechazo de `rel_path` con `..`.
- **H3** Admin: tokens de recuperación excluidos de `UsuarioAdmin`;
  `RegistroAuditoria` append-only (readonly, sin alta ni borrado).
- **H4** `marcar_leida`: POST marca siempre; GET solo marca si `next` es exactamente
  el detalle del documento de esa notificación (el link "Ver documento" sigue igual).
- **H5** Ruta muerta `cambiar_estado` eliminada de `apps/usuarios/urls.py` (legacy sin uso).
- **H6** Fechas/`categoria_id` inválidas se ignoran en vez de 500
  (`parse_fecha_segura`, `isdigit`).
- Verificación: `check` limpio, recovery 2/2, accesos 9/9.

## 10. Corrección run 3 (R3-01..R3-06) — 2026-09-05
- **R3-01:** buscador navbar con nodos `textContent` (cero `innerHTML` con datos);
  regex escapado (además corrige crash con `(` en la búsqueda).
- **R3-02:** `|escapejs` en ambos argumentos del `onclick` de detalle.
- **R3-03:** `apps/usuarios/backends.py` (`BloqueoAdminBackend`, mismo 3/15min)
  + `AUTHENTICATION_BACKENDS` en settings; frontal sin doble conteo.
- **R3-04:** `@require_POST` en `marcar_todas_leidas` (template ya era POST).
- **R3-05:** `validate_password` (validators de settings) en `registro_view`.
- **R3-06:** login responde idéntico genérico en 401 y 403 (muere el oráculo).
- Verificación: `check` limpio, `node --check main.js` OK, recovery 2/2, accesos 9/9.

## 12. Run 4 + DAST-lite — 2026-09-05 (0 findings)
- Hunt (seeds, errores, métodos, paginación, concurrencia, terceros, sesiones,
  descargas, búsqueda, deuda): todo descartado con evidencia.
- `pip audit`: 7 CVEs solo en `pip` 24.2 → actualizado a 26.2.1 → 0 vulns.
- `check --deploy`: solo W019 → SAMEORIGIN intencional (visor PDF), silenciado
  con justificación. Post-cambios: 0 issues en ambos modos.

## 11. Cierre — verificación final de los 20 hallazgos — 2026-09-05
Barrido en código: H-01 (decoradores ×4), H-02 (checks eliminar/restaurar),
H-03 (0 `|safe`), R2-01 (binding ×6), R2-03 (guardas), R2-04 (revalidación),
R2-02 (anti auto-voto + lock), R2-05 (redirect seguro ×6),
R3-01 (textContent), R3-02 (`|escapejs`), R3-03 (backend+settings),
R3-04 (`require_POST`), R3-05/06 (validate + genérico). Todo presente.
Suites: recovery 2/2 OK. Estado final: **20/20 mitigados y verificados**.
