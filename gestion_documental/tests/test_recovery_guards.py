"""
Regresión R2-01: el flag token_validado está ligado al email validado.
Un atacante que valida su propio token NO puede cambiar la clave de otro usuario.
"""
from django.test import TestCase, Client, override_settings

from apps.usuarios.models import Usuario


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class RecoveryBindingTest(TestCase):
    def _crear(self, email, password='Clave123!'):
        u = Usuario(
            first_name='Test', last_name='User', email=email,
            username=email.split('@')[0], rol='DOCENTE_PLANTA',
            esta_habilitado=True, is_active=True,
        )
        u.set_password(password)
        u.save()
        return u

    def test_swap_email_tras_validar_no_cambia_clave_ajena(self):
        atacante = self._crear('atacante_r201@campusucc.edu.co')
        victima = self._crear('victima_r201@campusucc.edu.co', 'Original123!')
        c = Client()
        # 1. Atacante inicia recovery con SU email y lee SU token de la BD
        c.post('/login/recuperar/', {'email': atacante.email})
        atacante.refresh_from_db()
        # 2. Valida su propio token -> flag ligado a SU email
        c.post('/login/recuperar/token/', {'token': atacante.token_recuperacion})
        # 3. Cambia el email de sesión a la víctima
        c.post('/login/recuperar/', {'email': victima.email})
        # 4. Intentar fijar nueva clave debe rebotar al login sin cambiar nada
        resp = c.get('/login/recuperar/nueva-contrasena/')
        self.assertRedirects(resp, '/login/', fetch_redirect_response=False)
        resp = c.post('/login/recuperar/nueva-contrasena/', {
            'nueva_contrasena': 'Robada123!', 'confirmar_contrasena': 'Robada123!',
        })
        self.assertRedirects(resp, '/login/', fetch_redirect_response=False)
        victima.refresh_from_db()
        self.assertTrue(victima.check_password('Original123!'))
        self.assertFalse(victima.check_password('Robada123!'))

    def test_flujo_legitimo_sigue_funcionando(self):
        user = self._crear('legit_r201@campusucc.edu.co', 'Antes123!')
        c = Client()
        c.post('/login/recuperar/', {'email': user.email})
        user.refresh_from_db()
        c.post('/login/recuperar/confirmar/')
        c.post('/login/recuperar/token/', {'token': user.token_recuperacion})
        resp = c.post('/login/recuperar/nueva-contrasena/', {
            'nueva_contrasena': 'Despues123!', 'confirmar_contrasena': 'Despues123!',
        })
        self.assertRedirects(resp, '/login/', fetch_redirect_response=False)
        user.refresh_from_db()
        self.assertTrue(user.check_password('Despues123!'))
