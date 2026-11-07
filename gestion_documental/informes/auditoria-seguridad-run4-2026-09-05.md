# Auditoría de Seguridad — Run 4 — Docuflow-prototype / SIGEA

- **Fecha:** 2026-09-05 (UTC) · **Run:** 4 (focos nunca auditados a fondo)
- **Resultado:** **0 findings explotables.** Rendimiento decreciente confirmado:
  run 1 = 9, run 2 = 5, run 3 = 6, run 4 = 0. Cobertura acumulada suficiente;
  no se recomienda run 5 salvo cambios grandes de código.

## Lo que se cazó (2 agentes, todo descartado con evidencia)

**Agente A — seeds, errores, métodos, paginación, concurrencia:**
- Seeds/fixtures: prod bloqueado sin `SEED_ALLOW_PROD`, passwords aleatorios,
  fixture solo hashes pbkdf2 (4 guesses comunes = False). Sin plaintext → sin takeover.
- Error pages: `linebreaksbr` escapa, 404 genérico, recovery sin token en URL.
- Métodos: toda vista mutante exige POST; `get_page()` + allowlists en orden.
- Concurrencia: `unique_together(solicitante, documento)` convierte la raza en
  `IntegrityError` cosmético; lote idempotente con actor autorizado.

**Agente B — terceros, sesiones, descargas, búsqueda, deuda:**
- PII a terceros (ui-avatars, gview, unpkg sin SRI, sin CSP): sin cadena explotable
  por actor app (gview no autenticado → bloqueado por login) → hardening conocido.
- Sesiones: inactividad real 15min deslizante; falta lifetime absoluto (Django no lo
  trae); logout con flush; sin leak de sessionid → hardening.
- Descargas: `FileResponse` cierra handle por diseño; `..` bloqueado + nombres uuid →
  docente no inyecta path; `autor_query` no expone emails (solo nombre/rol).
- TODO/FIXME: 0 en código (1 nota de fix ya aplicado).

## DAST-lite local (sin internet, contra este entorno)

- `pip install pip-audit` + `pip audit`: 7 vulns solo en `pip` 24.2 (herramienta del
  venv, no la app) → **`pip` actualizado a 26.2.1** → re-audit: **0 vulnerabilidades**
  (Django 6.1, Pillow, openpyxl, reportlab limpios).
- `manage.py check --deploy` (DEBUG=False): 1 único warning W019
  (`X-Frame-Options` SAMEORIGIN vs DENY) → **documentado y silenciado a conciencia**
  (`SILENCED_SYSTEM_CHECKS`): SAMEORIGIN es necesario para el visor PDF inline;
  DENY lo rompería. Resto (HSTS, cookies, SSL, nosniff, referrer): limpio.
- Post-cambios: `check --deploy` = 0 issues, `check` dev = 0 issues.

## Justificación de los 2 cambios aplicados

1. **Upgrade `pip` 24.2 → 26.2.1:** única superficie con CVEs conocidos del entorno;
   es tooling del venv, cero riesgo para la app. Porque un instalador vulnerable
   compromete la cadena de suministro local.
2. **Silenciar W019 con comentario:** porque el warning es correcto en general pero
   inaplicable aquí (visor PDF mismo-origen por diseño); silenciarlo con
   justificación escrita evita que futuros `check --deploy` lo oculten entre ruido
   y deja constancia de la decisión.

## Guía ZAP local (cuando quieras, en tu máquina)

1. `python manage.py runserver 127.0.0.1:8000` 2. ZAP → Automated Scan
   `http://127.0.0.1:8000` (ataque solo a tu localhost). 3. Ignora alertas de
   `DEBUG` (tracebacks) — son artefacto de dev, en prod `DEBUG=False`.
   4. Pásame el HTML del reporte y lo triago contra estos 4 runs.

## Trazabilidad

Fase 1 Recon ✓ (focos restantes) → Fase 2 Hunt ✓ (2 agentes, 0 candidatos viables) →
Fase 3 Validate ✓ (cada foco disprobado con evidencia) → Fase 4 Report ✓ →
Fase 5 Structured ✓ (`findings-run4-2026-09-05.json` = `[]`, PASS) →
Fase 6 Verification ✓ (este archivo reconcilia: nada que corregir salvo pip+W019).
