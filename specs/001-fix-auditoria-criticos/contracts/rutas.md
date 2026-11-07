# Contrato de rutas afectadas

| Ruta | Método | Quién | Respuesta esperada | Cambio |
|------|--------|-------|--------------------|--------|
| `/documentos/aprobar/` | GET | DECANA, COORDINADOR | 200 con `docs_urgentes_count`; DOCENTE → 403 | C1 |
| `/documentos/busqueda/?q=` | GET | autenticado | 200; títulos renderizados como texto | C2 |
| `/documentos/<id>/vista-previa/` | GET | con acceso | PDF: 200 `application/pdf`, `Content-Disposition: inline`, `X-Content-Type-Options: nosniff`; no PDF: 404; sin acceso: 403 + auditoría `ACCESO_DENEGADO` | **nueva** (A4) |
| `/documentos/<id>/descargar/` | GET | con acceso | adjunto del archivo vigente; sin acceso: redirección con mensaje genérico + `ACCESO_DENEGADO` | A1, A6 |
| `/documentos/<id>/` | GET | autenticado | vista bloqueada si no hay acceso + `ACCESO_DENEGADO` | A6 |
| `/media/...` | GET | cualquiera | 404 también en DEBUG | A4 |
| `/versiones/<id>/crear/` | POST | autor, directivas | versión nueva vigente + `NUEVA_VERSION` | A1 |
| `/login/` | POST | anónimo | igual que hoy; audita `LOGIN` / `LOGIN_FALLIDO` | A6 |
| cualquier ruta | * | usuario deshabilitado o inactivo | sesión cerrada, redirección a `/login/` | A2 |

## Configuración

| Variable de entorno | Por defecto | Efecto |
|---------------------|-------------|--------|
| `TRUSTED_PROXY_COUNT` | `0` | Número de proxies delante de Django cuyo `X-Forwarded-For` se acepta. |
