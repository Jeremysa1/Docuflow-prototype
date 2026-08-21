# Plan de Rediseño UI/UX Institucional - Docuflow (Definitivo)

Propuesta de rediseño integral y total de la interfaz para el sistema de gestión documental Docuflow. Siguiendo tus indicaciones, vamos a erradicar cualquier aspecto genérico (Bootstrap) y crearemos un sistema visual a la medida, garantizando que la interfaz "respire" y no se sienta apretada.

## User Review Required

> [!IMPORTANT]
> He añadido la estrategia para los **Íconos** que solicitaste. Revisa esta última versión, y si está perfecta, ¡dame la orden ("Adelante") para empezar a modificar el código!

## Proposed Changes

### 1. Sistema de Diseño (Vanilla CSS Puro) y "Respiración"

El mayor problema de las interfaces institucionales genéricas es la falta de espacio (densidad muy alta). Vamos a solucionar esto aplicando un diseño "aireado" (White Space):

#### **Layout Principal y Espaciado (Breathing Room)**
- **Adiós al encierro:** Se implementarán márgenes y paddings generosos (`2rem` a `3rem` mínimos entre secciones). La información ya no estará pegada a los bordes de la pantalla.
- **Navegación:** Un Sidebar fijo a la izquierda (colapsable), y un área de contenido principal que tiene un "max-width" controlado para que la vista no se estire demasiado en monitores grandes, lo cual reduce la fatiga visual.
- **Desvinculación de Bootstrap:** Se eliminarán TODAS las clases de Bootstrap (`col-md-6`, `row`, `container`, `card`, `btn-primary`, etc.) de las vistas internas. Todo funcionará con CSS Grid y Flexbox nativo para tener control absoluto.

#### **Diseño de Tarjetas (Cards) Únicas**
- Las tarjetas tendrán mucho espacio interno (`padding: 2.5rem`).
- En lugar de bordes duros de Bootstrap, usarán un fondo blanco puro sobre el fondo perla de la app (`#F8FAFC`), con **sombras sutiles y elegantes** que les darán profundidad sin sentirse pesadas o muy cercanas.

#### **Íconos y Consistencia Visual**
- Se evaluarán los íconos actuales. Si usas librerías como FontAwesome o SVGs sueltos, mantendremos su esencia. 
- Sin embargo, para cumplir con las directrices de la *Skill*, nos aseguraremos de que **todos los íconos tengan el mismo grosor (stroke-width)**, tamaño base (ej. `20x20` o `24x24`), y color semántico. Si detectamos inconsistencias, los unificaremos usando un set premium y limpio (como *Lucide* o *Heroicons*) que combine a la perfección con la tipografía. 
- Los íconos en el menú lateral y botones tendrán el doble de espacio de separación con el texto para contribuir a la sensación de frescura.

#### **Paleta de Colores y Tipografía**
- **Azules Institucionales:** Se mantendrán intactos para acentos, botones primarios y el Sidebar.
- **Fuentes:** `Inter` y `Outfit`. Incrementaremos el `line-height` a `1.6` o `1.7` en los textos largos para que la lectura sea relajada.

---

### 2. Archivos a Modificar (Scope Completo)

#### **Limpieza y Estructura Base**
- `gestion_documental/templates/base.html` **[MODIFY]** -> Eliminaremos el CDN/archivos de Bootstrap. Se construirá la estructura del Sidebar y Topbar desde cero.
- `gestion_documental/static/css/ui-ux-pro.css` **[NEW]** -> Hoja de estilos principal con todas las variables y el sistema de grillas CSS.

*(Nota: Las vistas de Login y Registro se mantendrán protegidas con su diseño propio).*

#### **Módulos a Transformar Completamente (Inyectando el nuevo diseño y espacios)**
1. **Documentos**
   - `dashboard.html` (Métricas amplias, sin estar apretadas).
   - `lista.html`, `mis_documentos.html`, `busqueda_avanzada.html` (Tablas nativas personalizadas, filas con buen alto `tr { height: 60px }`).
   - `subir.html`, `detalle.html`, `aprobar_documentos.html` (Formularios centrados, con inputs grandes y separados).
2. **Usuarios**
   - `perfil.html`, `gestion.html`
3. **Notificaciones y Auditoría**
   - `notificaciones/lista.html`, `auditoria/lista.html`
4. **Versiones y Permisos**
   - `versiones/lista.html`, `versiones/crear.html`
   - `permisos/solicitudes.html`, `permisos/gestionar_accesos.html`

## Verification Plan

### Manual Verification
1. Comprobaremos que la interfaz ya no se siente "pegada a la pantalla", validando los nuevos márgenes.
2. Buscaremos clases de Bootstrap para asegurar que fue eliminado al 100%.
3. Confirmaremos que la iconografía sea 100% consistente en tamaño y trazo.
4. Validaremos que las pantallas de Login/Registro siguen luciendo exactamente igual.
