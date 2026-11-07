# Implementation Plan: Rediseño visual "Matriz de autoevaluación"

**Branch**: `002-rediseno-matriz-cna` | **Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-rediseno-matriz-cna/spec.md`

## Summary

Se reemplaza la estética genérica por un sistema de diseño propio basado en la matriz de
autoevaluación CNA, conservando el azul `#142a59` y el blanco. Se entrega en tres fases revisables:

1. **Base:** tokens, shell, banner "huella de acreditación" y los 3 paneles por rol con métricas.
2. **Evidencias:** búsqueda, mis documentos, detalle, subir, editar, versiones, papelera,
   aprobación y Factores CNA.
3. **Gestión y acceso:** accesos, auditoría, usuarios, notificaciones, perfil, login y
   recuperación, páginas de error y admin; al final se retira el CSS heredado.

Los gráficos se dibujan como SVG en el servidor a partir de servicios de métricas nuevos, sin
librerías de gráficos.

## Technical Context

**Language/Version**: Python 3.12, Django 6.1.3, plantillas Django, CSS propio, JavaScript sin
framework

**Primary Dependencies**: sin dependencias nuevas de Python. Assets propios: Public Sans (WOFF2
servida localmente) e iconos Lucide (licencia ISC) copiados como sprite SVG

**Storage**: PostgreSQL (sin cambios de esquema); métricas derivadas de `Documento`,
`RegistroAuditoria` y `SolicitudAcceso`

**Testing**: `manage.py test tests` (django.test), más una prueba de reglas de diseño que
recorre plantillas y CSS

**Target Platform**: navegadores modernos de escritorio y móvil (Chrome, Edge, Safari iOS,
Chrome Android)

**Project Type**: aplicación web Django monolítica

**Performance Goals**: paneles con número fijo de consultas (sin N+1); métricas con caché e
invalidación por `bump_stats()`; CSS nuevo menor de 60 KB sin comprimir

**Constraints**:
- no cambiar rutas, permisos ni reglas de negocio;
- WCAG 2.1 AA;
- base de 16 px;
- áreas táctiles de 44 px;
- `prefers-reduced-motion`;
- sin CDN de fuentes ni de iconos.

**Scale/Scope**: 25 plantillas de app y 2 de proyecto, 3 roles, 12 factores, ~10 usuarios

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple | Estado |
|-----------|----------------|--------|
| I. Zero-Trust | Los datos de los paneles pasan por los servicios existentes con el filtro de rol. El docente solo ve datos propios: ni huella de facultad, ni matriz, ni pulso. Se eliminan los CDN externos (fuentes y Lucide desde unpkg). | ✅ |
| II. Auditoría | Solo se lee la auditoría (tiempos de revisión y pulso); no se modifica. | ✅ |
| III. Capa de servicios | Métricas en `apps/documentos/metricas.py` (`MetricasService`); las vistas solo las piden. | ✅ |
| IV. Seguridad por defecto | Assets locales; sin estilos ni scripts en línea nuevos (la prueba de reglas de diseño lo vigila). | ✅ |
| V. Pruebas | Pruebas de métricas, de paneles por rol, de páginas de error y de reglas de diseño. | ✅ |
| VI. Dominio CNA | La gradación CNA es el eje del sistema; textos en español con tuteo; sistema de diseño único (`static/css/sigea/`). | ✅ |

**Re-check post-diseño**: ✅. Sin violaciones; no hace falta "Complexity Tracking".

## Project Structure

### Documentation (this feature)

```text
specs/002-rediseno-matriz-cna/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── tokens.md          # tokens del sistema de diseño
│   └── componentes.md     # contratos de los componentes y template tags
└── tasks.md
```

### Source Code

```text
gestion_documental/
├── static/
│   ├── css/sigea/
│   │   ├── tokens.css        # colores, gradación, tipos, espacios, radios
│   │   ├── base.css          # reset, tipografía, foco, reduced motion
│   │   ├── shell.css         # riel lateral, barra móvil, banner
│   │   ├── componentes.css   # botones, chips, tablas→tarjetas, formularios, estados
│   │   └── graficos.css      # huella, matriz, pulso, barras
│   ├── css/legacy.css        # ui-ux-pro.css renombrado, cargado en @layer legacy hasta la fase 3
│   ├── fonts/public-sans/    # WOFF2 400/600/700/800
│   ├── icons/lucide.svg      # sprite con los iconos usados
│   └── js/sigea.js           # menú móvil, confirmaciones, estado de carga (reemplaza main.js)
├── templates/
│   ├── base.html             # shell nuevo
│   ├── componentes/          # banner_huella, matriz, pulso, chip_gradacion, estado_vacio, …
│   ├── 403.html  404.html  500.html
│   └── partials/paginacion.html
├── core/templatetags/sigea.py   # {% icono %}, {% chip_factor %}, filtros de gradación
├── apps/documentos/metricas.py  # MetricasService
├── apps/*/templates/...         # 25 plantillas migradas por fases
├── config/settings.py           # UNFOLD COLORS desde #142a59; handlers de error
└── tests/
    ├── test_metricas.py
    ├── test_paneles_rol.py
    ├── test_paginas_error.py
    └── test_reglas_diseno.py
```

**Structure Decision**: el sistema de diseño vive en `static/css/sigea/` con nombres de clase
`sg-*`. El CSS heredado se carga dentro de `@layer legacy`, así las páginas aún no migradas siguen
viéndose y las nuevas siempre ganan. La fase 3 lo elimina.

## Phases

| Fase | Contenido | Revisión del usuario |
|------|-----------|----------------------|
| 1 | Tokens, fuentes, iconos, shell, banner huella, 3 paneles, métricas, páginas de error | Sí |
| 2 | Búsqueda, mis documentos, detalle, subir, editar, versiones, papelera, aprobación, Factores CNA | Sí |
| 3 | Accesos, solicitudes, auditoría, usuarios, notificaciones, perfil, login y recuperación, admin, retiro del CSS heredado, revisión final | Sí |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Durante la migración conviven dos sistemas de estilos (`static/css/sigea/` y `legacy.css`), lo que el principio VI desaconseja | Las pantallas aún no migradas deben seguir funcionando | Migrar en un único cambio sin red; la convivencia termina en T054, que borra `legacy.css`, y T061 enmienda el principio VI para nombrar el sistema nuevo |
