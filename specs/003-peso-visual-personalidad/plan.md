# Implementation Plan: Peso visual, iconografía y portada de acceso

**Branch**: `003-peso-visual-personalidad` | **Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

## Summary

Reforzar el sistema de diseño de la spec 002 sin cambiar su dirección: tokens de borde y renglón más firmes, fondo papel en el contenido, cabeceras de tabla de marca, barras gruesas con porcentaje, iconos de página y de hoja, un componente de tipo de archivo, una portada de acceso reestructurada y correcciones de alineación (campos, logo del riel, foco de botones).

## Technical Context

**Language/Version**: Python 3.12, Django 6.1.3 (plantillas del servidor), CSS propio en capas (`static/css/sigea/`).
**Storage**: PostgreSQL, sin cambios de modelo.
**Testing**: `manage.py test tests` (86 pruebas) más `test_reglas_diseno`; capturas con Chrome sin ventana.
**Constraints**: sin estilos en línea salvo variables CSS; hex solo en `tokens.css`; texto mínimo 12 px; Zero-Trust por rol.

## Constitution Check

- Seguridad Zero-Trust: el componente de tipo de archivo solo lee la extensión; no expone datos nuevos. ✅
- Accesibilidad AA: colores de tipo de archivo con texto blanco ≥ 4,5:1; foco visible conservado. ✅
- Simplicidad: un template tag nuevo (`tipo_archivo`), un recorte del logo; sin dependencias. ✅

## Design

1. **Tokens** (`tokens.css`): `--sg-borde: 1.5px`, renglones más oscuros, `--sg-sombra-hoja-suave`, colores `--sg-tipo-pdf|word|excel|ppt`.
2. **Componentes** (`componentes.css`): hoja con borde firme y sombra suave; cabecera de hoja con fondo papel e icono; tabla con cabecera de marca y filas alternas; botones con borde 1,5 px y estado presionado; foco que respeta el radio; `.sg-campo { align-content: start }`; `.sg-titulo-icono`; `.sg-tipo`.
3. **Gráficos** (`graficos.css`): pista de 12 px con porcentaje; pozos de la huella con borde más firme.
4. **Shell** (`shell.css`): fondo papel; logo como máscara del emblema recortado (`img/sigea_emblema.png`) alineado a la columna de iconos.
5. **Plantillas**: icono de título en las 15 cabeceras de página; icono en cabeceras de hoja; `{% tipo_archivo doc %}` en listas y detalle; portada de acceso nueva en `_acceso.html`.
6. **Formularios**: etiquetas vacías en español en `DocumentoForm` y `DocumentoEditForm`.

## Project Structure

Sin carpetas nuevas. Archivos tocados: `static/css/sigea/*.css`, `static/img/sigea_emblema.png`, `core/templatetags/sigea.py`, `templates/componentes/tipo_archivo.html`, `templates/base.html`, `apps/*/templates/**`, `apps/documentos/forms.py`.
