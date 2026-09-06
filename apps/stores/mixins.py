from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from .models import Store, StoreUserPermission

class StoreOwnerRequiredMixin(LoginRequiredMixin):
    """Mixin base: verifica que el usuario tenga algún permiso sobre el comercio."""
    
    def dispatch(self, request, *args, **kwargs):
        store_id = kwargs.get('store_id')
        if not store_id:
            raise Http404("No se especificó un comercio.")
        
        self.store_id = store_id
        
        # Superusuario tiene acceso total
        if request.user.is_superuser:
            self.user_role = 'owner'
            return super().dispatch(request, *args, **kwargs)
        
        # Verificar si tiene permiso activo
        perm = StoreUserPermission.objects.filter(
            user=request.user,
            store_id=store_id,
            is_active=True
        ).first()
        if not perm:
            raise Http404("No tienes permisos para gestionar este comercio.")
        
        self.user_role = perm.role
        return super().dispatch(request, *args, **kwargs)
    
    def get_store(self):
        try:
            return Store.objects.get(id=self.store_id)
        except Store.DoesNotExist:
            return None
    
    def get_user_role(self):
        return getattr(self, 'user_role', None)

class ManagerRequiredMixin(StoreOwnerRequiredMixin):
    """Mixin para vistas que requieren al menos rol 'manager'."""
    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        if request.user.is_superuser:
            return result
        if self.get_user_role() not in ['owner', 'manager']:
            raise Http404("No tienes permisos suficientes.")
        return result

class OwnerRequiredMixin(StoreOwnerRequiredMixin):
    """Mixin para vistas que requieren rol 'owner'."""
    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        if request.user.is_superuser:
            return result
        if self.get_user_role() != 'owner':
            raise Http404("Solo el propietario puede realizar esta acción.")
        return result

class RoleContextMixin:
    """Agrega el rol del usuario al contexto de la vista."""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_role'] = self.get_user_role()
        return context