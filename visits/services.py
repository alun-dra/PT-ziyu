from django.core.exceptions import ValidationError

from .models import VisitRequest


def check_gardener_availability(gardener, date, time_start, time_end, exclude_visit_id=None):
    """
    Verifica si un jardinero está disponible en la fecha y rango horario indicados.

    Retorna True si el jardinero NO tiene visitas superpuestas (está disponible).
    Retorna False si hay superposición con otra visita asignada o confirmada.
    """
    overlapping = VisitRequest.objects.filter(
        gardener=gardener,
        preferred_date=date,
        status__in=[
            VisitRequest.Status.ASIGNADA,
            VisitRequest.Status.CONFIRMADA,
        ],
    )

    if exclude_visit_id is not None:
        overlapping = overlapping.exclude(pk=exclude_visit_id)

    for visit in overlapping:
        if time_start < visit.preferred_time_end and time_end > visit.preferred_time_start:
            return False

    return True


def assign_gardener_to_visit(visit, gardener):
    """
    Asigna un jardinero a una solicitud de visita.

    Valida la disponibilidad antes de asignar. Cambia el estado a 'asignada'.
    Lanza ValidationError si hay superposición.
    """
    if not check_gardener_availability(
        gardener=gardener,
        date=visit.preferred_date,
        time_start=visit.preferred_time_start,
        time_end=visit.preferred_time_end,
        exclude_visit_id=visit.pk,
    ):
        raise ValidationError(
            f'{gardener} ya tiene una visita asignada en esa fecha y horario.'
        )

    visit.gardener = gardener
    visit.status = VisitRequest.Status.ASIGNADA
    visit.full_clean()
    visit.save(update_fields=['gardener', 'status', 'updated_at'])
    return visit
