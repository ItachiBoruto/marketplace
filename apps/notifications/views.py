from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from .models import Notification


@login_required(login_url="login")
def dropdown(request):
    """HTML parcial con las ultimas notificaciones (para el dropdown del header)."""
    # Sin leer primero, luego las leidas, cada grupo por fecha descendente
    notifications = request.user.notifications.order_by('is_read', '-created_at')[:8]
    unread = request.user.notifications.filter(is_read=False).count()
    html = render_to_string(
        "notifications/_dropdown.html",
        {"notifications": notifications, "unread_count": unread},
        request=request,
    )
    return JsonResponse({"html": html, "unread_count": unread})


@login_required(login_url="login")
def unread_count(request):
    """Devuelve solo el numero de notificaciones sin leer."""
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({"unread_count": count})


@login_required(login_url="login")
def notification_list(request):
    """Pagina con todas las notificaciones."""
    qs = request.user.notifications.all()
    unread_only = request.GET.get("unread") == "1"
    if unread_only:
        qs = qs.filter(is_read=False)
    # Sin leer primero, luego las leidas, cada grupo por fecha descendente
    qs = qs.order_by('is_read', '-created_at')
    return render(request, "notifications/list.html", {
        "notifications": qs[:100],
        "unread_count": request.user.notifications.filter(is_read=False).count(),
        "unread_only": unread_only,
    })


@login_required(login_url="login")
@require_POST
def mark_read(request, notification_id):
    """Marca una notificacion como leida."""
    n = get_object_or_404(Notification, id=notification_id, user=request.user)
    n.is_read = True
    n.save(update_fields=["is_read"])
    if n.link:
        return redirect(n.link)
    return redirect("notifications:list")


@login_required(login_url="login")
@require_POST
def mark_all_read(request):
    """Marca todas como leidas."""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect("notifications:list")
