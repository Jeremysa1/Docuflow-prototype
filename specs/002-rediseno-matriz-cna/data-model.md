# Data Model: Rediseño "Matriz de autoevaluación"

Sin cambios de esquema. Estructuras derivadas que entrega `MetricasService`
(`apps/documentos/metricas.py`), con caché por clave e invalidación con `bump_stats()`.

## Gradacion (valor)

| Campo | Tipo | Regla |
|-------|------|-------|
| `nivel` | int 0–5 | 0 sin evidencia (0 %), 1 no se cumple (1–59 %), 2 insatisfactorio (60–69 %), 3 aceptable (70–79 %), 4 alto grado (80–89 %), 5 pleno (≥90 %) |
| `etiqueta` | str | Texto en español del nivel |
| `porcentaje` | int | `round(aprobados / meta * 100)`, sin tope (puede pasar de 100) |

## CeldaFactor

| Campo | Tipo | Regla |
|-------|------|-------|
| `codigo` | str | `F1`…`F12` |
| `nombre` | str | Nombre corto sin punto final |
| `aprobados`, `pendientes` | int | Por factor (y por programa en la matriz) |
| `meta` | int | Meta de facultad del factor (`metas_por_factor`) |
| `gradacion` | Gradacion | Calculada con aprobados frente a meta |

## Huella (banner)

Lista de 12 `CeldaFactor` más `total_aprobados`, `total_meta` y `pendientes_envejecidos` (>3
días).

## HuellaPersonal (banner del docente)

12 meses (el actual y los 11 anteriores, `America/Bogota`). Por mes: `aprobadas`, `pendientes`,
`rechazadas` de sus propias evidencias (por `fecha_creacion`), más totales del docente. Solo se
consultan documentos con `autor = usuario`.

## Matriz

`filas`: 12 factores × `columnas`: programas con evidencias o con docentes, más una columna
"Facultad". Cada celda es una `CeldaFactor`. Consultas: un `values('factor_cna',
'programa').annotate(...)` fijo.

## ColaRevision

Pendientes ordenados por `fecha_modificacion` ascendente, con `dias_esperando` y `envejecido`
(>3). Tiempos: 4 puntos semanales (media y mediana en horas) desde la auditoría (R4).

## Pulso

30 días × {descargas, accesos denegados, solicitudes de acceso}. Descargas y accesos denegados
salen de `RegistroAuditoria`; las solicitudes salen de `SolicitudAcceso.fecha_solicitud`, que tiene
historia (la acción `SOLICITO_ACCESO` solo existe desde 2026-11-07). Conteos diarios agrupados por
fecha local (`America/Bogota`), más el total del período y la
variación frente a los 30 días anteriores.

## Visibilidad por rol

| Dato | Decana | Coordinadora | Docente |
|------|--------|--------------|---------|
| Huella de facultad | ✓ | ✓ | — |
| Huella personal | — | — | ✓ |
| Matriz factor × programa | ✓ | ✓ | — |
| Cola y tiempos de revisión | resumen | ✓ completa | — |
| Pulso de seguridad | ✓ | ✓ | — |
| Mis evidencias | — | — | ✓ |
