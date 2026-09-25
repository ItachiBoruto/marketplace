from django.contrib import messages
from django.urls import reverse
from django.views.generic import ListView, UpdateView

from apps.products.models import Product
from apps.stores.mixins import ManagerRequiredMixin, OwnerRequiredMixin, RoleContextMixin
from .forms import StockAdjustForm
from .models import StockMovement

class StockAdjustView(RoleContextMixin, ManagerRequiredMixin, UpdateView):
    model = Product
    form_class = StockAdjustForm
    template_name = "stores/dashboard/stock_adjust.html"

    def get_success_url(self):
        return reverse("stores:product_list", kwargs={"store_id": self.store_id})

    def get_queryset(self):
        return Product.objects.filter(store=self.get_store())

    def form_valid(self, form):
        product = self.get_object()
        old_stock = product.stock
        new_stock = form.cleaned_data["stock"]
        quantity_change = new_stock - old_stock
        if quantity_change != 0:
            StockMovement.objects.create(
                store=product.store,
                product=product,
                quantity_change=quantity_change,
                movement_type="ADJ",
                created_by=self.request.user.username,
                order_reference="Ajuste manual desde dashboard",
            )
            messages.success(self.request, f"Stock actualizado de {old_stock} a {new_stock}.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["store"] = self.get_store()
        return context

class MovementListView(RoleContextMixin, OwnerRequiredMixin, ListView):
    model = StockMovement
    template_name = "stores/dashboard/movements.html"
    context_object_name = "movements"
    paginate_by = 20

    def get_queryset(self):
        store = self.get_store()
        return (
            StockMovement.objects
            .filter(store=store)
            .select_related("product", "product__category")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["store"] = self.get_store()
        return context
