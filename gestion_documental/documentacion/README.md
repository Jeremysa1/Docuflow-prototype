# 🚀 SIGEA v2.0 - Gestión Documental Universitaria

SIGEA es una plataforma integral de gestión documental de alto rendimiento, diseñada específicamente para entornos universitarios. El sistema centraliza, asegura y audita la documentación institucional con un enfoque riguroso en la **Acreditación de Calidad (Factores CNA)** y un modelo de seguridad **Zero-Trust**.

## 🗂️ Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Manual técnico | `gestion_documental/documentacion/manual_tecnico.md` |
| Especificaciones por funcionalidad (spec-kit) | `specs/` (raíz del repositorio) |
| Principios del proyecto | `.specify/memory/constitution.md` |
| Revisiones de seguridad | `gestion_documental/informes/` |
| Sistema de diseño | `DESIGN.md` y `PRODUCT.md` (raíz) |
| Referencias externas | `gestion_documental/documentacion/referencias/` |
| Scripts de QA manual | `gestion_documental/scripts/qa/` |

---

---

## 💎 Visión General y Estética
SIGEA v2.0 no es solo una herramienta administrativa; es una experiencia de usuario **Premium**. El sistema ha sido refinado para ofrecer una interfaz limpia, moderna y altamente funcional que emula la eficiencia de las mejores suites de productividad del mercado.

- **Diseño Moderno**: Paleta de colores institucional (`#142a59`) con acentos esmeralda y una estética de "90% zoom" para máxima densidad de información sin sacrificar legibilidad.
- **Iconografía**: un solo juego de iconos de línea (Lucide, servidos localmente) y estados que se distinguen por forma y color.
- **UX Fluida**: Micro-animaciones, estados activos persistentes en la navegación y transiciones suaves que mejoran la retención del usuario.

---

## 🛠️ Stack Tecnológico
- **Core**: Django 6.1 (Python 3.12)
- **Base de Datos**: PostgreSQL (Optimizado para auditoría masiva).
- **Frontend**: plantillas Django, sistema de diseño propio en `static/css/sigea/` (ver `DESIGN.md`), JavaScript sin framework.
- **Seguridad**: límites de intentos por IP, una sola política de contraseñas, CSP, sesiones de 15 min y usuario de base de datos con permisos mínimos.
- **Almacenamiento**: Gestión segura de archivos (`media/`) con validación de acceso a nivel de aplicación.

---

## 📂 Estructura del Ecosistema
El proyecto se organiza bajo una arquitectura de micro-servicios internos (Django Apps) que garantizan la escalabilidad:

```text
gestion_documental/
├── apps/
│   ├── auditoria/      # Logs inmutables y trazabilidad total (IP, Usuario, Acción).
│   ├── documentos/     # Core: Subida, búsqueda avanzada y visualización.
│   ├── notificaciones/ # Alertas de sistema y flujo de aprobación.
│   ├── permisos/       # Gestión de solicitudes de acceso y control de roles.
│   ├── usuarios/       # Administración de perfiles, roles y seguridad.
│   └── versiones/      # Control de versiones (Versioning) y rollback.
├── core/               # Lógica transversal (Decoradores, Servicios, Utils).
├── config/             # Configuración del servidor y ruteo global.
├── static/             # Assets: CSS Moderno, JS Dinámico e Imágenes.
└── templates/          # Componentes UI reutilizables y layouts base.
```

---

## 🚀 Funcionalidades Principales

### 1. Centro de Control (Dashboard)
Visualización rápida de métricas clave: documentos pendientes, mis archivos recientes y alertas de seguridad.

### 2. Gestión Documental Avanzada
- **Clasificación CNA**: Organización automática por los 12 factores de acreditación.
- **Búsqueda Ultra-Rápida**: Filtros combinados por factor, programa, autor, vigencia y estado.
- **Timeline de Versiones**: Cada documento mantiene un historial completo; nunca se pierde la trazabilidad de los cambios.

### 3. Seguridad Zero-Trust
- **Acceso Bajo Demanda**: Los documentos confidenciales requieren una solicitud formal que debe ser aprobada por un Coordinador o Decana.
- **Descarga Protegida**: El enlace real del archivo nunca se expone; el sistema sirve el contenido tras validar los permisos en tiempo real.

### 4. Auditoría de Grado Empresarial
Módulo especializado que registra cada interacción con el sistema:
- ¿Quién subió el archivo?
- ¿Desde qué IP?
- ¿Quién intentó descargarlo sin permiso?
- Historial de aprobaciones y motivos de rechazo.

---

## ⚙️ Instalación y Configuración

Siga estos pasos para desplegar el entorno de desarrollo:

1. **Clonar el repositorio y entrar al directorio**:
   ```bash
   cd SIGEA2/gestion_documental
   ```

2. **Crear y activar un entorno virtual**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**:
   Copie el archivo `.env.example` a `.env` y complete las credenciales de base de datos y la `SECRET_KEY`.

5. **Ejecutar migraciones y servidor**:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

---

## 👥 Roles y Permisos
- **Decana**: Supervisión global de todos los programas y documentos.
- **Coordinador**: Administra el flujo de su programa académico y aprueba documentos.
- **Docente**: Autor de documentos; puede subir, editar versiones y solicitar acceso a otros archivos.

---

## ✅ Estado Actual: Totalmente Funcional
El sistema ha superado las pruebas de estrés y validación de seguridad.
- **Backend**: 100% Operativo.
- **Frontend**: Diseño finalizado y consistente.
- **Base de Datos**: Estructura de auditoría y versiones lista para producción.

---

*Desarrollado y documentado con excelencia para el ecosistema universitario.*
*Actualizado: Mayo 2026.*

