# Revisión de seguridad: rediseño "Matriz de autoevaluación" (spec 002)

- **Fecha:** 2026-11-07
- **Alcance:** `specs/002-rediseno-matriz-cna`
- **Motivo:** la constitución exige una revisión documentada al tocar permisos, descargas o
  auditoría. Este rediseño cambia cómo se responde a un acceso denegado, añade métricas que leen
  la auditoría y retira dependencias de terceros.

## Cambios con impacto de seguridad

| Cambio | Riesgo evaluado | Decisión y prueba |
|--------|-----------------|-------------------|
| `role_required`, `document_permission_required` y las vistas de permisos y versiones lanzan `PermissionDenied` en lugar de devolver un 403 en texto plano | Que un 403 deje de serlo o filtre información | Sigue respondiendo 403 con `templates/403.html`, que no muestra datos del recurso. `tests/test_paginas_error.py`, `tests/test_us1_aprobacion.py`, `tests/test_us7_vista_previa.py` |
| `gestionar_accesos_view` ahora audita `ACCESO_DENEGADO` antes de negar | Trazabilidad incompleta | Mejora: el intento queda registrado |
| Métricas de los paneles (`apps/documentos/metricas.py`) | Exposición de datos de la facultad a docentes (Zero-Trust) | El docente solo recibe `huella_personal` (`autor=usuario`); la matriz, la cola y el pulso solo se calculan para Decana y Coordinadora. `tests/test_paneles_rol.py::test_docente_solo_ve_lo_suyo` |
| Navegación por rol (`apps/usuarios/context_processors.navegacion`) | Mostrar destinos a los que el rol no puede entrar | Usa las mismas reglas que las vistas; las vistas siguen comprobando permisos. `test_navegacion_respeta_el_rol` |
| Login con huella decorativa | Mostrar el avance real a un visitante sin sesión | Las alturas del login son fijas y decorativas, no consultan datos |
| Retiro de Google Fonts y de Lucide desde unpkg | Dependencia de terceros, seguimiento y cadena de suministro | Fuentes (OFL) e iconos (ISC) servidos desde `static/`, con licencias incluidas |
| Retiro de `main.js` y `legacy.css` | Código heredado con `innerHTML` | La búsqueda rápida nueva (`static/js/sigea.js`) construye resultados con nodos de texto |
| Mensajes de error en eliminar, restaurar y exportar | Fuga de detalles internos | Mensajes fijos y `logger.exception` (cierra el riesgo residual de la revisión 001) |
| Búsqueda por programa (`?programa=`) | Inyección o saltar filtros de visibilidad | Solo se acepta un entero y se aplica después del filtro por rol existente |

## Verificación

- `manage.py check`: sin problemas.
- `manage.py test tests`: 86 pruebas OK, incluidas las de reglas de diseño (sin estilos en línea
  salvo variables de datos, sin colores fuera de tokens y sin emojis).
- `collectstatic` con el almacenamiento de manifiesto de producción: genera 174 archivos con hash.

## Riesgos residuales

- Los iconos se sirven desde un sprite estático. Si se agrega una CSP estricta, debe permitir
  `img-src 'self'`; el sprite no se toca.
- Siguen pendientes de la auditoría M2 (bloqueo por cuenta), M3 (enumeración en la
  recuperación), M5 (metadatos de documentos sensibles en la búsqueda) y M6 (autoaprobación).
