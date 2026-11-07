# Contrato: componentes y template tags

## Template tags (`core/templatetags/sigea.py`, `{% load sigea %}`)

| Tag / filtro | Entrada | Salida |
|--------------|---------|--------|
| `{% icono "nombre" clase="" etiqueta="" %}` | nombre del sprite | `<svg aria-hidden>` o con `aria-label` si hay etiqueta; nombre inexistente → error en DEBUG |
| `{% chip_factor celda %}` | CeldaFactor | Chip "F3 · 4 / 20" en el tono de su gradación, con `title` y la etiqueta |
| `{% estado_documento doc %}` | Documento | Insignia con forma y color del estado (+ reloj si >3 días, + candado si sensible) |
| `{{ n|plural:"evidencia,evidencias" }}` | int | "1 evidencia" / "2 evidencias" |
| `{{ usuario|iniciales }}` | Usuario | "AD"; nunca vacío ("?" si no hay nombre) |

## Plantillas de inclusión (`templates/componentes/`)

| Componente | Contexto | Requisitos |
|------------|----------|------------|
| `banner_huella.html` | `huella`, `rol`, `titular`, `cifra`, `accion` | Banda azul, 12 columnas con `--altura`, `aria-label` con el resumen completo; móvil en franja |
| `matriz.html` | `matriz` | `<table>` con encabezados reales; celdas enlazadas a búsqueda filtrada; desplazamiento propio |
| `cola_revision.html` | `cola`, `tiempos` | Lista ordenada por antigüedad; acciones aprobar/rechazar; sparkline de 4 semanas con cifras |
| `pulso.html` | `pulso` | 3 series de 30 días en SVG, total y variación, enlace a la auditoría filtrada |
| `estado_vacio.html` | `titulo`, `texto`, `accion` | Sin ilustración de stock; icono de línea, texto y acción |
| `tabla_tarjetas` (CSS) | `<table class="sg-tabla">` | Debajo de 768 px cada fila es una tarjeta con `data-label` por celda |
| `boton` (CSS) | `.sg-btn`, `--primario` (solo acción reservada), `--secundario`, `--peligro` | Altura mínima de 44 px, estado de carga `aria-busy` |

## Shell (`templates/base.html`)

| Zona | Contenido |
|------|-----------|
| Escritorio | Riel lateral azul (marca, destinos por rol, usuario, salir); contenido a la derecha con migas y el `{% block banner %}` |
| Móvil | Barra superior con marca y notificaciones; barra inferior con 4 destinos + "Más" |
| Común | Enlace "Saltar al contenido", mensajes de Django como avisos con icono, confirmación modal accesible (reemplaza `sigeaConfirm`) |
