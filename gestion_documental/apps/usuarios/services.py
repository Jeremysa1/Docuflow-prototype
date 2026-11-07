"""
Servicios del módulo de usuarios.

Contiene toda la lógica de negocio relacionada con autenticación,
recuperación de contraseña y gestión de usuarios.
"""
import secrets
import re
from datetime import timedelta

from django.contrib.auth import login, logout
from django.core.mail import send_mail
from django.utils import timezone

from .models import Usuario, ProgramaAcademico
from .exceptions import AuthError
from core.utils.helpers import ReglaNegocioError
from core.cache_stats import bump_stats

# M2: límites de intentos fallidos. Ninguno bloquea la cuenta para todas las IP,
# así nadie puede dejar fuera a otra persona escribiendo mal su contraseña.
LIMITE_FALLOS_IP = 10
LIMITE_FALLOS_CUENTA_IP = 5
VENTANA_FALLOS_SEG = 15 * 60


def _clave_ip(ip):
    return f'sigea:login:ip:{ip or "sin-ip"}'


def _clave_cuenta_ip(email, ip):
    return f'sigea:login:cuenta:{(email or "").strip().lower()}:{ip or "sin-ip"}'


def _fallos(clave):
    from django.core.cache import cache
    return cache.get(clave, 0)


def _sumar_fallo(clave):
    from django.core.cache import cache
    try:
        cache.incr(clave)
    except ValueError:
        cache.set(clave, 1, timeout=VENTANA_FALLOS_SEG)


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
        from core.services.audit_service import AuditService
        from core.utils.helpers import enmascarar_email, obtener_ip_cliente

        ip = obtener_ip_cliente(request)
        clave_ip, clave_cuenta = _clave_ip(ip), _clave_cuenta_ip(email, ip)

        def fallo(usuario, motivo, codigo, mensaje, contar=True):
            if contar:
                _sumar_fallo(clave_ip)
                _sumar_fallo(clave_cuenta)
            # A6: todo intento fallido queda auditado; si el correo no existe se
            # guarda enmascarado (podría ser una contraseña escrita por error).
            AuditService.log(
                usuario=usuario, accion='LOGIN_FALLIDO', request=request,
                detalle=f"{motivo}: {usuario.email if usuario else enmascarar_email(email)}",
            )
            raise AuthError(codigo=codigo, mensaje=mensaje)

        # 0. M2: demasiados fallos desde esta IP, o para esta cuenta desde esta IP.
        #    No se evalúa la contraseña y la respuesta es la misma de siempre.
        if _fallos(clave_ip) >= LIMITE_FALLOS_IP or _fallos(clave_cuenta) >= LIMITE_FALLOS_CUENTA_IP:
            fallo(Usuario.objects.filter(email=email).first(), 'Límite de intentos por IP', 429,
                  "No pudimos verificar tu identidad", contar=False)

        # 1. Buscar usuario por email
        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            fallo(None, 'Correo no registrado', 401, "No pudimos verificar tu identidad")

        # 2. Verificar contraseña
        if not user.check_password(password):
            fallo(user, 'Contraseña incorrecta', 401, "No pudimos verificar tu identidad")

        # 3. Verificar estado de la cuenta
        if not user.is_active:
            fallo(user, 'Cuenta inactiva', 403, "Te identificamos, pero tu cuenta no tiene acceso")

        if not user.esta_habilitado:
            fallo(user, 'Cuenta no habilitada', 403, "Te identificamos, pero tu cuenta no tiene acceso")

        if user.bloqueado_hasta and user.bloqueado_hasta > timezone.now():
            minutos_restantes = int(
                (user.bloqueado_hasta - timezone.now()).total_seconds() / 60
            ) + 1
            fallo(user, 'Cuenta bloqueada', 403,
                  f"Tu cuenta está bloqueada. Inténtalo en {minutos_restantes} minutos")

        # 4. Login exitoso: se limpia el contador de esta cuenta en esta IP
        from django.core.cache import cache
        cache.delete(clave_cuenta)
        login(request, user)
        user.intentos_fallidos = 0
        user.bloqueado_hasta = None
        user.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])
        AuditService.log(usuario=user, accion='LOGIN', request=request)
        return user

    @staticmethod
    def cerrar_sesion(request):
        """Cierra la sesión del usuario actual."""
        from core.services.audit_service import AuditService
        if getattr(request.user, 'is_authenticated', False):
            AuditService.log(usuario=request.user, accion='LOGOUT', request=request)
        logout(request)

    # ─── RECUPERACIÓN DE CONTRASEÑA ──────────────────────────────

    @staticmethod
    def solicitar_recuperacion(email):
        """
        Genera y envía un token de recuperación de 6 dígitos.
        Siempre retorna True (no revela si el email existe).
        H-07: CSPRNG + throttle de re-emisión (no resetea intentos si hay token vigente reciente).
        """
        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return True  # No revelar por seguridad

        ahora = timezone.now()
        # Throttle: si se emitió hace <60s (expiración > ahora+2min), no re-emitir ni resetear intentos
        if user.token_expiracion and user.token_expiracion > ahora + timedelta(minutes=2):
            return True

        # Generar token de 6 dígitos con CSPRNG
        token = f"{secrets.randbelow(1000000):06d}"
        if len(token) != 6 or token == '000000':
            token = f"{secrets.randbelow(900000) + 100000:06d}"

        # Guardar token con expiración de 3 minutos
        user.token_recuperacion = token
        user.token_expiracion = ahora + timedelta(minutes=3)
        user.token_intentos = 0
        user.save(update_fields=[
            'token_recuperacion', 'token_expiracion', 'token_intentos'
        ])

        # Enviar email (console backend en desarrollo)
        send_mail(
            subject='Recuperación de contraseña - SIGEA',
            message=(
                f'Tu código de verificación es: {token}.\n'
                f'Válido por 3 minutos. Máximo 3 intentos.'
            ),
            from_email='noreply@SIGEA.edu.co',
            recipient_list=[email],
            fail_silently=False,
        )

        return True

    @staticmethod
    def confirmar_email_recuperacion(email):
        """
        Retorna el email ESCRITO enmascarado ("ye***@gmail.com").
        M3: no se consulta la base de datos, así la pantalla es idéntica exista o no.
        """
        from core.utils.helpers import enmascarar_email
        if '@' not in (email or ''):
            return None
        return enmascarar_email(email)

    @staticmethod
    def validar_token(email, token):
        """
        Valida el token de recuperación.
        Retorna dict: {'valido': bool, 'error': str|None, 'intentos_restantes': int}
        """
        # M3: todos los fallos responden igual (no revela si el correo existe ni
        # cuántos intentos le quedan a una cuenta real).
        invalido = {'valido': False, 'error': 'El código no es válido o ya expiró. Pide uno nuevo si lo necesitas.',
                    'intentos_restantes': None}
        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return invalido

        if not user.token_expiracion or user.token_expiracion < timezone.now():
            return invalido
        if user.token_intentos >= 3:
            return invalido
        if not secrets.compare_digest(str(token), str(user.token_recuperacion or '')):
            user.token_intentos += 1
            user.save(update_fields=['token_intentos'])
            return invalido

        # Token válido - NO limpiar aún
        return {'valido': True, 'error': None, 'intentos_restantes': 3 - user.token_intentos}

    @staticmethod
    def cambiar_contrasena(email, nueva_contrasena):
        """
        Cambia la contraseña validando políticas de seguridad.
        Retorna dict: {'exito': bool, 'error': str|None}
        """
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError

        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return {'exito': False, 'error': 'No se pudo cambiar la contraseña.'}

        # M4: la misma política de AUTH_PASSWORD_VALIDATORS que registro e invitación
        try:
            validate_password(nueva_contrasena, user)
        except ValidationError as e:
            return {'exito': False, 'error': ' '.join(e.messages)}

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

    # ─── INVITACIÓN (M8) ─────────────────────────────────────────

    @staticmethod
    def enlace_invitacion(user, request=None):
        """Enlace de un solo uso: el token deja de valer en cuanto cambia la contraseña."""
        from django.contrib.auth.tokens import default_token_generator
        from django.urls import reverse
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        ruta = reverse('auth:invitacion', args=[urlsafe_base64_encode(force_bytes(user.pk)),
                                                default_token_generator.make_token(user)])
        return request.build_absolute_uri(ruta) if request is not None else ruta

    @staticmethod
    def enviar_invitacion(user, request=None):
        send_mail(
            subject='Te damos la bienvenida a SIGEA',
            message=(
                f'Hola, {user.first_name}.\n\n'
                'La Decana creó tu cuenta en SIGEA. Para entrar, crea tu contraseña aquí:\n'
                f'{UsuarioService.enlace_invitacion(user, request)}\n\n'
                'El enlace sirve una sola vez y vence en 3 días.'
            ),
            from_email='noreply@SIGEA.edu.co',
            recipient_list=[user.email],
            fail_silently=False,
        )

    @staticmethod
    def usuario_de_invitacion(uidb64, token):
        """El usuario si el enlace es válido; None si no (vencido, usado o alterado)."""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_str
        from django.utils.http import urlsafe_base64_decode
        try:
            user = Usuario.objects.get(pk=force_str(urlsafe_base64_decode(uidb64)))
        except (Usuario.DoesNotExist, ValueError, TypeError, OverflowError):
            return None
        return user if default_token_generator.check_token(user, token) else None

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
    def _auditar_gestion(actor, accion, afectado, request=None, extra=''):
        """A6: deja traza de la gestión de usuarios con el usuario afectado en el detalle."""
        from core.services.audit_service import AuditService
        detalle = f"{afectado.get_full_name()} <{afectado.email}>"
        if extra:
            detalle = f"{detalle} | {extra}"
        AuditService.log(usuario=actor or afectado, accion=accion, request=request, detalle=detalle)

    @staticmethod
    def crear_usuario(nombre, apellido, email, rol, programa_id=None, actor=None, request=None):
        if Usuario.objects.filter(email=email).exists():
            raise ReglaNegocioError("El correo electrónico ya está registrado.")
        if rol not in (Usuario.Rol.DECANA, Usuario.Rol.COORDINADOR, Usuario.Rol.DOCENTE_PLANTA):
            raise ReglaNegocioError("Rol inválido.")
        # R2-03: unicidad de DECANA y COORDINADORA también al crear
        if rol in (Usuario.Rol.DECANA, Usuario.Rol.COORDINADOR):
            if Usuario.objects.filter(rol=rol, is_active=True).exists():
                raise ReglaNegocioError(f"Ya existe un(a) {rol} activo(a). Solo puede haber uno(a).")

        username = email.split('@')[0]
        # Handle duplicates in username just in case
        base_username = username
        counter = 1
        while Usuario.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # M8: si la crea la Decana queda habilitada (recibirá una invitación);
        # el registro público (sin actor) espera a que la Decana la habilite.
        esta_habilitado = actor is not None or rol in ('COORDINADOR', 'DECANA')

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
        UsuarioService._auditar_gestion(
            actor, 'CREO_USUARIO', user, request,
            extra=f"rol={rol}" if actor else 'Registro público',
        )
        bump_stats()
        if actor is not None:
            UsuarioService.enviar_invitacion(user, request)
        return user

    @staticmethod
    def habilitar_usuario(usuario_id, actor=None, request=None):
        user = Usuario.objects.get(pk=usuario_id)
        user.esta_habilitado = True
        user.save(update_fields=['esta_habilitado'])
        UsuarioService._auditar_gestion(actor, 'HABILITO_USUARIO', user, request)
        bump_stats()
        return user

    @staticmethod
    def deshabilitar_usuario(usuario_id, actor=None, request=None):
        user = Usuario.objects.get(pk=usuario_id)
        if user.rol == 'DECANA':
            raise ReglaNegocioError("No se puede deshabilitar a una DECANA.")
        user.esta_habilitado = False
        user.save(update_fields=['esta_habilitado'])
        UsuarioService._auditar_gestion(actor, 'DESHABILITO_USUARIO', user, request)
        bump_stats()
        return user

    @staticmethod
    def eliminar_usuario(usuario_id, current_user_id, actor=None, request=None):
        if str(usuario_id) == str(current_user_id):
            raise ReglaNegocioError("No puedes eliminarte a ti mismo.")
        user = Usuario.objects.get(pk=usuario_id)
        if user.rol == 'DECANA':
            raise ReglaNegocioError("No se puede eliminar a una DECANA.")
        user.is_active = False
        user.save(update_fields=['is_active'])
        UsuarioService._auditar_gestion(actor, 'ELIMINO_USUARIO', user, request)
        bump_stats()
        return user

    @staticmethod
    def actualizar_usuario(usuario_id, rol, programa_id, current_user_id=None, actor=None, request=None):
        """Actualiza el rol y programa académico de un usuario."""
        user = Usuario.objects.get(pk=usuario_id)
        rol_anterior = user.rol
        programa_anterior = user.programa_academico_id

        nuevo_rol = rol or user.rol

        # R2-03: nadie cambia su propio rol (evita auto-democión de la DECANA)
        if current_user_id is not None and str(usuario_id) == str(current_user_id) and nuevo_rol != user.rol:
            raise ReglaNegocioError("No puedes cambiar tu propio rol.")

        # R2-03: unicidad de DECANA y COORDINADORA (una sola de cada una en la facultad)
        if nuevo_rol in ('DECANA', 'COORDINADOR') and user.rol != nuevo_rol:
            if Usuario.objects.filter(rol=nuevo_rol, is_active=True).exclude(pk=user.pk).exists():
                raise ReglaNegocioError(f"Ya existe un(a) {nuevo_rol} activo(a). Solo puede haber uno(a).")
        if user.rol in ('DECANA', 'COORDINADOR') and nuevo_rol != user.rol:
            if not Usuario.objects.filter(rol=user.rol, is_active=True).exclude(pk=user.pk).exists():
                raise ReglaNegocioError(f"No se puede degradar al único {user.rol} activo.")
        if rol and rol not in (Usuario.Rol.DECANA, Usuario.Rol.COORDINADOR, Usuario.Rol.DOCENTE_PLANTA):
            raise ReglaNegocioError("Rol inválido.")

        if rol:
            user.rol = rol
            # R2-03: sincronizar flags Django con el rol (evita superusuario sigiloso)
            if rol == 'DECANA':
                user.is_staff = True
                user.is_superuser = True
            else:
                user.is_staff = False
                user.is_superuser = False

        if programa_id:
            user.programa_academico_id = programa_id
        elif programa_id == "": # Si se envía vacío intencionalmente
            user.programa_academico = None

        if rol:
            user.save()
        else:
            user.save(update_fields=['programa_academico'])
        UsuarioService._auditar_gestion(
            actor, 'ACTUALIZO_USUARIO', user, request,
            extra=f"rol {rol_anterior}->{user.rol}; programa {programa_anterior}->{user.programa_academico_id}",
        )
        return user


    @staticmethod
    def listar_programas():
        """Lista todos los programas académicos."""
        return ProgramaAcademico.objects.all()


