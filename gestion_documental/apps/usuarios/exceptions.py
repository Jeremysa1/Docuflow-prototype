"""
Excepciones personalizadas del módulo de usuarios.
"""


class AuthError(Exception):
    """Excepción de autenticación con código y mensaje."""

    def __init__(self, codigo, mensaje):
        self.codigo = codigo
        self.mensaje = mensaje
        super().__init__(mensaje)
