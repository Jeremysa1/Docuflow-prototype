# Quickstart: validar el rediseño

Desde `gestion_documental/` con el venv.

## Al final de cada fase

```bash
./venv/Scripts/python.exe manage.py check
./venv/Scripts/python.exe manage.py test tests --noinput
```

Esperado: todo pasa, incluida `tests/test_reglas_diseno.py` sobre las plantillas migradas en la
fase.

```bash
"C:/Users/USUARIO/.claude/plugins/cache/impeccable/impeccable/4.8.0/skills/impeccable/scripts/impeccable" detect --json templates apps static/css/sigea
```

Esperado: sin hallazgos en lo migrado.

## Recorrido visual

Con el servidor de desarrollo y una sesión de cada rol, a 1440 × 900 y a 390 × 844.

| Fase | Pantallas | Qué comprobar |
|------|-----------|---------------|
| 1 | Panel de Decana, Coordinadora y docente; 403, 404 y 500 | La huella usa los datos reales (F3 y F7 con avance); la cifra "6 / 205"; la cola ordenada; el pulso con enlace; nada por debajo de 12 px; foco visible con Tab |
| 2 | Búsqueda, mis documentos, detalle, subir, editar, versiones, papelera, aprobación, Factores CNA | Tablas como tarjetas en móvil, chips de factor iguales en todas, estados por forma |
| 3 | Accesos, solicitudes, auditoría, usuarios, notificaciones, perfil, login y recuperación, admin | Un solo tono (tú), sin emojis, admin con la misma paleta; `legacy.css` ya no se carga |

## Accesibilidad

- Navegar con teclado: todo control es alcanzable y tiene foco visible.
- Activar "reducir movimiento" en el sistema: la huella aparece sin animación.
- Zoom del navegador al 200 %: sin pérdida de contenido.
