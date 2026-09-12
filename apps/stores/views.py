from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, UpdateView
from django.urls import reverse

# Modelos
from .models import Store
from apps.products.models import Product
from apps.inventory.models import StockMovement

# Mixins y formularios
from .mixins import StoreOwnerRequiredMixin, ManagerRequiredMixin, OwnerRequiredMixin, RoleContextMixin
from .forms import StoreProfileForm

# ===================== VISTAS PÚBLICAS =====================

def store_list(request):
    stores = Store.objects.filter(is_active=True)
    return render(request, 'stores/list.html', {'stores': stores})

def store_detail(request, store_id):
    store = get_object_or_404(Store, id=store_id, is_active=True)
    products = Product.objects.filter(store=store, is_available=True)
    return render(request, 'stores/detail.html', {
        'store': store,
        'products': products,
    })

# ===================== REGISTRO DE USUARIOS =====================

# ===================== DASHBOARD DEL VENDEDOR =====================

class DashboardView(RoleContextMixin, StoreOwnerRequiredMixin, ListView):
    model = Product
    template_name = 'stores/dashboard/index.html'
    context_object_name = 'products'

    def get_queryset(self):
        store = self.get_store()
        return Product.objects.filter(store=store, is_available=True)[:5]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store = self.get_store()
        context['store'] = store
        context['total_products'] = Product.objects.filter(store=store).count()
        context['low_stock'] = Product.objects.filter(store=store, stock__lt=5).count()
        context['recent_movements'] = StockMovement.objects.filter(store=store)[:10]
        return context

class ProductListView(RoleContextMixin, ManagerRequiredMixin, ListView):
    model = Product
    template_name = 'stores/dashboard/product_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        store = self.get_store()
        qs = Product.objects.filter(store=store)
        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(name__icontains=search)
        return qs.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.get_store()
        return context

class StoreProfileView(RoleContextMixin, OwnerRequiredMixin, UpdateView):
    model = Store
    form_class = StoreProfileForm
    template_name = 'stores/dashboard/store_edit.html'

    def get_object(self):
        return self.get_store()

    def get_success_url(self):
        return reverse('stores:dashboard', kwargs={'store_id': self.store_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.get_store()
        return context
