from django.core.management.base import BaseCommand

from visits.models import Gardener, ServiceType


class Command(BaseCommand):
    help = 'Carga datos iniciales: tipos de servicio y jardineros de ejemplo.'

    def handle(self, *args, **options):
        self.stdout.write('Cargando tipos de servicio...')
        services = [
            {
                'name': 'Mantención de jardín',
                'description': 'Servicio completo de mantención: corte de pasto, desmalezado, fertilización y limpieza general.',
            },
            {
                'name': 'Diseño de jardín',
                'description': 'Diseño paisajístico personalizado para espacios exteriores, terrazas y patios.',
            },
            {
                'name': 'Poda de árboles',
                'description': 'Poda técnica de árboles y arbustos, incluyendo poda de formación, sanitaria y de rejuvenecimiento.',
            },
            {
                'name': 'Sistema de riego',
                'description': 'Instalación, reparación y mantención de sistemas de riego automático y manual.',
            },
            {
                'name': 'Limpieza de terreno',
                'description': 'Limpieza integral de terrenos: retiro de escombros, desmalezado profundo y preparación de suelo.',
            },
        ]
        for svc in services:
            obj, created = ServiceType.objects.get_or_create(
                name=svc['name'],
                defaults={'description': svc['description']},
            )
            status = 'creado' if created else 'ya existía'
            self.stdout.write(f'  {obj.name}: {status}')

        self.stdout.write('\nCargando jardineros...')
        gardeners = [
            {
                'first_name': 'Carlos',
                'last_name': 'Mendoza',
                'phone': '+56 9 8765 4321',
                'email': 'carlos.mendoza@ziyu.cl',
                'specialty': 'Diseño paisajístico',
            },
            {
                'first_name': 'Ana',
                'last_name': 'Valenzuela',
                'phone': '+56 9 1234 5678',
                'email': 'ana.valenzuela@ziyu.cl',
                'specialty': 'Poda y mantención',
            },
            {
                'first_name': 'Roberto',
                'last_name': 'Figueroa',
                'phone': '+56 9 5555 1234',
                'email': 'roberto.figueroa@ziyu.cl',
                'specialty': 'Sistemas de riego',
            },
        ]
        for g in gardeners:
            obj, created = Gardener.objects.get_or_create(
                first_name=g['first_name'],
                last_name=g['last_name'],
                defaults={
                    'phone': g['phone'],
                    'email': g['email'],
                    'specialty': g['specialty'],
                },
            )
            status = 'creado' if created else 'ya existía'
            self.stdout.write(f'  {obj}: {status}')

        self.stdout.write(self.style.SUCCESS('\nDatos iniciales cargados exitosamente.'))
