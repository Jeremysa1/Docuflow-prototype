"""
Middlewares propios de SIGEA.
"""
from django.contrib import messages
from django.contrib.auth import SESSION_KEY, logout
from django.shortcuts import redirect

MENSAJE_CUENTA_SIN_ACCESO = 'Tu sesión se cerró porque tu cuenta ya no tiene acceso. Escríbele a la Decanatura.'


class CuentaHabilitadaMiddleware:
    """A2: cierra la sesión de cuentas deshabilitadas o inactivas en su siguiente petición.

    `esta_habilitado` solo se comprobaba al iniciar sesión; con la sesión
    deslizante de 15 min, una cuenta deshabilitada seguía dentro mientras
    siguiera activa. Los superusuarios quedan exentos: `createsuperuser` crea
    cuentas con esta_habilitado=False y no deben quedar fuera del admin. La
    única superusuaria de negocio (Decana) no se puede deshabilitar.

    Va después de AuthenticationMiddleware y MessageMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user is None:
            return self.get_response(request)

        if user.is_authenticated:
            if not user.is_superuser and (not user.is_active or not getattr(user, 'esta_habilitado', True)):
                return self._expulsar(request)
        elif SESSION_KEY in request.session:
            # Cuenta inactiva: el backend ya la trata como anónima, pero la sesión
            # seguía guardada con su id. Se elimina para no dejar sesiones huérfanas.
            return self._expulsar(request)
        return self.get_response(request)

    @staticmethod
    def _expulsar(request):
        logout(request)
        messages.error(request, MENSAJE_CUENTA_SIN_ACCESO)
        return redirect('auth:login')


from django.middleware.csp import ContentSecurityPolicyMiddleware  # noqa: E402


class CSPSinAdminMiddleware(ContentSecurityPolicyMiddleware):
    """CSP de Django en toda la app salvo /admin/, cuyo tema (Unfold) usa scripts en línea."""

    def process_response(self, request, response):
        if request.path.startswith('/admin/'):
            return response
        return super().process_response(request, response)
