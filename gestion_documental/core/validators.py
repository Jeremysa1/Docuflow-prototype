"""Validadores de contraseña propios (M4: una sola política en todo SIGEA)."""
import re

from django.core.exceptions import ValidationError

SIMBOLOS = '!@#$%^&*'


class ComplejidadValidator:
    """Exige al menos una mayúscula y un carácter especial.

    Se suma a los validadores de Django en AUTH_PASSWORD_VALIDATORS, así que
    registro, recuperación e invitación aplican exactamente las mismas reglas.
    """

    def validate(self, password, user=None):
        errores = []
        if not re.search(r'[A-ZÁÉÍÓÚÑ]', password or ''):
            errores.append(ValidationError('La contraseña debe incluir al menos una letra mayúscula.',
                                           code='sin_mayuscula'))
        if not any(c in SIMBOLOS for c in password or ''):
            errores.append(ValidationError(f'La contraseña debe incluir al menos un símbolo ({SIMBOLOS}).',
                                           code='sin_simbolo'))
        if errores:
            raise ValidationError(errores)

    def get_help_text(self):
        return f'Tu contraseña debe incluir una mayúscula y un símbolo ({SIMBOLOS}).'
