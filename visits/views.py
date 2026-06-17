import json

from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import AssignGardenerForm, VisitRequestForm
from .models import Gardener, ServiceType, VisitRequest
from .services import assign_gardener_to_visit


def visit_request_view(request):
    """Vista pública: formulario para solicitar una visita."""
    if request.method == 'POST':
        form = VisitRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Tu solicitud de visita ha sido enviada correctamente.',
            )
            return redirect('visits:visit_request_success')
    else:
        form = VisitRequestForm()

    return render(request, 'visits/visit_request_form.html', {
        'form': form,
    })


def visit_request_success(request):
    """Vista pública: página de confirmación tras enviar la solicitud."""
    return render(request, 'visits/visit_request_success.html')


@login_required
def company_dashboard(request):
    """Vista interna: panel de la empresa con listado de visitas y estadísticas."""
    visits = VisitRequest.objects.select_related(
        'service_type', 'gardener',
    )

    # Filtros
    status_filter = request.GET.get('status', '')
    service_filter = request.GET.get('service_type', '')

    if status_filter:
        visits = visits.filter(status=status_filter)
    if service_filter:
        visits = visits.filter(service_type_id=service_filter)

    # Estadísticas (sobre el total, no filtradas)
    all_visits = VisitRequest.objects.all()
    stats = {
        'total': all_visits.count(),
        'pendientes': all_visits.filter(status=VisitRequest.Status.PENDIENTE).count(),
        'asignadas': all_visits.filter(status=VisitRequest.Status.ASIGNADA).count(),
        'confirmadas': all_visits.filter(status=VisitRequest.Status.CONFIRMADA).count(),
    }

    # Datos para el mapa: solo visitas con coordenadas
    visits_with_coords = visits.filter(
        latitude__isnull=False,
        longitude__isnull=False,
    )
    map_data = json.dumps([
        {
            'lat': str(v.latitude),
            'lng': str(v.longitude),
            'client': v.client_name,
            'address': v.address,
            'service': v.service_type.name,
            'status': v.get_status_display(),
            'date': v.preferred_date.isoformat(),
        }
        for v in visits_with_coords
    ])

    # Formulario de asignación
    assign_form = AssignGardenerForm()

    # Opciones de filtro
    service_types = ServiceType.objects.filter(is_active=True)
    status_choices = VisitRequest.Status.choices

    return render(request, 'visits/company_dashboard.html', {
        'visits': visits,
        'stats': stats,
        'map_data': map_data,
        'assign_form': assign_form,
        'service_types': service_types,
        'status_choices': status_choices,
        'current_status': status_filter,
        'current_service': service_filter,
    })


@login_required
@require_POST
def assign_gardener(request, pk):
    """Vista interna: asigna un jardinero a una solicitud de visita."""
    visit = get_object_or_404(VisitRequest, pk=pk)
    form = AssignGardenerForm(request.POST)

    if form.is_valid():
        gardener = form.cleaned_data['gardener']
        try:
            assign_gardener_to_visit(visit, gardener)
            messages.success(
                request,
                f'{gardener} ha sido asignado/a a la visita de {visit.client_name}.',
            )
        except ValidationError as e:
            messages.error(request, e.message)
    else:
        messages.error(request, 'Debes seleccionar un jardinero válido.')

    return redirect('visits:company_dashboard')


def visit_confirm(request, token):
    """
    Vista pública: el cliente confirma la visita usando su token único.
    GET muestra los detalles. POST confirma.
    """
    visit = get_object_or_404(VisitRequest, confirmation_token=token)

    if request.method == 'POST':
        if visit.status == VisitRequest.Status.ASIGNADA:
            visit.status = VisitRequest.Status.CONFIRMADA
            visit.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Tu visita ha sido confirmada exitosamente.')
        elif visit.status == VisitRequest.Status.CONFIRMADA:
            messages.info(request, 'Esta visita ya fue confirmada anteriormente.')
        elif visit.status == VisitRequest.Status.CANCELADA:
            messages.warning(request, 'Esta visita fue cancelada y no puede confirmarse.')
        else:
            messages.warning(
                request,
                'Esta visita aún no tiene un jardinero asignado. '
                'Te contactaremos cuando esté lista para confirmar.',
            )
        return redirect('visits:visit_confirm', token=token)

    return render(request, 'visits/visit_confirm.html', {
        'visit': visit,
    })


def visit_cancel(request, token):
    """
    Vista pública: el cliente cancela la visita usando su token único.
    POST cancela la visita.
    """
    visit = get_object_or_404(VisitRequest, confirmation_token=token)

    if request.method == 'POST':
        if visit.status in [VisitRequest.Status.PENDIENTE, VisitRequest.Status.ASIGNADA]:
            visit.status = VisitRequest.Status.CANCELADA
            visit.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Tu visita ha sido cancelada.')
        elif visit.status == VisitRequest.Status.CANCELADA:
            messages.info(request, 'Esta visita ya fue cancelada anteriormente.')
        elif visit.status == VisitRequest.Status.CONFIRMADA:
            visit.status = VisitRequest.Status.CANCELADA
            visit.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Tu visita confirmada ha sido cancelada.')
        return redirect('visits:visit_confirm', token=token)

    return redirect('visits:visit_confirm', token=token)


@require_POST
def logout_view(request):
    auth_logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('visits:visit_request')


@login_required
def documentation(request):
    stats = {
        'total_visits': VisitRequest.objects.count(),
        'total_gardeners': Gardener.objects.count(),
        'total_services': ServiceType.objects.count(),
    }
    return render(request, 'visits/documentation.html', {
        'stats': stats,
    })
