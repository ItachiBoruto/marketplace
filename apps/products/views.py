from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from .models import Product
from .serializers import ProductSerializer
from apps.stores.models import Store


# ===== PÁGINA PRINCIPAL (PROTEGIDA) =====
@login_required(login_url='login')
def product_list(request):
    """Página principal: muestra todos los productos disponibles (solo para usuarios autenticados)."""
    products = Product.objects.filter(is_available=True).select_related('store')
    
    # Búsqueda
    q = request.GET.get('q')
    if q:
        products = products.filter(
            Q(name__icontains=q) |
            Q(keywords__icontains=q)
        )
    
    # Filtro por comercio
    store_id = request.GET.get('store')
    if store_id:
        products = products.filter(store_id=store_id)
    
    # Filtro por categoría
    category = request.GET.get('category')
    if category:
        products = products.filter(name__icontains=category)
    
    # Orden
    sort = request.GET.get('sort')
    if sort == 'price':
        products = products.order_by('price')
    elif sort == '-price':
        products = products.order_by('-price')
    else:
        products = products.order_by('name')
    
    stores = Store.objects.filter(is_active=True)
    categories = Product.objects.filter(is_available=True).values_list('name', flat=True).distinct()
    
    context = {
        'products': products,
        'stores': stores,
        'categories': categories,
    }
    return render(request, 'products/list.html', context)


# ===== DETALLE DE PRODUCTO (PROTEGIDO) =====
@login_required(login_url='login')
def product_detail(request, product_id):
    """Muestra el detalle de un producto específico."""
    product = get_object_or_404(Product, id=product_id, is_available=True)
    return render(request, 'products/detail.html', {'product': product})


# ===== API PARA SCROLL INFINITO =====
class ProductPagination(PageNumberPagination):
    page_size = 12


class ProductListAPI(APIView):
    def get(self, request):
        products = Product.objects.filter(is_available=True).select_related('store')
        
        search = request.GET.get('search', '')
        if search:
            products = products.filter(
                Q(name__icontains=search) |
                Q(keywords__icontains=search)
            )
        
        store_id = request.GET.get('store')
        if store_id:
            products = products.filter(store_id=store_id)
        
        category = request.GET.get('category', '')
        if category:
            products = products.filter(name__icontains=category)
        
        sort = request.GET.get('sort')
        if sort == 'price':
            products = products.order_by('price')
        elif sort == '-price':
            products = products.order_by('-price')
        else:
            products = products.order_by('name')
        
        paginator = ProductPagination()
        result_page = paginator.paginate_queryset(products, request)
        serializer = ProductSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class StoreProductListAPI(APIView):
    def get(self, request):
        store_id = request.GET.get('store')
        if not store_id:
            return Response({"error": "Store ID required"}, status=400)
        
        products = Product.objects.filter(store_id=store_id, is_available=True)
        
        search = request.GET.get('search', '')
        if search:
            products = products.filter(
                Q(name__icontains=search) |
                Q(keywords__icontains=search)
            )
        
        sort = request.GET.get('sort', 'name')
        if sort == 'name':
            products = products.order_by('name')
        elif sort == 'price':
            products = products.order_by('price')
        elif sort == '-price':
            products = products.order_by('-price')
        elif sort == 'created_at':
            products = products.order_by('-created_at')
        
        paginator = ProductPagination()
        result_page = paginator.paginate_queryset(products, request)
        serializer = ProductSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)