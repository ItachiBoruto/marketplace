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
    from .schedule_utils import get_store_status

    from apps.products.models import Category

    store = get_object_or_404(Store, id=store_id, is_active=True)
    products = Product.objects.filter(
        store=store, is_available=True
    ).select_related('store', 'category')
    store_status = get_store_status(store)

    # Categorias que TIENEN al menos un producto disponible en este comercio
    store_categories = Category.objects.filter(
        products__store=store,
        products__is_available=True,
        is_active=True
    ).distinct().order_by('order', 'name')

    # Meta tags para compartir
    og_title = f"{store.name} - Mi Marketplace"
    og_description = store.description[:150] if store.description else f"Productos de {store.name}"
    og_image = store.logo.url if store.logo else None

    return render(request, 'stores/detail.html', {
        'store': store,
        'products': products,
        'store_categories': store_categories,
        'store_status': store_status,
        'og_title': og_title,
        'og_description': og_description,
        'og_image': og_image,
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
        from django.db.models import Sum
        from django.utils import timezone
        from datetime import timedelta

        context = super().get_context_data(**kwargs)
        store = self.get_store()
        context['store'] = store

        products = Product.objects.filter(store=store)
        context['total_products'] = products.count()
        context['low_stock'] = products.filter(stock__lt=5, is_available=True).count()

        # Movimientos separados
        base = StockMovement.objects.filter(store=store).select_related('product')
        context['recent_sales'] = base.filter(movement_type='SALE')[:8]
        context['recent_returns'] = base.filter(movement_type='RETURN')[:8]

        # Resumen de ventas
        today = timezone.now().date()
        start_of_day = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.min.time())
        )
        start_of_month = start_of_day.replace(day=1)

        sales_today = base.filter(
            movement_type='SALE', created_at__gte=start_of_day
        )
        sales_month = base.filter(
            movement_type='SALE', created_at__gte=start_of_month
        )

        context['sales_today_count'] = abs(
            sales_today.aggregate(s=Sum('quantity_change'))['s'] or 0
        )
        context['sales_month_count'] = abs(
            sales_month.aggregate(s=Sum('quantity_change'))['s'] or 0
        )
        context['returns_month_count'] = abs(
            base.filter(
                movement_type='RETURN', created_at__gte=start_of_month
            ).aggregate(s=Sum('quantity_change'))['s'] or 0
        )

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
