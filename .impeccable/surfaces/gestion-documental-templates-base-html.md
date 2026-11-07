---
version: 1
slug: "gestion-documental-templates-base-html"
primary_target: "gestion_documental/templates/base.html"
related_targets: []
---

# Surface brief: aplicación SIGEA (todas las pantallas autenticadas y el login)

## Scope and mode
Operate. Toda la aplicación web Django: shell (base.html), panel por rol, evidencias, búsqueda,
detalle, aprobación, accesos, auditoría, usuarios, notificaciones, login. Admin Unfold alineado en
color. Uso 50 % escritorio y 50 % móvil.

## Audience, task, constraints
Decana (avance global, supervisión), Coordinadora (cola de revisión, votos), docentes (subir,
versionar, solicitar acceso). Mantener azul #142a59 y blanco. Marca solo SIGEA. Métricas:
avance CNA por factor, tiempos de revisión, actividad y seguridad. No inventar datos.

## Direction contract
THESIS: SIGEA se lee como la matriz del informe de autoevaluación CNA: cada número es "cantidad
frente a meta" y la gradación de cumplimiento (sin evidencia → insatisfactorio → aceptable → alto
grado → pleno) es la única escala de azules del sistema. Rechaza el panel SaaS de tarjetas KPI con
icono en recuadro, ilustración isométrica y colores sueltos.

OWN-WORLD: blanco y azul. Riel lateral azul #142a59 con texto blanco; fondo blanco; renglones
#dfe4ee. Escala secuencial de 5 azules para la gradación, usada igual en celdas, badges de factor y
barras. Un azul de acción (#1f4fd1) reservado a la acción pendiente del usuario. Estados por forma
además de color: aprobado sólido, pendiente con borde punteado, rechazado tachado en rojo #b3261e,
envejecido (>3 días) en ámbar #9a5b00. Una sola familia de trabajo (Public Sans), cifras tabulares,
escala de 5 pasos, base 16 px. Iconos Lucide de trazo 1,75 sin recuadros de color.

STORY: la directiva entiende en segundos qué factores están lejos de su meta y qué está atascado;
la Coordinadora vacía su cola de la más antigua a la más nueva; el docente ve dónde aporta su
evidencia. Todos confían porque el estado y la trazabilidad se ven siempre.

FIRST VIEWPORT (panel de la Decana, 1440×900): riel lateral azul a la izquierda con SIGEA y
navegación. Encabezado "Matriz de autoevaluación" con avance global como 6 / 205 y pendientes con
su antigüedad. Centro: matriz factor (F1–F12) × programa con celdas en la gradación y "n / meta".
Derecha: cola de revisión ordenada por antigüedad y pulso de actividad de 30 días (descargas,
accesos denegados). En móvil, la matriz se vuelve lista por factor con barra en la gradación.

FORM: Matriz de autoevaluación (candidato 1 de mi lista; elegido por el usuario como
IMPECCABLE'S PICK). seed:80c80ae500d0eb65. Disciplinas sumadas: escala tipográfica de 5 pasos,
cantidad frente a meta siempre, un color reservado para la acción pendiente, estado por forma.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Signature move
La celda de gradación: el mismo chip "F3 · 4 / 20" en la escala de azules aparece en la matriz, en
cada documento, en la búsqueda y en los filtros, y siempre significa lo mismo.

## Unresolved
Metas por programa: hoy solo existen metas por factor a nivel facultad; la matriz por programa
usará la meta de facultad hasta que se definan metas por programa.
