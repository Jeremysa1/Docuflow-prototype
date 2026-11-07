# Auditoría de Seguridad — Run 2 (corrida aditiva) — Docuflow-prototype / SIGEA

- **Fecha:** 2026-09-05 (UTC) · **Run:** 2 (el run 1 cubrió H-01..H-09; este run ataca huecos + código nuevo del hardening)
- **Metodología:** skill `security-audit-skill` (6 fases). Fases 1–3 con agentes paralelos + lectura directa; Fase 6 con 2 verificadores frescos.
- **Resultado:** 5 confirmados — **1 CRITICAL, 2 MEDIUM, 2 LOW** (R2-02 degradado HIGH→MEDIUM→LOW tras verificación: ver §5).

## Tabla priorizada

| ID | Sev. | Categoría | Título | Ubicación principal |
|---|---|---|---|---|
| R2-01 | CRITICAL | Auth / Business logic (session-state confusion) | Takeover por `token_validado` no ligado al email | `apps/usuarios/views.py:103-195` |
| R2-03 | MEDIUM | Access control (privilege mgmt sin guardas) | `actualizar_usuario`: auto-democión DECANA, stealth superuser, multi-DECANA | `apps/usuarios/services.py:318-331` |
| R2-04 | MEDIUM | Resource handling (validation gap) | `restaurar_version` reactiva archivos bloqueados sin revalidar | `apps/versiones/services.py:60-83` |
| R2-02 | LOW | Business logic (separation-of-duties) | Auto-voto del solicitante en sensibles (quórum fraudulento, no nueva lectura) | `apps/permisos/services.py:251-270` |
| R2-05 | LOW | Web-protocol (open redirect) | `redirect(HTTP_REFERER)` sin allowlist en ramas de error de descarga | `apps/documentos/views.py:456,493`, `apps/versiones/views.py:95` |

## R2-01 — Takeover por `token_validado` booleano sin ligar al email (CRITICAL)

- **Categoría:** Authentication / Business logic (state confusion). **Severidad:** CRITICAL — likelihood high (4 POST anónimos), impacto critical (ATO arbitrario incl. DECANA). Confidence high (verificado línea por línea + verificador independiente VERIFIED).
- **Ubicación:** `apps/usuarios/views.py:103-111` (fija `recovery_email` sin limpiar flag), `:136-151` (flag `True` puro en `:150`), `:172-195` (usa `email` de sesión en `:191` sin comparar), `apps/usuarios/services.py:202-236` (`cambiar_contrasena` no verifica token), `apps/usuarios/urls_auth.py:11-15` (sin login).
- **Evidencia:**
  ```python
  # recuperar_contrasena_view :108-110 — no toca token_validado
  UsuarioService.solicitar_recuperacion(email)
  request.session['recovery_email'] = email
  # validar_token_view :149-150 — booleano sin email
  request.session['token_validado'] = True
  # nueva_contrasena_view :174-175,191 — nunca compara
  email = request.session.get('recovery_email')
  token_validado = request.session.get('token_validado')
  ...
  resultado = UsuarioService.cambiar_contrasena(email, nueva)
  ```
- **Ataque (sesión anónima única):** 1) `POST /login/recuperar/ email=<propio>` (lee su propio token de su inbox), 2) `POST /login/recuperar/token/ token=<propio>` → flag, 3) `POST /login/recuperar/ email=<victima>` (flag sobrevive), 4) `POST /login/recuperar/nueva-contrasena/` → password de la víctima cambiado. Bypassea throttle 60s, 3 intentos y ventana 3min sin adivinar nada.
- **Remediación:** guardar `session['recovery_email_validado']=email` al validar y exigir igualdad en `nueva_contrasena_view`; limpiar `token_validado` en todo POST a `recuperar/`/`reenviar/`; defensa en profundidad: que `cambiar_contrasena` exija token vigente.

## R2-03 — `actualizar_usuario` sin guardas (MEDIUM)

- **Categoría:** Access control. **Severidad:** MEDIUM — requiere sesión DECANA; impacto high (lockout admin + persistencia sigilosa). Confidence high (VERIFIED).
- **Ubicación:** `apps/usuarios/services.py:318-331` (asigna `rol`/`programa` y `save()` sin checks), `apps/usuarios/views.py:314-326` (sin check self), `apps/usuarios/urls_usuarios.py:14`. Contraste: `deshabilitar_usuario` (`:298-304`) y `eliminar_usuario` (`:307-315`) SÍ protegen DECANA/self.
- **Ataques:** a) auto-democión `POST /usuarios/gestion/<propio>/editar/ rol=DOCENTE_PLANTA` → 0 DECANAs → DoS administrativo (todo `role_required('DECANA')` inalcanzable); b) la ex-decana conserva `is_staff/is_superuser` (el servicio no los toca; seed los crea en `crear_datos_iniciales.py:46-47`) → superusuario con disfraz de docente (`usuario_tiene_acceso` total + `/admin/`); c) multi-DECANA (modelo sin `UniqueConstraint`).
- **Remediación:** prohibir auto-cambio de rol propio, exigir ≥1 DECANA activa, sincronizar `is_staff/is_superuser` con el rol, unicidad de DECANA/COORDINADORA.

## R2-04 — `restaurar_version` sin revalidar (MEDIUM)

- **Categoría:** Resource/file handling. **Severidad:** MEDIUM — requiere autor+ y fila legacy/admin-plantada; impacto high (reintroduce tipos bloqueados al doc vivo + `read()` sin tope en memoria). Confidence high (VERIFIED).
- **Ubicación:** `apps/versiones/services.py:60-83` (`:65` `read()`+`ContentFile`, `:72-78` crea `Version`, `:81` `documento.archivo.save`) sin `validar_archivo_subido` (que `crear_version:25` y la vista `crear:43` SÍ usan); vista `apps/versiones/views.py:75-95` solo chequea autorización. Vector: filas pre-hardening o plantadas vía `/admin/` (sin validación).
- **Remediación:** validar extensión+tamaño del contenido restaurado antes de persistir (igual que `crear_version`); topar `read()` (stream/chunks).

## R2-02 — Auto-voto del solicitante en sensibles (LOW, degradado de MEDIUM)

- **Categoría:** Business logic (separation-of-duties). **Severidad:** LOW — corrección del verificador independiente: `usuario_tiene_acceso` (`permisos/services.py:85-87`) ya da lectura total a COORD/DECANA, así que el auto-voto no otorga lectura nueva; impacto real = fraude de quórum + `PermisoDocumento` persistente que sobrevive a una degradación de rol. Requiere rol privilegiado + 2º voto. Confidence medium-high.
- **Ubicación:** `apps/permisos/services.py:262-270` (sin `votante==solicitante: raise`), `:100-111` (solicitar solo bloquea autor), quórum `:322-326`, vista `:87-92`.
- **Ataque:** COORDINADOR solicita sensible ajeno y vota APROBADO en su propia solicitud (1/2 del quórum).
- **Remediación:** rechazar `votante == solicitud.solicitante` + `transaction.atomic()` + `select_for_update()` (hay TOCTOU aprueba-vs-rechaza concurrente como hardening).

## R2-05 — Open-redirect vía `Referer` en errores de descarga (LOW)

- **Categoría:** Web-protocol. **Severidad:** LOW — requiere auth + fallo + `Referer` atacante; impacto = bounce phishing desde dominio legítimo. Confidence high (VERIFIED).
- **Ubicación:** `apps/documentos/views.py:456` y `:493`, `apps/versiones/views.py:95`: `redirect(request.META.get('HTTP_REFERER', ...))` sin allowlist (contrasta con `notificaciones/views.py:33` que sí valida — el fix del run 1 no se aplicó aquí).
- **Ataque:** víctima logueada abre link atacante a `/documentos/99999/descargar/` (falla) con `Referer: https://evil` → `302 Location: https://evil` desde dominio confiable.
- **Remediación:** misma allowlist que `marcar_leida` o fallback fijo sin `Referer` crudo.

## Descartados (Fase 3 adversarial — no son findings)

- Bypass RBAC vía `/admin/`: solo la decana seed es staff/superuser; staff sin permisos ve admin vacío (default Django). Poder previsto, no bypass.
- X-Accel `rel_path`/`filename`: docs nuevos son `uuid+ext allowlist` (inyección imposible); `../` solo vía `/admin/` ya privilegiado + nginx fuera del repo → no reportable.
- `FileResponse(open())` LFI/TOCTOU: `ruta` solo manipulable por staff; sin actor local → no explotable web.
- `marcar_leida` GET/CSRF: filtro por usuario + allowlist + `SameSite=Lax` → impacto mínimo propio.
- Fuerza bruta distribuida / fixation / reutilización post-cambio: matemáticas inviables (3 intentos/3min/10⁶), limpieza `:194-195` OK.
- Token plaintext en BD visible en admin: requiere staff + ventana 3min → insider/hardening.
- Oráculo `buscar_ajax`/`busqueda_avanzada`: scoped + detalle bloquea contenido; discoverability diseñada.
- Fechas inválidas → 500 genérico (`DEBUG=False` default): robustez, no inyección.
- XFF spoofeable: solo polución de logs, ninguna decisión depende de IP.

## Hardening notes (no findings)

- `transaction.atomic()` + `select_for_update()` en votar/responder (TOCTOU concurrente).
- `actualizar_usuario`: `update_fields` en vez de `save()` completo; auditar cambios de rol.
- `Content-Disposition`: `filename*` RFC5987 + saneado de `"` para archivos legacy.
- Excluir `token_recuperacion` del admin (`exclude`/`readonly_fields`).
- `GET` sin side effects en `marcar_leida` (POST-only + `require_POST`).

## Positivos (run 2)

- `votar`: anti-doble-voto + motivo obligatorio + 1 rechazo deniega.
- Recovery: `secrets`, throttle 60s, 3 intentos, `secrets.token_urlsafe` en seeds, `SEED_ALLOW_PROD`.
- Uploads: doble validación vista+servicio+storage, nombres uuid.
- `email` enmascarado, no-enumeración (`return True`), `role_required` consistente, `DEBUG=False` default, console-backend prohibido en prod.

## Trazabilidad de fases

Fase 1 Recon ✓ (cambios + 5 hotspots) → Fase 2 Hunt ✓ (2 agentes, 5 candidatos) → Fase 3 Validate ✓ (5 confirmados, 8+ descartados) → Fase 4 Report ✓ (este archivo) → Fase 5 Structured ✓ (`informes/findings-run2-2026-09-05.json` validado) → Fase 6 Verification ✓ (R2-01 VERIFIED; R2-02 corregido a LOW; R2-03/R2-04/R2-05 VERIFIED).
