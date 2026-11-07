---
name: SIGEA
description: Sistema Integrado de Gestión de Evidencias para la Acreditación, leído como la matriz del informe de autoevaluación CNA.
colors:
  marca: "#142a59"
  marca-2: "#1c3a78"
  marca-3: "#2a4b8f"
  accion: "#1f4fd1"
  accion-2: "#1a43b3"
  grad-0: "#eef1f6"
  grad-1: "#d6e0f3"
  grad-2: "#a9bde6"
  grad-3: "#4a6cc0"
  grad-4: "#2f56b0"
  grad-5: "#142a59"
  ok: "#1f6f4a"
  ok-fondo: "#e6f2ec"
  pendiente: "#1f4fd1"
  pendiente-fondo: "#e8eefc"
  alerta: "#9a5b00"
  alerta-fondo: "#fbf1e1"
  error: "#b3261e"
  error-fondo: "#fbe9e7"
  sensible: "#5b2a86"
  sensible-fondo: "#f1eaf7"
  blanco: "#ffffff"
  papel: "#f5f7fb"
  renglon: "#dfe4ee"
  renglon-2: "#c5cddd"
  texto: "#142a59"
  texto-2: "#4d5871"
  texto-3: "#636d86"
  texto-inverso-2: "#c9d3ea"
typography:
  display:
    fontFamily: "Public Sans, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "clamp(2.5rem, 5vw, 3.5rem)"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.03em"
    fontFeature: "tnum"
  headline:
    fontFamily: "Public Sans, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "2rem"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Public Sans, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Public Sans, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: "tnum"
  body-sm:
    fontFamily: "Public Sans, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: "tnum"
  label:
    fontFamily: "Public Sans, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 700
    lineHeight: 1
    fontFeature: "tnum"
rounded:
  r-1: "4px"
  r-2: "8px"
  pill: "999px"
spacing:
  e-1: "4px"
  e-2: "8px"
  e-3: "12px"
  e-4: "16px"
  e-5: "24px"
  e-6: "32px"
  e-7: "48px"
  toque: "44px"
components:
  button-primary:
    backgroundColor: "{colors.accion}"
    textColor: "{colors.blanco}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.r-2}"
    padding: "0 16px"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.accion-2}"
    textColor: "{colors.blanco}"
  button-secondary:
    backgroundColor: "{colors.blanco}"
    textColor: "{colors.marca}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.r-2}"
    padding: "0 16px"
    height: "44px"
  button-secondary-hover:
    backgroundColor: "{colors.papel}"
    textColor: "{colors.marca}"
  button-marca:
    backgroundColor: "{colors.marca}"
    textColor: "{colors.blanco}"
    rounded: "{rounded.r-2}"
    padding: "0 16px"
    height: "44px"
  button-peligro:
    backgroundColor: "{colors.blanco}"
    textColor: "{colors.error}"
    rounded: "{rounded.r-2}"
    height: "44px"
  chip-factor-grad-0:
    backgroundColor: "{colors.grad-0}"
    textColor: "{colors.texto-2}"
    typography: "{typography.label}"
    rounded: "{rounded.r-1}"
    padding: "0 8px"
    height: "28px"
  chip-factor-grad-2:
    backgroundColor: "{colors.grad-2}"
    textColor: "{colors.marca}"
    typography: "{typography.label}"
    rounded: "{rounded.r-1}"
    padding: "0 8px"
    height: "28px"
  chip-factor-grad-5:
    backgroundColor: "{colors.grad-5}"
    textColor: "{colors.blanco}"
    typography: "{typography.label}"
    rounded: "{rounded.r-1}"
    padding: "0 8px"
    height: "28px"
  estado-aprobado:
    backgroundColor: "{colors.ok-fondo}"
    textColor: "{colors.ok}"
    typography: "{typography.label}"
    rounded: "{rounded.r-1}"
    padding: "0 8px"
    height: "28px"
  estado-pendiente:
    backgroundColor: "{colors.pendiente-fondo}"
    textColor: "{colors.pendiente}"
    typography: "{typography.label}"
    rounded: "{rounded.r-1}"
    padding: "0 8px"
    height: "28px"
  input:
    backgroundColor: "{colors.blanco}"
    textColor: "{colors.texto}"
    typography: "{typography.body}"
    rounded: "{rounded.r-2}"
    padding: "8px 12px"
    height: "44px"
  riel-enlace:
    backgroundColor: "{colors.marca}"
    textColor: "{colors.texto-inverso-2}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.r-2}"
    padding: "0 12px"
    height: "44px"
  riel-enlace-actual:
    backgroundColor: "{colors.blanco}"
    textColor: "{colors.marca}"
  hoja:
    backgroundColor: "{colors.blanco}"
    rounded: "{rounded.r-2}"
    padding: "24px"
  banner-huella:
    backgroundColor: "{colors.marca}"
    textColor: "{colors.blanco}"
    rounded: "{rounded.r-2}"
    padding: "32px 32px 24px"
---

# Design System: SIGEA

## Overview

**Creative North Star: "Matriz de autoevaluación"**

SIGEA se lee como la matriz del informe de autoevaluación CNA. Cada número es cantidad frente a meta ("4 / 20", "6 / 205"), y la gradación de cumplimiento del CNA (sin evidencia, no se cumple, insatisfactorio, aceptable, alto grado, pleno) es la única escala de azules del sistema: la misma en las celdas de la matriz, en los chips de factor, en las barras y en la huella del banner. Si un azul aparece, significa un grado.

El mundo es azul institucional y blanco. Un riel lateral azul marca (#142a59) con texto blanco sostiene la navegación; el trabajo ocurre sobre blanco, separado por renglones finos, en hojas planas con borde de 1 px y no en tarjetas decorativas. La densidad es de documento de trabajo: tablas, listas de filas, metadatos en definición, todo con cifras tabulares. Un único azul vivo (#1f4fd1) se reserva para la acción pendiente del usuario y para el foco.

El estado nunca depende solo del color: aprobado es sólido, pendiente lleva borde punteado, rechazado va tachado, el envejecido (más de 3 días) es ámbar punteado con reloj de arena y el sensible lleva candado en morado. Las directivas y los docentes leen lo mismo en escritorio y en móvil, donde las tablas se vuelven fichas y la matriz se vuelve lista por factor.

**Key Characteristics:**
- Una sola escala de azules (gradación CNA de 6 niveles) con significado fijo.
- Cantidad frente a meta en toda cifra de avance.
- Un azul de acción reservado; el resto de los botones son neutros o de marca.
- Estado por forma más color.
- Una familia (Public Sans, local) con cifras tabulares y escala de 6 pasos.
- Plano: renglones y bordes en lugar de sombras; la sombra solo para lo que flota.
- Iconos Lucide de trazo 1,75 desde un sprite local, sin recuadros de color.

## Colors

Azul institucional y blanco, con una escala secuencial de azules que codifica cumplimiento y una familia de estados semánticos siempre acompañados de forma.

### Primary
- **Azul marca SIGEA** (marca): riel lateral, banner huella, barra inferior móvil, texto principal, títulos de fila y página actual de la paginación. Es también el último grado (pleno) de la gradación.
- **Azul marca medio** (marca-2): hover sobre superficies de marca (enlaces del riel, botones dentro del banner) y avatar de marca.
- **Azul marca claro** (marca-3): contadores sobre el riel, divisor del pie del riel, barra de desplazamiento del riel.

### Secondary
- **Azul de acción** (accion, hover accion-2): solo el botón de la acción pendiente del usuario, los enlaces de texto, el anillo de foco, el punto de notificación nueva y el realce de celda de matriz al pasar el puntero.

### Tertiary: gradación CNA
- **Sin evidencia** (grad-0): fondo casi blanco con borde de renglón y texto secundario; pista vacía de las barras de meta.
- **No se cumple** (grad-1) y **Insatisfactorio** (grad-2): azules pálidos con texto azul marca. grad-1 también es el fondo de contadores, avatares y resaltado de búsqueda; grad-2 es el color de selección de texto y de las barras del pulso.
- **Aceptable** (grad-3) y **Alto grado** (grad-4): azules medios con texto blanco. grad-3 también tiñe los iconos de estado vacío, las barras de tiempos de revisión y los nodos de la línea de tiempo.
- **Pleno** (grad-5): el azul marca. Sobre el banner azul, la barra plena se pinta blanca para seguir siendo la más intensa.

### Estados
- **Aprobado** (ok / ok-fondo): verde bosque, borde sólido, icono de visto.
- **Pendiente** (pendiente / pendiente-fondo): el mismo azul de acción, borde punteado, icono de reloj; fondo de notificación nueva.
- **Envejecido / alerta** (alerta / alerta-fondo): ámbar, borde punteado, reloj de arena; franja de alerta bajo el banner y días de la cola de revisión.
- **Rechazado / error** (error / error-fondo): rojo, borde sólido y texto tachado; errores de campo, botón de peligro, punto de la campana, pulso de accesos denegados.
- **Sensible** (sensible / sensible-fondo): morado, con candado.

### Neutral
- **Blanco** (blanco): fondo de la aplicación, de las hojas, de los campos.
- **Papel** (papel): hover de filas y botones, cabecera de tablas, pie de diálogo, fondo del buscador y del acceso.
- **Renglón** (renglon): bordes de hoja y divisores de filas. **Renglón fuerte** (renglon-2): bordes de campo y de botón secundario, línea de tiempo.
- **Texto** (texto, igual a marca), **texto secundario** (texto-2) y **placeholder** (texto-3, 5,1:1 sobre blanco). Sobre marca: blanco y **texto inverso secundario** (texto-inverso-2).

### Named Rules
**The Una Escala Rule.** Los azules de grad-0 a grad-5 significan grado de cumplimiento CNA y nada más. No se introducen azules nuevos para decorar, agrupar o distinguir categorías.

**The Acción Reservada Rule.** El azul de acción rellena un solo botón por contexto: la acción pendiente del usuario (aprobar, subir, guardar). Las acciones restantes usan el botón secundario blanco o el de marca.

**The Forma Antes Que Color Rule.** Ningún estado se comunica solo con color: sólido, punteado, tachado, icono de reloj, reloj de arena o candado acompañan siempre al tono.

## Typography

**Display Font:** Public Sans (con system-ui, -apple-system, Segoe UI, sans-serif)
**Body Font:** Public Sans
**Label/Mono Font:** Public Sans, pesos 600 a 800 servidos localmente en woff2 (400, 600, 700, 800)

**Character:** Una sola familia de trabajo, de oficina pública, sobria y legible; la jerarquía sale del peso (800 en títulos, 700 en etiquetas) y del tamaño, nunca de una segunda familia. Todo el cuerpo usa cifras tabulares para que "4 / 20" se alinee en columna.

### Hierarchy
- **Display** (800, clamp(2.5rem, 5vw, 3.5rem), 1, -0.03em): solo la cifra grande del banner huella y el código de las páginas de error.
- **Headline** (800, 2rem, 1.2): el h1 de página.
- **Title** (800, 1.25rem, 1.2): h2, titular del banner (700, 1,3), total del pulso, marca del riel. El h3 baja a 1rem en 700.
- **Body** (400, 1rem, 1.5): texto corriente, campos de formulario. Cabeceras de página limitadas a 70ch.
- **Body small** (0.875rem): tablas, botones (700), enlaces del riel (600), etiquetas de campo (700), avisos (600).
- **Label** (700, 0.75rem): chips de factor, estados, metadatos, ayudas de campo, códigos de la huella. Las cabeceras de tabla y los títulos de grupo del riel usan esta etiqueta en mayúsculas con 0.04em de tracking.

### Named Rules
**The Seis Pasos Rule.** Solo existen 12, 14, 16, 20 y 32 px y el display fluido de 40 a 56 px. El display se reserva para una cifra por pantalla.

**The Cifra Tabular Rule.** Toda cifra se compone con tabular-nums (heredado del body); no se desactiva.

## Layout

Shell de dos zonas. En escritorio (desde 1024 px) un riel lateral fijo de 248 px (72 px en modo corto, solo iconos) y un área principal con barra superior fija de 4rem translúcida y contenido centrado hasta 1360 px con relleno de 32 px. Por debajo de 1024 px el riel desaparece: barra superior con la marca y una barra inferior azul de 64 px con navegación de iconos y etiqueta, más una hoja "Más" que sube desde abajo; el contenido reserva el alto de la barra inferior y la zona segura.

El ritmo es una escala de 4 px a 48 px (e-1 a e-7). Las páginas se apilan con 32 px entre bloques y las rejillas internas con 24 px. Desde 1100 px la rejilla principal es contenido flexible más una columna lateral de 380 px (cola de revisión, pulso), o dos mitades. Formularios en una columna que pasa a dos desde 768 px; filtros en auto-fit de mínimo 180 px.

Por debajo de 768 px las tablas se vuelven fichas apiladas con la etiqueta de cada dato a la izquierda, y la matriz factor × programa se vuelve lista por factor. Todo objetivo táctil mide al menos 44 px.

## Elevation & Depth

Sistema plano. La profundidad viene de renglones de 1 px, del cambio blanco a papel y del bloque azul marca del riel y el banner. Las hojas en reposo no tienen sombra. La sombra existe solo para lo que flota sobre la página.

### Shadow Vocabulary
- **Hoja flotante** (`box-shadow: 0 12px 32px -8px rgba(20, 42, 89, 0.28), 0 2px 6px rgba(20, 42, 89, 0.12)`): diálogos de confirmación, hoja "Más" móvil, resultados del buscador, enlace de salto.
- **Velo** (`rgba(20, 42, 89, 0.45)`): fondo detrás de diálogos y de la hoja móvil.

### Named Rules
**The Plano Por Defecto Rule.** Si no flota, no tiene sombra. Las hojas se separan con borde de renglón, no con elevación.

## Shapes

Esquinas contenidas: 8 px para contenedores, botones, campos, avisos, banner y diálogos; 4 px para chips, estados, celdas de matriz y la punta de las barras. Los círculos quedan para avatares, puntos de notificación y nodos de línea de tiempo; la píldora (999 px) solo para contadores y la pista de la barra de meta. Los bordes son de 1 px; los de estado y los punteados de pendiente de 1,5 px. El borde punteado es un dispositivo propio del mundo: significa pendiente o vacío (estado pendiente, envejecido, zona de carga de archivo, pozo de la huella, votos sin emitir) y no se usa como adorno.

## Components

### Buttons
Contenidos y firmes: altura táctil, peso 700 en texto pequeño.
- **Shape:** esquinas de 8 px, altura mínima 44 px, relleno horizontal de 16 px, icono y texto con 8 px de separación.
- **Primary:** relleno azul de acción con texto blanco; reservado a la acción pendiente.
- **Secondary (por defecto):** blanco con borde renglón fuerte y texto azul marca; hover a papel con borde azul marca.
- **Marca:** relleno azul marca, hover a marca medio, para acciones institucionales que no son la pendiente.
- **Peligro:** blanco con texto rojo; hover a fondo de error con borde rojo.
- **Fantasma / icono:** sin borde; el botón de icono es un cuadrado de 44 px.
- **Hover / Focus:** transición de fondo y borde de 200 ms con curva cubic-bezier(0.2, 0.8, 0.2, 1); foco con contorno de 2 px azul de acción separado 2 px. Ocupado: el texto se vuelve transparente y gira un anillo. Desactivado: opacidad 0,55.
- **Dentro del banner:** contorno blanco translúcido; el primario se invierte a blanco con texto marca.

### Chips (chip de factor)
La firma del sistema: "F3 · 4 / 20".
- **Style:** 28 px de alto, esquinas de 4 px, etiqueta de 12 px en 700 con la cifra en 600; fondo y texto según el grado (grad-0 con borde renglón; grad-1 y 2 con texto marca; grad-3 a 5 con texto blanco).
- **State:** siempre significa lo mismo en matriz, documentos, búsqueda y filtros; puede ser enlace al filtro del factor. Sin factor se muestra un estado neutro "Sin factor".

### Estados de documento
- Mismo módulo que el chip (28 px, 4 px, 12 px 700) con borde de 1,5 px del color del estado e icono pequeño delante: aprobado sólido con visto, pendiente punteado con reloj, envejecido punteado ámbar con reloj de arena y "más de 3 días", rechazado sólido con texto tachado, sensible morado con candado.

### Cards / Containers (hoja)
- **Corner Style:** 8 px.
- **Background:** blanco.
- **Shadow Strategy:** ninguna (ver Elevation & Depth).
- **Border:** 1 px renglón; cabeza y pie separados por renglón.
- **Internal Padding:** cabeza 16 × 24 px con h2 de 16 px en 700; cuerpo 24 px; pie 12 × 24 px en texto pequeño.

### Tablas y listas de filas
- Cabecera en papel con etiqueta mayúscula de 12 px; celdas de 12 × 16 px separadas por renglón; hover a papel; título de fila en azul marca 700 con secundario de 12 px debajo; cifras alineadas a la derecha. En móvil se vuelven fichas.
- Las listas de filas usan el mismo renglón, relleno de 12 × 24 px y metadatos de 12 px.

### Inputs / Fields
- **Style:** blanco, borde de 1 px renglón fuerte, esquinas de 8 px, 44 px de alto, texto de 16 px; etiqueta de 14 px en 700 azul marca encima, ayuda de 12 px debajo.
- **Focus:** contorno de 2 px azul de acción sin separación y borde del mismo azul. Hover: borde a texto secundario.
- **Error / Disabled:** borde rojo y mensaje de 12 px en 600 rojo con icono.
- **Opciones y carga:** las opciones radio son filas con borde que al marcarse toman borde marca doble y fondo papel; la carga de archivo es una zona punteada de 1,5 px sobre papel que pasa a grad-0 con borde marca.

### Navigation
- **Riel lateral:** fondo azul marca, enlaces de 44 px con icono y texto de 14 px en 600 color inverso secundario; hover a marca medio con texto blanco; página actual invertida a blanco con texto marca en 700; contador alineado a la derecha. Títulos de grupo en etiqueta mayúscula. Pie con usuario y avatar.
- **Barra superior:** blanca al 94 % con desenfoque, buscador de hasta 32rem sobre papel con icono a la izquierda y resultados en hoja flotante.
- **Móvil:** barra inferior azul marca con icono y etiqueta de 12 px; la página actual pasa a blanco y engrosa el trazo del icono a 2,25.
- **Pestañas de filtro:** texto de 14 px en 700, subrayado de 2 px azul marca para la actual, con contador en píldora grad-1.

### Banner huella (firma)
Bloque azul marca de esquinas de 8 px. A la izquierda el saludo, el titular (20 px) y la cifra display con su detalle ("6 / 205"), nota y acciones. A la derecha 12 columnas de 11rem (6rem en móvil): para directivas, una por factor F1 a F12 con altura igual al avance frente a meta y tono igual a su grado, sobre un pozo punteado blanco translúcido; para el docente, los 12 meses personales apilados por estado (aprobadas blancas sólidas, en revisión punteadas, rechazadas rayadas). Cada columna lleva código y "n/meta" debajo y una leyenda de grados. Las barras crecen desde la base en 300 ms escalonadas 40 ms; con movimiento reducido no se animan.

### Matriz factor × programa
Tabla con 3 px de separación entre celdas de 44 px de alto y 4 px de esquina, pintadas en la gradación con "n / meta"; al pasar el puntero, anillo de 2 px azul de acción; la fila de total lleva contorno marca. En móvil, lista por factor.

### Barra cantidad frente a meta y pulso
- **Meta:** pista de 8 px en píldora grad-0 con relleno en el color del grado y la cifra "n / meta" a la derecha.
- **Pulso de 30 días:** barras SVG en grad-2 con los picos en marca; la serie de accesos denegados usa fondo de error y picos en rojo. Total en 20 px 800.

### Iconos
Sprite local de Lucide, trazo 1,75, extremos redondeados, 1,25em (1em en la variante pequeña), siempre en currentColor y sin recuadro de color de fondo.

## Do's and Don'ts

### Do:
- **Do** expresar todo avance como cantidad frente a meta ("4 / 20") y pintarlo con el grado que le corresponde (grad-0 a grad-5).
- **Do** usar el chip de factor del sistema cada vez que aparezca un factor CNA, en cualquier pantalla.
- **Do** acompañar cada estado con su forma: sólido, punteado, tachado, reloj, reloj de arena o candado.
- **Do** separar contenedores con renglón de 1 px (renglon) y esquinas de 8 px; reservar la sombra de hoja flotante a diálogos, menús y hojas móviles.
- **Do** mantener todo objetivo táctil en 44 px o más y el foco visible en 2 px azul de acción (blanco sobre superficies de marca).
- **Do** usar solo los tamaños de la escala (12, 14, 16, 20, 32 px y el display fluido) y los pesos 400, 600, 700 y 800 de Public Sans.

### Don't:
- **Don't** usar los azules de la gradación para decorar o para categorías que no sean grado de cumplimiento.
- **Don't** rellenar con azul de acción más de un botón por contexto ni usarlo para acciones que no son la pendiente del usuario.
- **Don't** construir paneles de tarjetas KPI con icono en recuadro de color, ilustraciones isométricas ni colores sueltos fuera de los tokens.
- **Don't** comunicar un estado solo con color.
- **Don't** añadir una segunda familia tipográfica ni fuentes remotas; Public Sans se sirve localmente.
- **Don't** mostrar la identidad visual de la universidad: la marca es solo SIGEA.
