from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404

from .models import Store, StoreUserPermission


class StoreOwnerRequiredMixin(LoginRequiredMixin):
    """
    Mixin base:
      1. Exige autenticación (redirige al login si no está autenticado).
      2. Verifica que el usuario tenga algún permiso sobre el comercio.
      3. Verifica que su rol esté dentro de `allowed_roles`.
    """
    allowed_roles = ("owner", "manager", "viewer")

    def dispatch(self, request, *args, **kwargs):
        # 1. Autenticación
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # 2. Obtener store_id de la URL
        store_id = kwargs.get("store_id")
        if not store_id:
            raise Http404("No se especificó un comercio.")
        self.store_id = store_id

        # 3. Superuser bypass o verificar permiso
        if request.user.is_superuser:
            self.user_role = "owner"
        else:
            perm = (
                StoreUserPermission.objects
                .filter(user=request.user, store_id=store_id, is_active=True)
                .only("role")
                .first()
            )
            if not perm:
                raise Http404("No tienes permisos para gestionar este comercio.")
            self.user_role = perm.role

        # 4. Verificar que el rol esté permitido
        if self.user_role not in self.allowed_roles:
            raise Http404("No tienes permisos suficientes.")

        # 5. Ejecutar la vista
        return super().dispatch(request, *args, **kwargs)

    def get_store(self):
        try:
            return Store.objects.get(id=self.store_id)
        except Store.DoesNotExist:
            return None

    def get_user_role(self):
        return getattr(self, "user_role", None)


class ManagerRequiredMixin(StoreOwnerRequiredMixin):
    """Requiere rol owner o manager."""
    allowed_roles = ("owner", "manager")


class OwnerRequiredMixin(StoreOwnerRequiredMixin):
    """Requiere rol owner."""
    allowed_roles = ("owner",)


class RoleContextMixin:
    """Inyecta `user_role` en el contexto del template."""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_role"] = self.get_user_role()
        return context
