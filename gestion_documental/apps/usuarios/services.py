"""
Servicios del módulo de usuarios.

Contiene toda la lógica de negocio relacionada con autenticación,
recuperación de contraseña y gestión de usuarios.
"""
import random
import re
from datetime import timedelta

from django.contrib.auth import login, logout
from django.core.mail import send_mail
from django.utils import timezone

from .models import Usuario, ProgramaAcademico
from .exceptions import AuthError


class UsuarioService:
    """Servicio para la gestión de usuarios."""

    # ─── AUTENTICACIÓN ───────────────────────────────────────────

    @staticmethod
    def autenticar_usuario(request, email, password):
        """
        Autentica un usuario por EMAIL (no username).

        Lógica:
        1. Buscar por email → si no existe: AuthError 401
        2. Contraseña incorrecta → incrementar intentos, bloquear si >= 3
        3. Validar is_active, esta_habilitado, bloqueado_hasta
        4. Si todo OK → login + resetear intentos
        """
        # 1. Buscar usuario por email
        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            raise AuthError(
                codigo=401,
                mensaje="No pudimos verificar tu identidad"
            )

        # 2. Verificar contraseña
        if not user.check_password(password):
            user.intentos_fallidos += 1
            if user.intentos_fallidos >= 3:
                user.bloqueado_hasta = timezone.now() + timedelta(minutes=15)
                user.intentos_fallidos = 0
                user.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])
                raise AuthError(
                    codigo=401,
                    mensaje="No pudimos verificar tu identidad"
                )
            user.save(update_fields=['intentos_fallidos'])
            raise AuthError(
                codigo=401,
                mensaje="No pudimos verificar tu identidad"
            )

        # 3. Verificar estado de la cuenta
        if not user.is_active:
            raise AuthError(
                codigo=403,
                mensaje="Lo identificamos, pero no tiene acceso"
            )

        if not user.esta_habilitado:
            raise AuthError(
                codigo=403,
                mensaje="Lo identificamos, pero no tiene acceso"
            )

        if user.bloqueado_hasta and user.bloqueado_hasta > timezone.now():
            minutos_restantes = int(
                (user.bloqueado_hasta - timezone.now()).total_seconds() / 60
            ) + 1
            raise AuthError(
                codigo=403,
                mensaje=f"Cuenta bloqueada temporalmente. Intente en {minutos_restantes} minutos"
            )

        # 4. Login exitoso
        login(request, user)
        user.intentos_fallidos = 0
        user.bloqueado_hasta = None
        user.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])
        return user

    @staticmethod
    def cerrar_sesion(request):
        """Cierra la sesión del usuario actual."""
        logout(request)

    # ─── RECUPERACIÓN DE CONTRASEÑA ──────────────────────────────

    @staticmethod
    def solicitar_recuperacion(email):
        """
        Genera y envía un token de recuperación de 6 dígitos.
        Siempre retorna True (no revela si el email existe).
        """
        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return True  # No revelar por seguridad

        # Generar token de 6 dígitos
        token = str(random.randint(100000, 999999))

        # Guardar token con expiración de 3 minutos
        user.token_recuperacion = token
        user.token_expiracion = timezone.now() + timedelta(minutes=3)
        user.token_intentos = 0
        user.save(update_fields=[
            'token_recuperacion', 'token_expiracion', 'token_intentos'
        ])

        # Enviar email (console backend en desarrollo)
        send_mail(
            subject='Recuperación de contraseña - Docuflow',
            message=(
                f'Tu código de verificación es: {token}.\n'
                f'Válido por 3 minutos. Máximo 3 intentos.'
            ),
            from_email='noreply@docuflow.edu.co',
            recipient_list=[email],
            fail_silently=False,
        )

        return True

    @staticmethod
    def confirmar_email_recuperacion(email):
        """
        Retorna el email enmascarado para confirmación.
        Ejemplo: "ye***@gmail.com"
        Si no existe → retorna None.
        """
        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return None

        parts = user.email.split('@')
        if len(parts) == 2:
            local = parts[0]
            domain = parts[1]
            if len(local) > 2:
                masked = local[:2] + '***'
            else:
                masked = local[0] + '***'
            return f"{masked}@{domain}"
        return None

    @staticmethod
    def validar_token(email, token):
        """
        Valida el token de recuperación.
        Retorna dict: {'valido': bool, 'error': str|None, 'intentos_restantes': int}
        """
        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return {'valido': False, 'error': 'Token inválido', 'intentos_restantes': 0}

        # Verificar expiración
        if not user.token_expiracion or user.token_expiracion < timezone.now():
            return {'valido': False, 'error': 'Token expirado', 'intentos_restantes': 0}

        # Verificar intentos
        if user.token_intentos >= 3:
            return {
                'valido': False,
                'error': 'Máximo de intentos alcanzado',
                'intentos_restantes': 0
            }

        # Verificar token
        if token != user.token_recuperacion:
            user.token_intentos += 1
            user.save(update_fields=['token_intentos'])
            restantes = 3 - user.token_intentos
            return {
                'valido': False,
                'error': f'Token incorrecto. Te quedan {restantes} intentos',
                'intentos_restantes': restantes
            }

        # Token válido - NO limpiar aún
        return {'valido': True, 'error': None, 'intentos_restantes': 3 - user.token_intentos}

    @staticmethod
    def cambiar_contrasena(email, nueva_contrasena):
        """
        Cambia la contraseña validando políticas de seguridad.
        Retorna dict: {'exito': bool, 'error': str|None}
        """
        # Validar políticas
        if len(nueva_contrasena) < 8:
            return {'exito': False, 'error': 'La contraseña debe tener mínimo 8 caracteres'}

        if not re.search(r'[A-Z]', nueva_contrasena):
            return {'exito': False, 'error': 'La contraseña debe incluir al menos una letra mayúscula'}

        if not re.search(r'[!@#$%^&*]', nueva_contrasena):
            return {
                'exito': False,
                'error': 'La contraseña debe incluir al menos un carácter especial (!@#$%^&*)'
            }

        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return {'exito': False, 'error': 'Usuario no encontrado'}

        # Cambiar contraseña
        user.set_password(nueva_contrasena)

        # Limpiar tokens
        user.token_recuperacion = None
        user.token_expiracion = None
        user.token_intentos = 0
        user.save(update_fields=[
            'password', 'token_recuperacion', 'token_expiracion', 'token_intentos'
        ])

        return {'exito': True, 'error': None}

    # ─── CONSULTAS ───────────────────────────────────────────────

    @staticmethod
    def obtener_usuario_por_id(usuario_id):
        """Obtiene un usuario por su ID."""
        try:
            return Usuario.objects.get(pk=usuario_id)
        except Usuario.DoesNotExist:
            return None

    @staticmethod
    def listar_usuarios(rol=None, programa=None, habilitado=None):
        """Lista usuarios con filtros opcionales."""
        queryset = Usuario.objects.all().order_by('-date_joined')
        if rol:
            queryset = queryset.filter(rol=rol)
        if programa:
            queryset = queryset.filter(programa_academico_id=programa)
        if habilitado is not None:
            queryset = queryset.filter(esta_habilitado=habilitado)
        return queryset

    @staticmethod
    def crear_usuario(nombre, apellido, email, rol, programa_id=None):
        if Usuario.objects.filter(email=email).exists():
            raise Exception("El correo electrónico ya está registrado.")
        
        username = email.split('@')[0]
        # Handle duplicates in username just in case
        base_username = username
        counter = 1
        while Usuario.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        esta_habilitado = True if rol in ('COORDINADOR', 'DECANA') else False

        user = Usuario(
            first_name=nombre,
            last_name=apellido,
            email=email,
            username=username,
            rol=rol,
            programa_academico_id=programa_id,
            esta_habilitado=esta_habilitado
        )
        user.set_unusable_password()
        user.save()
        return user

    @staticmethod
    def habilitar_usuario(usuario_id):
        user = Usuario.objects.get(pk=usuario_id)
        user.esta_habilitado = True
        user.save(update_fields=['esta_habilitado'])
        return user

    @staticmethod
    def deshabilitar_usuario(usuario_id):
        user = Usuario.objects.get(pk=usuario_id)
        if user.rol == 'DECANA':
            raise Exception("No se puede deshabilitar a una DECANA.")
        user.esta_habilitado = False
        user.save(update_fields=['esta_habilitado'])
        return user

    @staticmethod
    def eliminar_usuario(usuario_id, current_user_id):
        if str(usuario_id) == str(current_user_id):
            raise Exception("No puedes eliminarte a ti mismo.")
        user = Usuario.objects.get(pk=usuario_id)
        if user.rol == 'DECANA':
            raise Exception("No se puede eliminar a una DECANA.")
        user.is_active = False
        user.save(update_fields=['is_active'])
        return user

    @staticmethod
    def actualizar_usuario(usuario_id, rol, programa_id):
        """Actualiza el rol y programa académico de un usuario."""
        user = Usuario.objects.get(pk=usuario_id)
        
        if rol:
            user.rol = rol
        
        if programa_id:
            user.programa_academico_id = programa_id
        elif programa_id == "": # Si se envía vacío intencionalmente
            user.programa_academico = None
            
        user.save()
        return user


    @staticmethod
    def listar_programas():
        """Lista todos los programas académicos."""
        return ProgramaAcademico.objects.all()

    @staticmethod
    def actualizar_foto_perfil(usuario, archivo_foto):
        """Actualiza la foto de perfil de un usuario."""
        if archivo_foto:
            usuario.foto_perfil = archivo_foto
            usuario.save(update_fields=['foto_perfil'])
            return True
        return False
