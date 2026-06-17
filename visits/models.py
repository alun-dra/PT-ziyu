import uuid

from django.core.exceptions import ValidationError
from django.db import models


class ServiceType(models.Model):
    """Catálogo de tipos de servicio de jardinería."""

    name = models.CharField(
        max_length=100,
        verbose_name='Nombre',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
    )

    class Meta:
        verbose_name = 'Tipo de Servicio'
        verbose_name_plural = 'Tipos de Servicio'
        ordering = ['name']

    def __str__(self):
        return self.name


class Gardener(models.Model):
    """Jardinero que realiza las visitas."""

    first_name = models.CharField(
        max_length=100,
        verbose_name='Nombre',
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name='Apellido',
    )
    phone = models.CharField(
        max_length=20,
        verbose_name='Teléfono',
    )
    email = models.EmailField(
        verbose_name='Correo electrónico',
    )
    specialty = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Especialidad',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
    )

    class Meta:
        verbose_name = 'Jardinero'
        verbose_name_plural = 'Jardineros'
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class VisitRequest(models.Model):
    """Solicitud de visita de un cliente."""

    class Status(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        ASIGNADA = 'asignada', 'Asignada'
        CONFIRMADA = 'confirmada', 'Confirmada'
        CANCELADA = 'cancelada', 'Cancelada'

    # Datos del cliente
    client_name = models.CharField(
        max_length=200,
        verbose_name='Nombre del cliente',
    )
    client_email = models.EmailField(
        verbose_name='Correo electrónico',
    )
    client_phone = models.CharField(
        max_length=20,
        verbose_name='Teléfono',
    )

    # Ubicación
    address = models.CharField(
        max_length=300,
        verbose_name='Dirección',
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        verbose_name='Latitud',
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        verbose_name='Longitud',
    )

    # Detalles del servicio
    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.PROTECT,
        related_name='visit_requests',
        verbose_name='Tipo de servicio',
    )
    garden_area_sqm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Área del jardín (m²)',
    )

    # Agenda
    preferred_date = models.DateField(
        verbose_name='Fecha preferida',
    )
    preferred_time_start = models.TimeField(
        verbose_name='Hora de inicio',
    )
    preferred_time_end = models.TimeField(
        verbose_name='Hora de término',
    )

    # Información adicional
    notes = models.TextField(
        blank=True,
        verbose_name='Notas adicionales',
    )

    # Estado y asignación
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDIENTE,
        db_index=True,
        verbose_name='Estado',
    )
    gardener = models.ForeignKey(
        Gardener,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visit_requests',
        verbose_name='Jardinero asignado',
    )

    # Token de confirmación (para acceso seguro sin autenticación)
    confirmation_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='Token de confirmación',
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización',
    )

    class Meta:
        verbose_name = 'Solicitud de Visita'
        verbose_name_plural = 'Solicitudes de Visita'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['preferred_date']),
            models.Index(fields=['confirmation_token']),
        ]

    def __str__(self):
        return f'{self.client_name} - {self.service_type} ({self.get_status_display()})'

    def clean(self):
        super().clean()
        errors = {}

        # Validar que la hora de término sea posterior a la de inicio
        if self.preferred_time_start and self.preferred_time_end:
            if self.preferred_time_end <= self.preferred_time_start:
                errors['preferred_time_end'] = (
                    'La hora de término debe ser posterior a la hora de inicio.'
                )

        # Validar superposición de horarios del jardinero
        if self.gardener and self.preferred_date and self.preferred_time_start and self.preferred_time_end:
            overlapping = VisitRequest.objects.filter(
                gardener=self.gardener,
                preferred_date=self.preferred_date,
                status__in=[self.Status.ASIGNADA, self.Status.CONFIRMADA],
            ).exclude(pk=self.pk)

            for visit in overlapping:
                if (
                    self.preferred_time_start < visit.preferred_time_end
                    and self.preferred_time_end > visit.preferred_time_start
                ):
                    errors['gardener'] = (
                        f'{self.gardener} ya tiene una visita asignada el '
                        f'{self.preferred_date} entre {visit.preferred_time_start} '
                        f'y {visit.preferred_time_end}.'
                    )
                    break

        if errors:
            raise ValidationError(errors)
