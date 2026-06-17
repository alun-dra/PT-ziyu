from datetime import date, time, timedelta
from uuid import uuid4

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from .forms import AssignGardenerForm, VisitRequestForm
from .models import Gardener, ServiceType, VisitRequest
from .services import assign_gardener_to_visit, check_gardener_availability


class ServiceTypeModelTest(TestCase):

    def test_str_returns_name(self):
        service = ServiceType.objects.create(name='Poda de árboles')
        self.assertEqual(str(service), 'Poda de árboles')

    def test_default_is_active(self):
        service = ServiceType.objects.create(name='Riego')
        self.assertTrue(service.is_active)


class GardenerModelTest(TestCase):

    def test_str_returns_full_name(self):
        gardener = Gardener.objects.create(
            first_name='Juan',
            last_name='Pérez',
            phone='+56912345678',
            email='juan@test.cl',
        )
        self.assertEqual(str(gardener), 'Juan Pérez')

    def test_default_is_active(self):
        gardener = Gardener.objects.create(
            first_name='Ana',
            last_name='Silva',
            phone='+56987654321',
            email='ana@test.cl',
        )
        self.assertTrue(gardener.is_active)


class VisitRequestModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.service = ServiceType.objects.create(name='Mantención')
        cls.gardener = Gardener.objects.create(
            first_name='Carlos',
            last_name='López',
            phone='+56911111111',
            email='carlos@test.cl',
        )

    def _create_visit(self, **kwargs):
        defaults = {
            'client_name': 'Test Cliente',
            'client_email': 'cliente@test.cl',
            'client_phone': '+56900000000',
            'address': 'Test 123',
            'service_type': self.service,
            'garden_area_sqm': 50,
            'preferred_date': date.today() + timedelta(days=7),
            'preferred_time_start': time(10, 0),
            'preferred_time_end': time(12, 0),
        }
        defaults.update(kwargs)
        return VisitRequest.objects.create(**defaults)

    def test_str_representation(self):
        visit = self._create_visit()
        expected = f'Test Cliente - Mantención (Pendiente)'
        self.assertEqual(str(visit), expected)

    def test_default_status_is_pendiente(self):
        visit = self._create_visit()
        self.assertEqual(visit.status, VisitRequest.Status.PENDIENTE)

    def test_confirmation_token_is_generated(self):
        visit = self._create_visit()
        self.assertIsNotNone(visit.confirmation_token)

    def test_confirmation_tokens_are_unique(self):
        visit1 = self._create_visit(client_name='Cliente 1')
        visit2 = self._create_visit(client_name='Cliente 2')
        self.assertNotEqual(visit1.confirmation_token, visit2.confirmation_token)

    def test_clean_rejects_end_before_start(self):
        visit = self._create_visit(
            preferred_time_start=time(14, 0),
            preferred_time_end=time(12, 0),
        )
        with self.assertRaises(ValidationError) as ctx:
            visit.full_clean()
        self.assertIn('preferred_time_end', ctx.exception.message_dict)

    def test_clean_rejects_overlapping_gardener_schedule(self):
        self._create_visit(
            gardener=self.gardener,
            status=VisitRequest.Status.ASIGNADA,
            preferred_date=date.today() + timedelta(days=7),
            preferred_time_start=time(10, 0),
            preferred_time_end=time(12, 0),
        )
        visit2 = self._create_visit(
            gardener=self.gardener,
            status=VisitRequest.Status.ASIGNADA,
            preferred_date=date.today() + timedelta(days=7),
            preferred_time_start=time(11, 0),
            preferred_time_end=time(13, 0),
        )
        with self.assertRaises(ValidationError) as ctx:
            visit2.full_clean()
        self.assertIn('gardener', ctx.exception.message_dict)

    def test_clean_allows_non_overlapping_times(self):
        self._create_visit(
            gardener=self.gardener,
            status=VisitRequest.Status.ASIGNADA,
            preferred_date=date.today() + timedelta(days=7),
            preferred_time_start=time(10, 0),
            preferred_time_end=time(12, 0),
        )
        visit2 = self._create_visit(
            gardener=self.gardener,
            status=VisitRequest.Status.ASIGNADA,
            preferred_date=date.today() + timedelta(days=7),
            preferred_time_start=time(12, 0),
            preferred_time_end=time(14, 0),
        )
        # Should not raise
        visit2.full_clean()

    def test_clean_allows_different_dates(self):
        self._create_visit(
            gardener=self.gardener,
            status=VisitRequest.Status.ASIGNADA,
            preferred_date=date.today() + timedelta(days=7),
            preferred_time_start=time(10, 0),
            preferred_time_end=time(12, 0),
        )
        visit2 = self._create_visit(
            gardener=self.gardener,
            status=VisitRequest.Status.ASIGNADA,
            preferred_date=date.today() + timedelta(days=8),
            preferred_time_start=time(10, 0),
            preferred_time_end=time(12, 0),
        )
        # Should not raise — different day
        visit2.full_clean()


class VisitRequestFormTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.service = ServiceType.objects.create(name='Mantención')

    def _valid_data(self, **overrides):
        data = {
            'client_name': 'Test Cliente',
            'client_email': 'test@test.cl',
            'client_phone': '+56900000000',
            'address': 'Av. Test 123',
            'service_type': self.service.pk,
            'garden_area_sqm': '50.00',
            'preferred_date': (date.today() + timedelta(days=7)).isoformat(),
            'preferred_time_start': '10:00',
            'preferred_time_end': '12:00',
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        form = VisitRequestForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_required_fields(self):
        form = VisitRequestForm(data={})
        self.assertFalse(form.is_valid())
        required = [
            'client_name', 'client_email', 'client_phone',
            'address', 'service_type', 'garden_area_sqm',
            'preferred_date', 'preferred_time_start', 'preferred_time_end',
        ]
        for field in required:
            self.assertIn(field, form.errors, f'{field} should be required')

    def test_date_in_past_rejected(self):
        data = self._valid_data(preferred_date=(date.today() - timedelta(days=1)).isoformat())
        form = VisitRequestForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('preferred_date', form.errors)

    def test_end_before_start_rejected(self):
        data = self._valid_data(
            preferred_time_start='14:00',
            preferred_time_end='12:00',
        )
        form = VisitRequestForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('preferred_time_end', form.errors)

    def test_inactive_service_excluded(self):
        inactive = ServiceType.objects.create(name='Inactivo', is_active=False)
        form = VisitRequestForm()
        qs = form.fields['service_type'].queryset
        self.assertNotIn(inactive, qs)
        self.assertIn(self.service, qs)

    def test_latitude_longitude_optional(self):
        data = self._valid_data()
        # lat/lng not provided — should be valid
        form = VisitRequestForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_latitude_longitude_accepted(self):
        data = self._valid_data(latitude='-33.4489000', longitude='-70.6693000')
        form = VisitRequestForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)


class AssignGardenerFormTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.active_gardener = Gardener.objects.create(
            first_name='Activo',
            last_name='Gardener',
            phone='+56911111111',
            email='activo@test.cl',
        )
        cls.inactive_gardener = Gardener.objects.create(
            first_name='Inactivo',
            last_name='Gardener',
            phone='+56922222222',
            email='inactivo@test.cl',
            is_active=False,
        )

    def test_only_active_gardeners_shown(self):
        form = AssignGardenerForm()
        qs = form.fields['gardener'].queryset
        self.assertIn(self.active_gardener, qs)
        self.assertNotIn(self.inactive_gardener, qs)

    def test_valid_selection(self):
        form = AssignGardenerForm(data={'gardener': self.active_gardener.pk})
        self.assertTrue(form.is_valid())

    def test_invalid_inactive_selection(self):
        form = AssignGardenerForm(data={'gardener': self.inactive_gardener.pk})
        self.assertFalse(form.is_valid())


class ServicesTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.service = ServiceType.objects.create(name='Mantención')
        cls.gardener = Gardener.objects.create(
            first_name='Pedro',
            last_name='Soto',
            phone='+56933333333',
            email='pedro@test.cl',
        )

    def _create_visit(self, **kwargs):
        defaults = {
            'client_name': 'Test',
            'client_email': 'test@test.cl',
            'client_phone': '+56900000000',
            'address': 'Test 123',
            'service_type': self.service,
            'garden_area_sqm': 50,
            'preferred_date': date.today() + timedelta(days=7),
            'preferred_time_start': time(10, 0),
            'preferred_time_end': time(12, 0),
        }
        defaults.update(kwargs)
        return VisitRequest.objects.create(**defaults)

    def test_check_availability_empty_schedule(self):
        available = check_gardener_availability(
            self.gardener,
            date.today() + timedelta(days=7),
            time(10, 0),
            time(12, 0),
        )
        self.assertTrue(available)

    def test_check_availability_overlap_detected(self):
        self._create_visit(
            gardener=self.gardener,
            status=VisitRequest.Status.ASIGNADA,
        )
        available = check_gardener_availability(
            self.gardener,
            date.today() + timedelta(days=7),
            time(11, 0),
            time(13, 0),
        )
        self.assertFalse(available)

    def test_check_availability_no_overlap(self):
        self._create_visit(
            gardener=self.gardener,
            status=VisitRequest.Status.ASIGNADA,
        )
        available = check_gardener_availability(
            self.gardener,
            date.today() + timedelta(days=7),
            time(12, 0),
            time(14, 0),
        )
        self.assertTrue(available)

    def test_check_availability_excludes_visit(self):
        visit = self._create_visit(
            gardener=self.gardener,
            status=VisitRequest.Status.ASIGNADA,
        )
        available = check_gardener_availability(
            self.gardener,
            date.today() + timedelta(days=7),
            time(10, 0),
            time(12, 0),
            exclude_visit_id=visit.pk,
        )
        self.assertTrue(available)

    def test_assign_gardener_success(self):
        visit = self._create_visit()
        assign_gardener_to_visit(visit, self.gardener)
        visit.refresh_from_db()
        self.assertEqual(visit.gardener, self.gardener)
        self.assertEqual(visit.status, VisitRequest.Status.ASIGNADA)

    def test_assign_gardener_overlap_raises(self):
        self._create_visit(
            gardener=self.gardener,
            status=VisitRequest.Status.ASIGNADA,
        )
        visit2 = self._create_visit(
            preferred_time_start=time(11, 0),
            preferred_time_end=time(13, 0),
        )
        with self.assertRaises(ValidationError):
            assign_gardener_to_visit(visit2, self.gardener)


class VisitRequestViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.service = ServiceType.objects.create(name='Mantención')

    def test_get_request_form(self):
        response = self.client.get(reverse('visits:visit_request'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Solicitar Visita')
        self.assertIsInstance(response.context['form'], VisitRequestForm)

    def test_post_valid_creates_visit(self):
        data = {
            'client_name': 'María',
            'client_email': 'maria@test.cl',
            'client_phone': '+56900000000',
            'address': 'Av. Test 123',
            'service_type': self.service.pk,
            'garden_area_sqm': '50.00',
            'preferred_date': (date.today() + timedelta(days=7)).isoformat(),
            'preferred_time_start': '10:00',
            'preferred_time_end': '12:00',
        }
        response = self.client.post(reverse('visits:visit_request'), data)
        self.assertRedirects(response, reverse('visits:visit_request_success'))
        self.assertEqual(VisitRequest.objects.count(), 1)
        visit = VisitRequest.objects.first()
        self.assertEqual(visit.client_name, 'María')
        self.assertEqual(visit.status, VisitRequest.Status.PENDIENTE)

    def test_post_invalid_shows_errors(self):
        response = self.client.post(reverse('visits:visit_request'), {})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

    def test_success_page_renders(self):
        response = self.client.get(reverse('visits:visit_request_success'))
        self.assertEqual(response.status_code, 200)


class CompanyDashboardViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='admin_test',
            password='testpass123',
        )
        cls.service = ServiceType.objects.create(name='Mantención')
        cls.gardener = Gardener.objects.create(
            first_name='Carlos',
            last_name='López',
            phone='+56911111111',
            email='carlos@test.cl',
        )

    def _create_visit(self, **kwargs):
        defaults = {
            'client_name': 'Test',
            'client_email': 'test@test.cl',
            'client_phone': '+56900000000',
            'address': 'Test 123',
            'service_type': self.service,
            'garden_area_sqm': 50,
            'preferred_date': date.today() + timedelta(days=7),
            'preferred_time_start': time(10, 0),
            'preferred_time_end': time(12, 0),
        }
        defaults.update(kwargs)
        return VisitRequest.objects.create(**defaults)

    def test_requires_login(self):
        response = self.client.get(reverse('visits:company_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_dashboard_renders_for_authenticated_user(self):
        self.client.login(username='admin_test', password='testpass123')
        self._create_visit()
        response = self.client.get(reverse('visits:company_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Panel de Gestión')

    def test_dashboard_shows_stats(self):
        self.client.login(username='admin_test', password='testpass123')
        self._create_visit(status=VisitRequest.Status.PENDIENTE)
        self._create_visit(
            client_name='Otro',
            status=VisitRequest.Status.ASIGNADA,
            gardener=self.gardener,
        )
        response = self.client.get(reverse('visits:company_dashboard'))
        stats = response.context['stats']
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['pendientes'], 1)
        self.assertEqual(stats['asignadas'], 1)

    def test_dashboard_filter_by_status(self):
        self.client.login(username='admin_test', password='testpass123')
        self._create_visit(status=VisitRequest.Status.PENDIENTE)
        self._create_visit(
            client_name='Asignada',
            status=VisitRequest.Status.ASIGNADA,
            gardener=self.gardener,
        )
        response = self.client.get(
            reverse('visits:company_dashboard'),
            {'status': 'pendiente'},
        )
        visits = response.context['visits']
        self.assertEqual(visits.count(), 1)
        self.assertEqual(visits.first().status, VisitRequest.Status.PENDIENTE)


class AssignGardenerViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='admin_test',
            password='testpass123',
        )
        cls.service = ServiceType.objects.create(name='Mantención')
        cls.gardener = Gardener.objects.create(
            first_name='Carlos',
            last_name='López',
            phone='+56911111111',
            email='carlos@test.cl',
        )

    def _create_visit(self, **kwargs):
        defaults = {
            'client_name': 'Test',
            'client_email': 'test@test.cl',
            'client_phone': '+56900000000',
            'address': 'Test 123',
            'service_type': self.service,
            'garden_area_sqm': 50,
            'preferred_date': date.today() + timedelta(days=7),
            'preferred_time_start': time(10, 0),
            'preferred_time_end': time(12, 0),
        }
        defaults.update(kwargs)
        return VisitRequest.objects.create(**defaults)

    def test_requires_login(self):
        visit = self._create_visit()
        response = self.client.post(
            reverse('visits:assign_gardener', args=[visit.pk]),
            {'gardener': self.gardener.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_assign_success(self):
        self.client.login(username='admin_test', password='testpass123')
        visit = self._create_visit()
        response = self.client.post(
            reverse('visits:assign_gardener', args=[visit.pk]),
            {'gardener': self.gardener.pk},
        )
        self.assertRedirects(response, reverse('visits:company_dashboard'))
        visit.refresh_from_db()
        self.assertEqual(visit.gardener, self.gardener)
        self.assertEqual(visit.status, VisitRequest.Status.ASIGNADA)

    def test_get_not_allowed(self):
        self.client.login(username='admin_test', password='testpass123')
        visit = self._create_visit()
        response = self.client.get(
            reverse('visits:assign_gardener', args=[visit.pk]),
        )
        self.assertEqual(response.status_code, 405)


class VisitConfirmViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.service = ServiceType.objects.create(name='Mantención')
        cls.gardener = Gardener.objects.create(
            first_name='Carlos',
            last_name='López',
            phone='+56911111111',
            email='carlos@test.cl',
        )

    def _create_visit(self, **kwargs):
        defaults = {
            'client_name': 'Test',
            'client_email': 'test@test.cl',
            'client_phone': '+56900000000',
            'address': 'Test 123',
            'service_type': self.service,
            'garden_area_sqm': 50,
            'preferred_date': date.today() + timedelta(days=7),
            'preferred_time_start': time(10, 0),
            'preferred_time_end': time(12, 0),
        }
        defaults.update(kwargs)
        return VisitRequest.objects.create(**defaults)

    def test_confirm_page_shows_details(self):
        visit = self._create_visit(
            gardener=self.gardener,
            status=VisitRequest.Status.ASIGNADA,
        )
        response = self.client.get(
            reverse('visits:visit_confirm', args=[visit.confirmation_token]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, visit.client_name)

    def test_confirm_changes_status(self):
        visit = self._create_visit(
            gardener=self.gardener,
            status=VisitRequest.Status.ASIGNADA,
        )
        response = self.client.post(
            reverse('visits:visit_confirm', args=[visit.confirmation_token]),
        )
        visit.refresh_from_db()
        self.assertEqual(visit.status, VisitRequest.Status.CONFIRMADA)

    def test_confirm_invalid_token_404(self):
        response = self.client.get(
            reverse('visits:visit_confirm', args=[uuid4()]),
        )
        self.assertEqual(response.status_code, 404)

    def test_confirm_pendiente_shows_warning(self):
        visit = self._create_visit(status=VisitRequest.Status.PENDIENTE)
        response = self.client.post(
            reverse('visits:visit_confirm', args=[visit.confirmation_token]),
            follow=True,
        )
        visit.refresh_from_db()
        self.assertEqual(visit.status, VisitRequest.Status.PENDIENTE)

    def test_cancel_changes_status(self):
        visit = self._create_visit(
            gardener=self.gardener,
            status=VisitRequest.Status.ASIGNADA,
        )
        response = self.client.post(
            reverse('visits:visit_cancel', args=[visit.confirmation_token]),
        )
        visit.refresh_from_db()
        self.assertEqual(visit.status, VisitRequest.Status.CANCELADA)

    def test_idor_prevented_by_token(self):
        """Acceder con un token incorrecto retorna 404, no filtra por PK."""
        visit = self._create_visit()
        fake_token = uuid4()
        response = self.client.get(
            reverse('visits:visit_confirm', args=[fake_token]),
        )
        self.assertEqual(response.status_code, 404)
