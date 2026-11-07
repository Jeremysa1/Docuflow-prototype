# Research: Rediseño "Matriz de autoevaluación"

## R1. Convivencia con el CSS actual durante las fases

- **Decision**: renombrar `ui-ux-pro.css` a `legacy.css` y cargarlo con
  `@import url(legacy.css) layer(legacy)`; el sistema nuevo va en capas posteriores
  (`@layer legacy, base, componentes, paginas`). Se borra en la fase 3.
- **Rationale**: entrega por fases sin pantallas rotas; las capas hacen que el CSS nuevo gane sin
  `!important`.
- **Alternatives**: migrar todo de una vez (descartado por la aclaración); prefijar todo el
  heredado (más trabajo para algo que se va a borrar).

## R2. Gráficos sin librería

- **Decision**: la huella, la matriz, las barras de cantidad frente a meta y el pulso de 30 días
  se dibujan como SVG o HTML en plantillas de inclusión, con datos de `MetricasService`. Cada
  gráfico tiene cifras visibles y `<title>`/`aria-label`.
- **Rationale**: cero JavaScript para ver datos, accesible, sin dependencias y fácil de probar
  en el HTML.
- **Alternatives**: Chart.js o ApexCharts (dependencia, canvas poco accesible, estética genérica).

## R3. Gradación CNA

- **Decision**: `gradacion(aprobados, meta)` devuelve un nivel de 0 a 5:
  - 0: sin evidencia (0 %);
  - 1: no se cumple (1–59 %);
  - 2: insatisfactorio (60–69 %);
  - 3: aceptable (70–79 %);
  - 4: alto grado (80–89 %);
  - 5: pleno (90 % o más).

  El nivel corresponde a los tokens `--sg-grad-0` … `--sg-grad-5` y a una etiqueta en español.
- **Rationale**: es la escala elegida en la aclaración y se aplica igual en todo el sistema.

## R4. Tiempos de revisión

- **Decision**: para cada documento revisado en 30 días, el tiempo es el primer `APROBO` o
  `RECHAZO` de la auditoría menos la `fecha_creacion` del documento, o el último `NUEVA_VERSION`
  si existe. Se reportan la media y la mediana por semana (4 puntos).
- **Rationale**: no requiere modelo nuevo; la auditoría ya tiene las fechas.
- **Alternatives**: añadir `fecha_revision` a `Documento` (migración y doble fuente de verdad).

## R5. Fuentes e iconos locales

- **Decision**:
  - Public Sans WOFF2 (pesos 400, 600, 700, 800) en `static/fonts`, cargada con `@font-face` y
    `font-display: swap`.
  - Iconos Lucide copiados en un sprite `static/icons/lucide.svg` con solo los usados (unos 40),
    renderizados por el tag `{% icono "nombre" %}` como `<svg><use href=…#nombre>`.
  - Se quita el script de unpkg y `lucide.createIcons()`.
- **Rationale**: sin terceros (Zero-Trust y CSP), sin parpadeo de iconos y un único grosor de
  trazo controlado por CSS.
- **Alternatives**: seguir con el CDN (dependencia externa); otra familia de iconos (Lucide ya es
  coherente con la línea elegida).

## R6. Tipografía

- **Decision**: una familia, Public Sans, con cifras tabulares (`font-variant-numeric:
  tabular-nums`). La escala de 5 pasos tiene base 16 px y es fluida en móvil:

  | Token | Tamaño | Uso |
  |-------|--------|-----|
  | `--sg-t-1` | 12 px | metadatos |
  | `--sg-t-2` | 14 px | interfaz secundaria |
  | `--sg-t-3` | 16 px | cuerpo |
  | `--sg-t-4` | 20 px | títulos de sección |
  | `--sg-t-5` | 32 px | cifra o título de página |

  La cifra del banner usa `--sg-t-6`, de 56 px, el único tamaño de exhibición.
- **Rationale**: es un sistema que se opera (Operate): la marca vive en la precisión de las
  cifras, no en una fuente de exhibición. Public Sans no está en la lista de fuentes por defecto
  que impeccable pide evitar.

## R7. Banner "huella de acreditación"

- **Decision**: una banda azul `#142a59` a todo el ancho del área de contenido, de unos 220 px en
  escritorio.
  - A la izquierda va el titular del rol y la cifra grande en blanco.
  - A la derecha, 12 columnas verticales (F1–F12): la altura de cada una es su porcentaje frente
    a la meta (con un tope del 100 %) y el tono es su gradación sobre el azul. La etiqueta del
    factor va al pie de cada columna.
  - Para el docente el banner es su huella personal: las 12 columnas son sus últimos 12 meses y
    cada una apila sus evidencias de ese mes por estado (aprobadas en blanco, en revisión con
    borde punteado, rechazadas con trazo rojo). Nunca muestra datos de la facultad.
  - Al cargar, las columnas crecen una sola vez (300 ms, escalonadas), salvo con movimiento
    reducido.
  - En móvil, las 12 columnas pasan a una franja horizontal compacta bajo la cifra.
- **Rationale**: es el momento memorable que pidió el usuario. Se hace con datos reales, distintos
  para cada facultad y cada día: representa la plataforma y no puede ser una ilustración de stock.

## R8. Navegación móvil

- **Decision**: en móvil hay una barra inferior con 4 destinos por rol y "Más" (que abre una hoja
  con el resto); en escritorio, un riel lateral azul de 248 px que se puede contraer a 72 px.
  Los destinos se generan en un único helper de contexto por rol.
- **Rationale**: los docentes usan el celular la mitad del tiempo y la barra inferior queda al
  alcance del pulgar.

## R9. Páginas de error y 403

- **Decision**: `role_required` lanza `PermissionDenied` en vez de devolver
  `HttpResponseForbidden` en texto plano. Se crean `templates/403.html`, `404.html` y `500.html`
  (la 500 sin depender del contexto de la petición) y `error_403.html` / `error_404.html` de
  usuarios pasan a extenderlas.
- **Rationale**: un solo diseño de error, siempre con un camino de vuelta.

## R10. Admin Unfold

- **Decision**: regenerar `UNFOLD["COLORS"]["primary"]` como escala OKLCH centrada en `#142a59`
  (700 ≈ marca), con la fuente Public Sans en `admin_unfold.css`.
- **Rationale**: es el mismo producto; hoy el admin usa el azul por defecto de Tailwind.

## R11. Vigilancia del sistema de diseño

- **Decision**: `tests/test_reglas_diseno.py` falla si una plantilla migrada tiene:
  - `style="` con algo que no sea una variable de datos (`--valor`, `--altura`);
  - colores hex fuera de `tokens.css`;
  - `font-size` por debajo de 12 px en el CSS nuevo;
  - `!important` en `static/css/sigea/`;
  - emojis en plantillas.

  Además, el detector de impeccable corre al final de cada fase.
- **Rationale**: lo que no se vigila vuelve a degradarse (132 colores hoy).
