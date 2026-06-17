from datetime import date

from django import forms
from django.core.exceptions import ValidationError

from .models import Gardener, VisitRequest


class VisitRequestForm(forms.ModelForm):
    """Formulario público para que un cliente solicite una visita."""

    class Meta:
        model = VisitRequest
        fields = [
            'client_name',
            'client_email',
            'client_phone',
            'address',
            'latitude',
            'longitude',
            'service_type',
            'garden_area_sqm',
            'preferred_date',
            'preferred_time_start',
            'preferred_time_end',
            'notes',
        ]
        widgets = {
            'client_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: María González',
                'autocomplete': 'name',
            }),
            'client_email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'correo@ejemplo.cl',
                'autocomplete': 'email',
            }),
            'client_phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+56 9 1234 5678',
                'autocomplete': 'tel',
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: Av. Providencia 1234, Santiago',
                'autocomplete': 'street-address',
            }),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'service_type': forms.Select(attrs={
                'class': 'form-input',
            }),
            'garden_area_sqm': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: 50',
                'min': '1',
                'step': '0.01',
            }),
            'preferred_date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date',
            }),
            'preferred_time_start': forms.TimeInput(attrs={
                'class': 'form-input',
                'type': 'time',
            }),
            'preferred_time_end': forms.TimeInput(attrs={
                'class': 'form-input',
                'type': 'time',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': 'Describe tu jardín o indica detalles relevantes...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service_type'].queryset = self.fields[
            'service_type'
        ].queryset.filter(is_active=True)
        self.fields['service_type'].empty_label = 'Selecciona un servicio'

    def clean_preferred_date(self):
        preferred_date = self.cleaned_data.get('preferred_date')
        if preferred_date and preferred_date < date.today():
            raise ValidationError('La fecha no puede ser anterior a hoy.')
        return preferred_date

    def clean(self):
        cleaned_data = super().clean()
        time_start = cleaned_data.get('preferred_time_start')
        time_end = cleaned_data.get('preferred_time_end')

        if time_start and time_end and time_end <= time_start:
            self.add_error(
                'preferred_time_end',
                'La hora de término debe ser posterior a la hora de inicio.',
            )

        return cleaned_data


class AssignGardenerForm(forms.Form):
    """Formulario para asignar un jardinero a una solicitud de visita."""

    gardener = forms.ModelChoiceField(
        queryset=Gardener.objects.filter(is_active=True),
        label='Jardinero',
        empty_label='Selecciona un jardinero',
        widget=forms.Select(attrs={
            'class': 'form-input',
        }),
    )
