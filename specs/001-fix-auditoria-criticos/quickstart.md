# Quickstart: validar las correcciones

Ejecutar desde `gestion_documental/` con el venv del proyecto.

## 1. Verificación estática

```bash
./venv/Scripts/python.exe manage.py check
./venv/Scripts/python.exe manage.py makemigrations --check --dry-run
```

Esperado: sin problemas y "No changes detected" (tras aplicar la migración de `auditoria`).

## 2. Pruebas

```bash
./venv/Scripts/python.exe manage.py test tests --noinput
```

Esperado: todas pasan, incluidas `tests/test_correcciones_auditoria.py`, `test_performance.py` y
`test_recovery_guards.py`. Tras el renombrado (R10), este comando ya no toca la BD de desarrollo.

## 3. Dependencias

```bash
./venv/Scripts/python.exe -m pip_audit -r requirements.txt
```

Esperado: `No known vulnerabilities found`.

## 4. Repositorio

```bash
git status --short --ignored gestion_documental/.env.bak gestion_documental/.env.example
```

Esperado: `.env.bak` aparece como ignorado (`!!`); `.env.example` sigue versionado.

## 5. Recorrido manual

| Escenario | Esperado |
|-----------|----------|
| Decana abre `/documentos/aprobar/` y `?urgente=1` | Carga, contadores coherentes ([contrato](contracts/rutas.md)). |
| Título `<img src=x onerror=alert(1)>` y búsqueda `img` | Se ve el texto literal y no hay alerta. |
| Descarga con cabecera `X-Forwarded-For: 8.8.8.8` | La auditoría registra `127.0.0.1`. |
| Docente sube v2 de un documento aprobado | Descarga entrega v2, estado Pendiente, la Coordinadora notificada. |
| Deshabilitar a un docente con sesión abierta | Su siguiente clic lo lleva al login. |
| "Visualizar archivo" en un PDF / un DOCX | PDF dentro del modal; DOCX con botón de descarga. |
| `/media/<ruta real>` | 404. |
| Auditoría tras login, solicitud, voto y habilitación | Cada evento listado con etiqueta en español. |
