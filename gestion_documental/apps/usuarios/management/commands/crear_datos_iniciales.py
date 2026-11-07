from django.core.management.base import BaseCommand, CommandError
from apps.usuarios.models import Usuario, ProgramaAcademico
from apps.documentos.models import Categoria
import os
import secrets

class Command(BaseCommand):
    help = 'Crea los datos iniciales para la base de datos (SOLO desarrollo)'

    def handle(self, *args, **kwargs):
        import django.conf as _conf
        if not _conf.settings.DEBUG and os.getenv('SEED_ALLOW_PROD', '0') != '1':
            raise CommandError('Rehúsa crear seeds en prod. Define SEED_ALLOW_PROD=1 solo si sabes lo que haces.')
        seed_password = os.getenv('SEED_PASSWORD')
        if not seed_password:
            # H-09: nunca más Admin123! por defecto; password aleatorio impreso una vez
            seed_password = secrets.token_urlsafe(16)
            self.stdout.write(self.style.WARNING('[SEED] SEED_PASSWORD no definido: usando password aleatorio (ver abajo).'))
        # 1. Crear Programas Académicos
        programas_data = [
            {'nombre': 'Ingeniería Civil', 'codigo': 'civil'},
            {'nombre': 'Ingeniería de Software', 'codigo': 'software'},
            {'nombre': 'Ingeniería Mecánica', 'codigo': 'mecanica'}
        ]
        for p in programas_data:
            ProgramaAcademico.objects.update_or_create(codigo=p['codigo'], defaults={'nombre': p['nombre']})

        # 2. Crear Categorías
        categorias_nombres = [
            'Autoevaluación', 'Laboratorios', 'Estadísticas',
            'Egresados/Estudiantes', 'Prácticas', 'Homologaciones',
            'Formulación de programas', 'Actas Institucionales',
            'Planificación', 'Informes', 'Evaluación',
            'Guía Pedagógica', 'Administrativo'
        ]
        for c in categorias_nombres:
            Categoria.objects.update_or_create(nombre=c)

        # 3. Crear Usuarios
        p_software = ProgramaAcademico.objects.get(codigo='software')

        usuarios_data = [
            {
                'email': 'decana@campusucc.edu.co',
                'first_name': 'Andrea', 'last_name': 'Decana',
                'rol': 'DECANA', 'esta_habilitado': True, 'is_active': True,
                'is_staff': True, 'is_superuser': True,
                'username': 'decana', 'programa_academico': None
            },
            {
                'email': 'coordinador@campusucc.edu.co',
                'first_name': 'Carlos', 'last_name': 'Coordinador',
                'rol': 'COORDINADOR', 'esta_habilitado': True, 'is_active': True,
                'username': 'coordinador', 'programa_academico': p_software
            },
            {
                'email': 'docente@campusucc.edu.co',
                'first_name': 'Javier', 'last_name': 'Docente',
                'rol': 'DOCENTE_PLANTA', 'esta_habilitado': True, 'is_active': True,
                'username': 'docente', 'programa_academico': p_software
            },
            {
                'email': 'docente_inactivo@campusucc.edu.co',
                'first_name': 'Luis', 'last_name': 'Inactivo',
                'rol': 'DOCENTE_PLANTA', 'esta_habilitado': False, 'is_active': True,
                'username': 'docente_inactivo', 'programa_academico': p_software
            }
        ]

        for u in usuarios_data:
            user, created = Usuario.objects.update_or_create(
                email=u['email'],
                defaults={
                    'first_name': u['first_name'],
                    'last_name': u['last_name'],
                    'rol': u['rol'],
                    'esta_habilitado': u['esta_habilitado'],
                    'is_active': u['is_active'],
                    'is_staff': u.get('is_staff', False),
                    'is_superuser': u.get('is_superuser', False),
                    'username': u['username'],
                    'programa_academico': u['programa_academico']
                }
            )
            user.set_password(seed_password)
            user.save()

        # 4. Imprimir resultados
        self.stdout.write(self.style.SUCCESS('[OK] Datos iniciales creados correctamente'))
        self.stdout.write('   Usuarios creados/actualizados: 4')
        self.stdout.write('   Programas: 3 | Categorias: 13')
        if not os.getenv('SEED_PASSWORD'):
            self.stdout.write(self.style.WARNING(f'   [SEED] Password inicial (rótelo ya): {seed_password}'))
