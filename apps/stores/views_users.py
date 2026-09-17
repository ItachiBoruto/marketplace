"""Vistas para gestionar usuarios de un comercio. Solo superuser."""
from django.contrib import messages
from django.contrib.auth.models import User
from django.views import View
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .mixins import RoleContextMixin, SuperuserRequiredMixin
from .models import Store, StoreUserPermission


ROLE_LABELS = dict(StoreUserPermission.ROLE_CHOICES)


def _is_superuser(request):
    return request.user.is_authenticated and request.user.is_superuser


def _user_payload(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email or "",
    }


class StoreUsersView(RoleContextMixin, SuperuserRequiredMixin, View):
    """Lista y gestiona usuarios con permiso sobre el comercio. Solo superuser."""

    def get(self, request, *args, **kwargs):
        store = self.get_store()
        if not store:
            raise Http404("Comercio no encontrado.")

        permissions = StoreUserPermission.objects.filter(
            store=store
        ).select_related("user").order_by("role", "user__username")

        return render(request, "stores/dashboard/users.html", {
            "store": store,
            "permissions": permissions,
            "role_labels": ROLE_LABELS,
        })


@login_required(login_url="login")
def search_users(request, store_id):
    if not _is_superuser(request):
        return JsonResponse({"error": "forbidden"}, status=403)
    if request.headers.get("X-Requested-With") != "XMLHttpRequest":
        raise Http404()

    store = get_object_or_404(Store, id=store_id)
    query = request.GET.get("q", "").strip()
    if len(query) < 2:
        return JsonResponse({"results": []})

    existing_ids = set(
        StoreUserPermission.objects.filter(store=store).values_list("user_id", flat=True)
    )
    users = User.objects.filter(
        Q(username__icontains=query) | Q(email__icontains=query)
    ).exclude(id__in=existing_ids).order_by("username")[:10]

    return JsonResponse({"results": [_user_payload(u) for u in users]})


@login_required(login_url="login")
def add_store_user(request, store_id):
    if not _is_superuser(request):
        raise Http404()
    if request.method != "POST":
        return HttpResponseBadRequest("Metodo no permitido")

    store = get_object_or_404(Store, id=store_id)
    user_id = request.POST.get("user_id")
    role = request.POST.get("role", "manager")

    if role not in dict(StoreUserPermission.ROLE_CHOICES):
        messages.error(request, "Rol inválido.")
        return redirect("stores:users", store_id=store.id)

    target_user = get_object_or_404(User, id=user_id)

    perm, created = StoreUserPermission.objects.get_or_create(
        user=target_user, store=store,
        defaults={"role": role, "is_active": True}
    )
    if not created:
        perm.role = role
        perm.is_active = True
        perm.save(update_fields=["role", "is_active"])

    messages.success(
        request,
        f'Usuario {target_user.username} asignado como {ROLE_LABELS[role]} en {store.name}.'
    )
    return redirect("stores:users", store_id=store.id)


@login_required(login_url="login")
def change_user_role(request, store_id, permission_id):
    if not _is_superuser(request):
        raise Http404()
    if request.method != "POST":
        return HttpResponseBadRequest("Metodo no permitido")

    store = get_object_or_404(Store, id=store_id)
    perm = get_object_or_404(StoreUserPermission, id=permission_id, store=store)
    new_role = request.POST.get("role")

    if new_role not in dict(StoreUserPermission.ROLE_CHOICES):
        messages.error(request, "Rol inválido.")
        return redirect("stores:users", store_id=store.id)

    if perm.role == "owner" and new_role != "owner":
        owners_count = StoreUserPermission.objects.filter(
            store=store, role="owner", is_active=True
        ).count()
        if owners_count <= 1:
            messages.error(
                request,
                "No puedes degradar al último owner. Asigna otro owner primero."
            )
            return redirect("stores:users", store_id=store.id)

    perm.role = new_role
    perm.save(update_fields=["role"])
    messages.success(
        request,
        f'Rol de {perm.user.username} cambiado a {ROLE_LABELS[new_role]}.'
    )
    return redirect("stores:users", store_id=store.id)


@login_required(login_url="login")
def remove_store_user(request, store_id, permission_id):
    if not _is_superuser(request):
        raise Http404()
    if request.method != "POST":
        return HttpResponseBadRequest("Metodo no permitido")

    store = get_object_or_404(Store, id=store_id)
    perm = get_object_or_404(StoreUserPermission, id=permission_id, store=store)

    if perm.role == "owner":
        owners_count = StoreUserPermission.objects.filter(
            store=store, role="owner", is_active=True
        ).count()
        if owners_count <= 1:
            messages.error(request, "No puedes eliminar al último owner del comercio.")
            return redirect("stores:users", store_id=store.id)

    username = perm.user.username
    perm.delete()
    messages.success(request, f"Acceso de {username} eliminado.")
    return redirect("stores:users", store_id=store.id)
