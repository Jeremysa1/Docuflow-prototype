# Contrato: tokens del sistema de diseño (`static/css/sigea/tokens.css`)

Únicos valores permitidos en el CSS nuevo. Contraste verificado contra blanco o contra el azul de
marca, según el uso.

## Color

| Token | Valor | Uso |
|-------|-------|-----|
| `--sg-marca` | `#142a59` | Riel, banner, títulos |
| `--sg-marca-2` | `#1c3a78` | Hover del riel, superficies del banner |
| `--sg-blanco` | `#ffffff` | Fondo |
| `--sg-papel` | `#f5f7fb` | Fondo de áreas secundarias |
| `--sg-renglon` | `#dfe4ee` | Bordes y divisiones |
| `--sg-texto` | `#142a59` | Texto principal |
| `--sg-texto-2` | `#4d5871` | Texto secundario (7:1 sobre blanco) |
| `--sg-accion` | `#1f4fd1` | Reservado: acción principal pendiente y foco |
| `--sg-ok` | `#1f6f4a` | Aprobado (con forma sólida) |
| `--sg-pendiente` | `#1f4fd1` | Pendiente (borde punteado) |
| `--sg-alerta` | `#9a5b00` | Envejecido (>3 días, con reloj) |
| `--sg-error` | `#b3261e` | Rechazado (tachado), acceso denegado |
| `--sg-sensible` | `#5b2a86` | Documento sensible (con candado) |

## Gradación CNA (escala única)

| Token | Nivel | Valor | Texto encima |
|-------|-------|-------|--------------|
| `--sg-grad-0` | Sin evidencia | `#eef1f6` | `--sg-texto-2` |
| `--sg-grad-1` | No se cumple | `#d6e0f3` | `--sg-texto` |
| `--sg-grad-2` | Insatisfactorio | `#a9bde6` | `--sg-texto` |
| `--sg-grad-3` | Aceptable | `#4a6cc0` | blanco (5,0:1) |
| `--sg-grad-4` | Alto grado | `#2f56b0` | blanco |
| `--sg-grad-5` | Pleno | `#142a59` | blanco |

Sobre el banner azul, los niveles 4 y 5 tienen poco contraste con el fondo (2,05:1 y 1:1). Por eso
cada columna de la huella lleva un borde de 1 px `rgba(255,255,255,.55)` y la etiqueta "n / meta"
en blanco: el valor se lee por la altura y la cifra, nunca solo por el tono. Contraste verificado:
todos los pares texto/fondo de la tabla son ≥ 4,5:1.

## Tipografía

`--sg-fuente: "Public Sans", system-ui, sans-serif`

| Token | Valor |
|-------|-------|
| `--sg-t-1` | 0.75rem (12 px) |
| `--sg-t-2` | 0.875rem (14 px) |
| `--sg-t-3` | 1rem (16 px) |
| `--sg-t-4` | 1.25rem (20 px) |
| `--sg-t-5` | 2rem (32 px) |
| `--sg-t-6` | clamp(2.5rem, 5vw, 3.5rem), solo para la cifra del banner |

Pesos: 400, 600, 700, 800.

## Espacio, forma y movimiento

| Grupo | Tokens |
|-------|--------|
| Espacio | `--sg-e-1` 4 px · `--sg-e-2` 8 px · `--sg-e-3` 12 px · `--sg-e-4` 16 px · `--sg-e-5` 24 px · `--sg-e-6` 32 px · `--sg-e-7` 48 px |
| Radio | `--sg-r-1` 4 px (chips, celdas) · `--sg-r-2` 8 px (paneles, botones) |
| Sombra | solo `--sg-sombra-hoja` para hojas y modales |
| Movimiento | `--sg-dur` 200 ms · `--sg-dur-larga` 300 ms · `--sg-curva` cubic-bezier(.2,.8,.2,1) |

Con movimiento reducido, todas las duraciones valen 0.
