"""Vistas para gestionar el horario de atencion de un comercio."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render

from .models import Store, StoreSchedule
from .forms import ScheduleForm
from .mixins import OwnerRequiredMixin, RoleContextMixin
from django.views import View


class ScheduleConfigView(RoleContextMixin, OwnerRequiredMixin, View):
    """Vista para configurar el horario semanal completo."""

    def get(self, request, *args, **kwargs):
        store = self.get_store()
        if not store:
            raise Http404()

        # Asegurar que existan los 7 dias (o crearlos vacios)
        existing = {s.day_of_week: s for s in store.schedules.all()}
        schedules = []
        for day_num, day_name in StoreSchedule.DAY_CHOICES:
            sched = existing.get(day_num)
            if not sched:
                sched = StoreSchedule(store=store, day_of_week=day_num)
            schedules.append(sched)

        return render(request, 'stores/dashboard/schedule.html', {
            'store': store,
            'schedules': schedules,
            'day_names': StoreSchedule.DAY_CHOICES,
        })

    def post(self, request, *args, **kwargs):
        store = self.get_store()
        if not store:
            raise Http404()

        # === Toggle 24/7 ===
        has_24_7 = request.POST.get('has_24_7_schedule') == 'on'
        if store.has_24_7_schedule != has_24_7:
            store.has_24_7_schedule = has_24_7
            store.save(update_fields=['has_24_7_schedule'])

        # Procesar los 7 dias
        errors = []
        for day_num, day_name in StoreSchedule.DAY_CHOICES:
            prefix = f"day_{day_num}_"
            is_closed = request.POST.get(f"{prefix}is_closed") == "on"

            sched, _ = StoreSchedule.objects.get_or_create(
                store=store, day_of_week=day_num
            )
            sched.is_closed = is_closed

            if is_closed:
                sched.pickup_open = None
                sched.pickup_close = None
                sched.delivery_open = None
                sched.delivery_close = None
            else:
                p_open = request.POST.get(f"{prefix}pickup_open", "").strip()
                p_close = request.POST.get(f"{prefix}pickup_close", "").strip()
                d_open = request.POST.get(f"{prefix}delivery_open", "").strip()
                d_close = request.POST.get(f"{prefix}delivery_close", "").strip()

                sched.pickup_open = p_open or None
                sched.pickup_close = p_close or None
                sched.delivery_open = d_open or None
                sched.delivery_close = d_close or None

            try:
                sched.full_clean()
                sched.save()
            except Exception as e:
                errors.append(f"{day_name}: {e}")

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            messages.success(request, 'Horario actualizado correctamente.')

        return redirect('stores:schedule_config', store_id=store.id)


@login_required(login_url='login')
def toggle_day(request, store_id, day):
    """Marca o desmarca un dia como cerrado (accion rapida AJAX)."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Metodo no permitido')

    store = get_object_or_404(Store, id=store_id)

    # Verificar que sea owner o superuser
    is_owner = request.user.is_superuser or store.user_permissions.filter(
        user=request.user, role='owner', is_active=True
    ).exists()
    if not is_owner:
        raise Http404()

    if day < 0 or day > 6:
        raise Http404()

    sched, _ = StoreSchedule.objects.get_or_create(store=store, day_of_week=day)
    sched.is_closed = not sched.is_closed
    sched.save(update_fields=['is_closed'])

    return redirect('stores:schedule_config', store_id=store.id)
