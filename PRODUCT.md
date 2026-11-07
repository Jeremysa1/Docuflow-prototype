# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Decana** (una por facultad): supervisa todos los programas, habilita usuarios, aprueba
  evidencias y consulta la auditoría. Necesita saber de un vistazo cuánto falta para la
  acreditación y qué está atascado.
- **Coordinadora** (una para toda la facultad): revisa y aprueba lo que suben los docentes de
  cualquier programa y vota accesos a documentos sensibles.
- **Docentes de planta**: suben evidencias con sus metadatos, publican versiones nuevas y piden
  acceso a documentos ajenos.

Se usa tanto en computador como en celular, en proporción similar: los docentes suben y consultan
desde el móvil; las directivas revisan desde ambos.

## Product Purpose

SIGEA (Sistema Integrado de Gestión de Evidencias para la Acreditación) centraliza, protege y
audita las evidencias documentales de una facultad para la acreditación de alta calidad ante el
CNA. Tiene éxito cuando cada factor CNA tiene sus evidencias aprobadas a tiempo y se puede
demostrar quién hizo qué con cada documento.

## Positioning

No es un gestor de archivos genérico: organiza todo alrededor de los 12 factores CNA, con
aprobación por roles, acceso Zero-Trust (los documentos sensibles necesitan 2 votos) y una
auditoría que sirve como evidencia del propio proceso.

## Operating Context

- Flujo: el docente sube → la Coordinadora revisa (aprueba o rechaza con motivo) → la Decana
  supervisa; las versiones nuevas de un docente vuelven a revisión.
- Documentos sensibles: solicitud de acceso con motivo y votación de autor, Coordinadora y Decana.
- Métricas que se usan para decidir: avance CNA por factor frente a la meta, tiempos de revisión
  (pendientes envejecidos, cuellos de botella) y actividad y seguridad (accesos, descargas,
  accesos denegados, solicitudes).
- Exportaciones a Excel y PDF para reportes de acreditación.

## Capabilities and Constraints

- Django 6.1 con plantillas del servidor, CSS propio y JavaScript sin framework; admin con
  django-unfold.
- Interfaz en español de Colombia (`es-co`), zona horaria `America/Bogota`.
- Formatos admitidos: PDF, DOCX, XLSX, PPTX (máx. 10 MB). La vista previa en página es solo
  para PDF.
- Terminología: factores CNA (F1–F12), evidencia, programa académico, versión, solicitud de
  acceso, documento sensible.
- Gobernado por `.specify/memory/constitution.md` (Zero-Trust, auditoría inmutable, capa de
  servicios, pruebas).

## Brand Commitments

- La marca es **SIGEA**, como producto independiente: sin identidad visible de la universidad.
- Restricción visual confirmada por el usuario: **mantener el azul institucional y el blanco**
  como colores de la marca. El azul actual es `#142a59`.
- Logo actual: `gestion_documental/static/img/sigea_logo_p2.png` (una "S").

## Evidence on Hand

- Datos reales de desarrollo: 7 documentos, 8 usuarios, 12 factores CNA con metas definidas en
  `ReporteService.obtener_estadisticas_cna`.
- No hay testimonios, fotografías propias ni métricas de uso históricas; no deben inventarse.

## Product Principles

1. **La acreditación es la brújula.** Cada pantalla responde a "¿cuánto falta y qué está
   atascado?" antes que a la decoración.
2. **La confianza se ve.** El estado, la sensibilidad y la trazabilidad de un documento tienen
   que ser evidentes, nunca ocultos.
3. **Cada rol ve su trabajo primero.** La Decana ve el avance global, la Coordinadora su cola y el
   docente sus evidencias.
4. **El color significa algo.** Un color de estado siempre quiere decir lo mismo en todo el
   sistema.

## Accessibility & Inclusion

Uso móvil frecuente: áreas táctiles amplias, texto legible sin zoom y contraste WCAG 2.1 AA.
