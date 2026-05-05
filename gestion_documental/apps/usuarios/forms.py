"""
Formularios del módulo de usuarios.
"""
from django import forms


class LoginForm(forms.Form):
    """Formulario de inicio de sesión por email."""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'usuario@campusucc.edu.co',
            'autofocus': True,
            'id': 'login-email',
        }),
        label='Correo electrónico'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': '••••••••',
            'id': 'login-password',
        }),
        label='Contraseña'
    )


class RecuperarContrasenaForm(forms.Form):
    """Formulario para solicitar recuperación de contraseña."""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input form-input-underline',
            'placeholder': 'usuario@campusucc.edu.co',
            'id': 'recovery-email',
        }),
        label='Correo institucional'
    )


class TokenForm(forms.Form):
    """Formulario para validar token de 6 dígitos."""

    token = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.HiddenInput(attrs={'id': 'token-hidden'}),
        label='Token'
    )


class CambiarContrasenaForm(forms.Form):
    """Formulario para cambiar contraseña."""

    nueva_contrasena = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nueva contraseña',
            'id': 'new-password',
        }),
        label='Nueva contraseña'
    )
    confirmar_contrasena = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirme nueva contraseña',
            'id': 'confirm-password',
        }),
        label='Confirme nueva contraseña'
    )
