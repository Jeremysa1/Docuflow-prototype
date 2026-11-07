"""
Vistas del módulo de usuarios.

Las vistas reciben la petición HTTP, validan formularios y delegan
la lógica de negocio al servicio correspondiente.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from .forms import LoginForm, RecuperarContrasenaForm, CambiarContrasenaForm
from .services import UsuarioService
from .exceptions import AuthError
from core.decorators.role_required import role_required
from core.utils.helpers import ReglaNegocioError
import logging

logger = logging.getLogger(__name__)
MSG_ERROR_GENERICO = 'No se pudo completar la acción. Inténtalo de nuevo o contacta a soporte.'
from django.core.paginator import Paginator


def login_view(request):
    """Vista de inicio de sesión por email."""
    if request.user.is_authenticated:
        return redirect('documentos:dashboard')

    error_tipo = None
    error_mensaje = None

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            try:
                user = UsuarioService.autenticar_usuario(
                    request,
                    form.cleaned_data['email'],
                    form.cleaned_data['password']
                )
                messages.success(request, f'Bienvenido, {user.get_full_name()}')
                return redirect('documentos:dashboard')

            except AuthError:
                # R3-06: respuesta idéntica para 401 y 403 (sin oráculo de enumeración)
                error_tipo = '401'
                error_mensaje = 'No pudimos verificar tu identidad'
    else:
        form = LoginForm()

    return render(request, 'usuarios/login.html', {
        'form': form,
        'error_tipo': error_tipo,
        'error_mensaje': error_mensaje,
    })


def registro_view(request):
    """Vista de registro público de usuarios."""
    if request.user.is_authenticated:
        if request.user.rol == 'DOCENTE_PLANTA':
            return redirect('documentos:mis_documentos')
        return redirect('documentos:dashboard')

    error = None
    if request.method == 'POST':
        nombre_completo = request.POST.get('nombre_completo', '')
        email = request.POST.get('email', '').strip().lower()
        # H-hardening: el registro público solo crea DOCENTE_PLANTA; se ignora cualquier rol enviado
        rol = 'DOCENTE_PLANTA'
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        from django.core.validators import validate_email
        from core.utils.helpers import obtener_ip_cliente, throttle_fijo
        try:
            validate_email(email)
            correo_valido = True
        except DjangoValidationError:
            correo_valido = False

        # M9: máximo 5 registros por hora desde una misma IP
        if throttle_fijo(f"sigea:throttle:registro:{obtener_ip_cliente(request) or 'sin-ip'}", 5, 3600):
            error = 'Hiciste demasiados registros seguidos. Inténtalo de nuevo en una hora.'
        elif not nombre_completo.strip():
            error = 'Escribe tu nombre completo.'
        elif not correo_valido:
            error = 'Escribe un correo válido.'
        elif password != password_confirm:
            error = "Las contraseñas no coinciden."
        else:
            try:
                # R3-05: misma política que el resto del sistema (validators de settings)
                validate_password(password)
            except DjangoValidationError as e:
                error = ' '.join(e.messages)
            else:
                try:
                    partes = nombre_completo.strip().split(' ', 1)
                    nombre = partes[0]
                    apellido = partes[1] if len(partes) > 1 else ''

                    # Crear usuario
                    user = UsuarioService.crear_usuario(nombre, apellido, email, rol, None, request=request)
                    user.set_password(password)
                    user.esta_habilitado = False  # Siempre requiere habilitación de la Decana
                    user.save()

                    messages.success(request, 'Cuenta creada exitosamente. Un administrador debe habilitarla para que puedas iniciar sesión.')
                    return redirect('auth:login')
                except ReglaNegocioError as e:
                    error = str(e)
                except Exception:
                    logger.exception('Error en el registro público')
                    error = MSG_ERROR_GENERICO

    return render(request, 'usuarios/registro.html', {'error': error})


@login_required
def logout_view(request):
    """Vista de cierre de sesión (solo POST)."""
    if request.method == 'POST':
        UsuarioService.cerrar_sesion(request)
        messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('auth:login')


def recuperar_contrasena_view(request):
    """Vista para solicitar recuperación de contraseña."""
    if request.method == 'POST':
        form = RecuperarContrasenaForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            UsuarioService.solicitar_recuperacion(email)
            # R2-01: reinicio limpio — una validación previa jamás debe sobrevivir a un email nuevo
            request.session['recovery_email'] = email
            request.session.pop('token_validado', None)
            request.session.pop('recovery_email_validado', None)
            return redirect('auth:confirmar_email')
    else:
        form = RecuperarContrasenaForm()

    return render(request, 'usuarios/recuperar_contrasena.html', {'form': form})


def confirmar_email_view(request):
    """Vista para confirmar email y enviar token."""
    email = request.session.get('recovery_email')
    if not email:
        return redirect('auth:recuperar_contrasena')

    email_enmascarado = UsuarioService.confirmar_email_recuperacion(email)

    if request.method == 'POST':
        # Enviar token
        UsuarioService.solicitar_recuperacion(email)
        # R2-01: el token nuevo invalida cualquier validación anterior
        request.session.pop('token_validado', None)
        request.session.pop('recovery_email_validado', None)
        return redirect('auth:validar_token')

    return render(request, 'usuarios/confirmar_email.html', {
        'email_enmascarado': email_enmascarado,
    })


def validar_token_view(request):
    """Vista para validar el token de 6 dígitos."""
    email = request.session.get('recovery_email')
    if not email:
        return redirect('auth:recuperar_contrasena')

    error = None
    intentos_restantes = 3

    if request.method == 'POST':
        token = request.POST.get('token', '')
        resultado = UsuarioService.validar_token(email, token)

        if resultado['valido']:
            # R2-01: la validación queda ligada al email validado, no a la sesión en abstracto
            request.session['token_validado'] = True
            request.session['recovery_email_validado'] = email
            return redirect('auth:nueva_contrasena')
        else:
            error = resultado['error']
            intentos_restantes = resultado['intentos_restantes']

    return render(request, 'usuarios/validar_token.html', {
        'error': error,
        'intentos_restantes': intentos_restantes,
    })


def reenviar_token_view(request):
    """Vista para reenviar el token de recuperación."""
    if request.method == 'POST':
        email = request.session.get('recovery_email')
        if email:
            UsuarioService.solicitar_recuperacion(email)
            # R2-01: el token nuevo invalida cualquier validación anterior
            request.session.pop('token_validado', None)
            request.session.pop('recovery_email_validado', None)
            messages.success(request, 'Código reenviado exitosamente.')
    return redirect('auth:validar_token')


def nueva_contrasena_view(request):
    """Vista para establecer nueva contraseña."""
    email = request.session.get('recovery_email')
    token_validado = request.session.get('token_validado')
    email_validado = request.session.get('recovery_email_validado')

    # R2-01: el flag solo vale para el email que se validó
    if not email or not token_validado or email_validado != email:
        return redirect('auth:login')

    error = None

    if request.method == 'POST':
        form = CambiarContrasenaForm(request.POST)
        if form.is_valid():
            nueva = form.cleaned_data['nueva_contrasena']
            confirmar = form.cleaned_data['confirmar_contrasena']

            if nueva != confirmar:
                error = 'Las contraseñas no coinciden.'
            else:
                resultado = UsuarioService.cambiar_contrasena(email, nueva)
                if resultado['exito']:
                    # Limpiar sesión de recuperación
                    request.session.pop('recovery_email', None)
                    request.session.pop('token_validado', None)
                    request.session.pop('recovery_email_validado', None)
                    messages.success(
                        request,
                        'Contraseña cambiada exitosamente. Inicia sesión con tu nueva contraseña.'
                    )
                    return redirect('auth:login')
                else:
                    error = resultado['error']
    else:
        form = CambiarContrasenaForm()

    return render(request, 'usuarios/cambiar_contrasena.html', {
        'form': form,
        'error': error,
    })


@login_required
def perfil_view(request):
    """Vista del perfil del usuario actual."""
    return render(request, 'usuarios/perfil.html', {
        'usuario': request.user,
    })


@login_required
@role_required('DECANA')
def gestion_usuarios_view(request):
    """Vista para que la Decana gestione a los usuarios."""
    rol_filter = request.GET.get('rol', '')
    prog_filter = request.GET.get('programa', '')
    hab_filter_str = request.GET.get('habilitado', '')
    
    hab_filter = None
    if hab_filter_str == '1': hab_filter = True
    elif hab_filter_str == '0': hab_filter = False

    usuarios_qs = UsuarioService.listar_usuarios(rol=rol_filter, programa=prog_filter, habilitado=hab_filter)
    
    paginator = Paginator(usuarios_qs, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    programas = UsuarioService.listar_programas()
    
    context = {
        'page_obj': page_obj,
        'programas': programas,
        'total_usuarios': UsuarioService.listar_usuarios().count(),
        'docentes_activos': UsuarioService.listar_usuarios(rol='DOCENTE_PLANTA', habilitado=True).count(),
        'coordinadores': UsuarioService.listar_usuarios(rol='COORDINADOR').count(),
        'pendientes_habilitacion': UsuarioService.listar_usuarios(rol='DOCENTE_PLANTA', habilitado=False).count(),
    }
    return render(request, 'usuarios/gestion.html', context)


@login_required
@role_required('DECANA')
def agregar_usuario_view(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        email = request.POST.get('email')
        rol = request.POST.get('rol')
        programa_id = request.POST.get('programa_id')
        try:
            UsuarioService.crear_usuario(nombre, apellido, email, rol, programa_id or None,
                                         actor=request.user, request=request)
            messages.success(request, f'Creaste la cuenta de {nombre} {apellido}. Le enviamos una invitación a {email} para que cree su contraseña.')
        except ReglaNegocioError as e:
            messages.error(request, str(e))
        except Exception:
            logger.exception('Error al crear usuario')
            messages.error(request, MSG_ERROR_GENERICO)
    return redirect('usuarios:gestion_usuarios')


@login_required
@role_required('DECANA')
def habilitar_usuario_view(request, uid):
    if request.method == 'POST':
        try:
            user = UsuarioService.habilitar_usuario(uid, actor=request.user, request=request)
            messages.success(request, f'Usuario {user.get_full_name()} habilitado.')
        except ReglaNegocioError as e:
            messages.error(request, str(e))
        except Exception:
            logger.exception('Error al habilitar usuario %s', uid)
            messages.error(request, MSG_ERROR_GENERICO)
    return redirect('usuarios:gestion_usuarios')


@login_required
@role_required('DECANA')
def deshabilitar_usuario_view(request, uid):
    if request.method == 'POST':
        try:
            user = UsuarioService.deshabilitar_usuario(uid, actor=request.user, request=request)
            messages.success(request, f'Usuario {user.get_full_name()} deshabilitado.')
        except ReglaNegocioError as e:
            messages.error(request, str(e))
        except Exception:
            logger.exception('Error al deshabilitar usuario %s', uid)
            messages.error(request, MSG_ERROR_GENERICO)
    return redirect('usuarios:gestion_usuarios')


@login_required
@role_required('DECANA')
def eliminar_usuario_view(request, uid):
    if request.method == 'POST':
        try:
            user = UsuarioService.eliminar_usuario(uid, request.user.id, actor=request.user, request=request)
            messages.success(request, f'Usuario {user.get_full_name()} eliminado.')
        except ReglaNegocioError as e:
            messages.error(request, str(e))
        except Exception:
            logger.exception('Error al eliminar usuario %s', uid)
            messages.error(request, MSG_ERROR_GENERICO)
    return redirect('usuarios:gestion_usuarios')


@login_required
@role_required('DECANA')
def editar_usuario_view(request, uid):
    """Vista para que la Decana edite el rol y programa de un usuario."""
    if request.method == 'POST':
        rol = request.POST.get('rol')
        programa_id = request.POST.get('programa_id')
        try:
            user = UsuarioService.actualizar_usuario(uid, rol, programa_id, current_user_id=request.user.id,
                                                     actor=request.user, request=request)
            messages.success(request, f'Usuario {user.get_full_name()} actualizado correctamente.')
        except ReglaNegocioError as e:
            messages.error(request, str(e))
        except Exception:
            logger.exception('Error al actualizar usuario %s', uid)
            messages.error(request, MSG_ERROR_GENERICO)
    return redirect('usuarios:gestion_usuarios')


def invitacion_view(request, uidb64, token):
    """M8: la persona invitada por la Decana crea su contraseña con un enlace de un solo uso."""
    user = UsuarioService.usuario_de_invitacion(uidb64, token)
    if user is None:
        return render(request, 'usuarios/invitacion.html', {'invalido': True}, status=400)

    error = None
    if request.method == 'POST':
        nueva = request.POST.get('nueva_contrasena', '')
        if nueva != request.POST.get('confirmar_contrasena', ''):
            error = 'Las contraseñas no coinciden.'
        else:
            try:
                validate_password(nueva, user)
            except DjangoValidationError as e:
                error = ' '.join(e.messages)
            else:
                user.set_password(nueva)  # cambia el hash: el enlace deja de valer
                user.save(update_fields=['password'])
                from core.services.audit_service import AuditService
                AuditService.log(usuario=user, accion='ACTUALIZO_USUARIO', request=request,
                                 detalle='Contraseña creada desde la invitación')
                messages.success(request, 'Listo, ya tienes contraseña. Inicia sesión.')
                return redirect('auth:login')
    return render(request, 'usuarios/invitacion.html', {'error': error, 'invitado': user})
