"""
Backend de autenticación con bloqueo por intentos fallidos (R3-03).

El lockout de UsuarioService solo cubría el login frontal; /admin/login/
usaba ModelBackend sin límite. Este backend reutiliza los mismos campos
(intentos_fallidos/bloqueado_hasta) para que ambos portales compartan
la protección. El login frontal sigue usando check_password directo,
así que no hay doble conteo.
"""
from datetime import timedelta

from django.contrib.auth.backends import ModelBackend
from django.utils import timezone


class BloqueoAdminBackend(ModelBackend):
    """ModelBackend + bloqueo 3 intentos / 15 min (igual que el frontal)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        # pyrefly: ignore [missing-import]
        from apps.usuarios.models import Usuario

        if not username or not password:
            return None
        try:
            user = Usuario.objects.get(username=username)
        except Usuario.DoesNotExist:
            return None

        if user.bloqueado_hasta and user.bloqueado_hasta > timezone.now():
            return None

        if user.check_password(password):
            return user if self.user_can_authenticate(user) else None

        user.intentos_fallidos += 1
        if user.intentos_fallidos >= 3:
            user.bloqueado_hasta = timezone.now() + timedelta(minutes=15)
            user.intentos_fallidos = 0
        user.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])
        return None
