from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

# Modelos
from .models import Store, StoreUserPermission
from apps.audit.models import AuditLog
from apps.products.models import Product
from apps.inventory.models import StockMovement

# Mixins y formularios
from .mixins import StoreOwnerRequiredMixin, ManagerRequiredMixin, OwnerRequiredMixin, RoleContextMixin
from .forms import ProductForm, StockAdjustForm, StoreProfileForm, CustomUserCreationForm


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


def product_detail_ajax(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_available=True)
    return render(request, 'stores/_product_detail.html', {'product': product})


# ===================== REGISTRO DE USUARIOS =====================

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Inicia sesión automáticamente
            return redirect('/')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


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


class ProductCreateView(RoleContextMixin, ManagerRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'stores/dashboard/product_form.html'

    def get_success_url(self):
        return reverse('stores:product_list', kwargs={'store_id': self.store_id})

    def form_valid(self, form):
        form.instance.store = self.get_store()
        AuditLog.objects.create(
            user=self.request.user,
            store=self.get_store(),
            action='create',
            details=f'Producto creado: {form.instance.name}',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.get_store()
        return context


class ProductUpdateView(RoleContextMixin, ManagerRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'stores/dashboard/product_form.html'

    def get_success_url(self):
        return reverse('stores:product_list', kwargs={'store_id': self.store_id})

    def get_queryset(self):
        return Product.objects.filter(store=self.get_store())

    def form_valid(self, form):
        AuditLog.objects.create(
            user=self.request.user,
            store=self.get_store(),
            action='update',
            details=f'Producto actualizado: {form.instance.name}',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.get_store()
        return context


class ProductDeleteView(RoleContextMixin, OwnerRequiredMixin, DeleteView):
    model = Product
    template_name = 'stores/dashboard/product_confirm_delete.html'

    def get_success_url(self):
        return reverse('stores:product_list', kwargs={'store_id': self.store_id})

    def get_queryset(self):
        return Product.objects.filter(store=self.get_store())

    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        AuditLog.objects.create(
            user=self.request.user,
            store=self.get_store(),
            action='delete',
            details=f'Producto eliminado: {product.name}',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.get_store()
        return context


class StockAdjustView(RoleContextMixin, ManagerRequiredMixin, UpdateView):
    model = Product
    form_class = StockAdjustForm
    template_name = 'stores/dashboard/stock_adjust.html'

    def get_success_url(self):
        return reverse('stores:product_list', kwargs={'store_id': self.store_id})

    def get_queryset(self):
        return Product.objects.filter(store=self.get_store())

    def form_valid(self, form):
        product = self.get_object()
        old_stock = product.stock
        new_stock = form.cleaned_data['stock']
        quantity_change = new_stock - old_stock
        if quantity_change != 0:
            StockMovement.objects.create(
                store=product.store,
                product=product,
                quantity_change=quantity_change,
                movement_type='ADJ',
                created_by=self.request.user.username,
                order_reference='Ajuste manual desde dashboard'
            )
            AuditLog.objects.create(
                user=self.request.user,
                store=self.get_store(),
                action='stock_adjust',
                details=f'Stock ajustado: {product.name} (cambio: {quantity_change})',
                ip_address=self.request.META.get('REMOTE_ADDR')
            )
            messages.success(self.request, f'Stock actualizado de {old_stock} a {new_stock}.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = self.get_store()
        return context


class MovementListView(RoleContextMixin, OwnerRequiredMixin, ListView):
    model = StockMovement
    template_name = 'stores/dashboard/movements.html'
    context_object_name = 'movements'
    paginate_by = 20

    def get_queryset(self):
        store = self.get_store()
        return StockMovement.objects.filter(store=store).order_by('-created_at')

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