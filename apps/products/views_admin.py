from django.urls import reverse
from django.views.generic import CreateView, UpdateView, DeleteView

from apps.audit.models import AuditLog
from apps.stores.mixins import ManagerRequiredMixin, OwnerRequiredMixin, RoleContextMixin
from .forms import ProductForm
from .models import Product


class ProductCreateView(RoleContextMixin, ManagerRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "stores/dashboard/product_form.html"

    def get_success_url(self):
        return reverse("stores:product_list", kwargs={"store_id": self.store_id})

    def form_valid(self, form):
        form.instance.store = self.get_store()
        AuditLog.objects.create(
            user=self.request.user,
            store=self.get_store(),
            action="create",
            details=f"Producto creado: {form.instance.name}",
            ip_address=self.request.META.get("REMOTE_ADDR"),
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["store"] = self.get_store()
        return context


class ProductUpdateView(RoleContextMixin, ManagerRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "stores/dashboard/product_form.html"

    def get_success_url(self):
        return reverse("stores:product_list", kwargs={"store_id": self.store_id})

    def get_queryset(self):
        return Product.objects.filter(store=self.get_store())

    def form_valid(self, form):
        AuditLog.objects.create(
            user=self.request.user,
            store=self.get_store(),
            action="update",
            details=f"Producto actualizado: {form.instance.name}",
            ip_address=self.request.META.get("REMOTE_ADDR"),
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["store"] = self.get_store()
        return context


class ProductDeleteView(RoleContextMixin, OwnerRequiredMixin, DeleteView):
    model = Product
    template_name = "stores/dashboard/product_confirm_delete.html"

    def get_success_url(self):
        return reverse("stores:product_list", kwargs={"store_id": self.store_id})

    def get_queryset(self):
        return Product.objects.filter(store=self.get_store())

    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        AuditLog.objects.create(
            user=self.request.user,
            store=self.get_store(),
            action="delete",
            details=f"Producto eliminado: {product.name}",
            ip_address=self.request.META.get("REMOTE_ADDR"),
        )
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["store"] = self.get_store()
        return context
