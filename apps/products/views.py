from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from django.db.models import Q
from .models import Product
from .serializers import ProductSerializer
from apps.stores.models import Store


# ===== PÁGINA PRINCIPAL (PROTEGIDA) =====
def product_list(request):
    """Página principal: muestra todos los productos disponibles (solo para usuarios autenticados)."""
    products = Product.objects.filter(is_available=True).select_related('store', 'category')
    
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
    # Categorias reales (modelo Category), no nombres de productos
    from .models import Category
    categories = Category.objects.filter(is_active=True).order_by('order', 'name')

    context = {
        'products': products,
        'stores': stores,
        'categories': categories,
    }
    return render(request, 'products/list.html', context)


# ===== DETALLE DE PRODUCTO (PROTEGIDO) =====
def product_detail(request, product_id):
    """Muestra el detalle del producto + productos similares."""
    product = get_object_or_404(Product, id=product_id, is_available=True)

    # 1. Primero: productos de la misma tienda
    same_store = list(
        Product.objects.filter(store=product.store, is_available=True)
        .exclude(id=product.id)
        .select_related('store')
        .order_by('-created_at')[:6]
    )
    related = same_store

    # 2. Si hay menos de 6, completar con productos de keywords similares
    if len(related) < 6:
        needed = 6 - len(related)
        keywords = [k.strip() for k in (product.keywords or '').split(',') if k.strip()]
        if keywords:
            q = Q()
            for kw in keywords:
                q |= Q(keywords__icontains=kw)
            exclude_ids = [product.id] + [p.id for p in related]
            extra = list(
                Product.objects.filter(q, is_available=True)
                .exclude(id__in=exclude_ids)
                .select_related('store')
                .order_by('-created_at')[:needed]
            )
            related = related + extra

    # Meta tags para compartir
    og_title = f"{product.name} - ${product.price}"
    og_description = f"Vendido por {product.store.name} en Mi Marketplace"
    og_image = product.image.url if product.image else None

    return render(request, 'products/detail.html', {
        'product': product,
        'related_products': related,
        'og_title': og_title,
        'og_description': og_description,
        'og_image': og_image,
        'og_type': 'product',
    })


# ===== API PARA SCROLL INFINITO =====
# ===== THROTTLES PERSONALIZADOS =====
class CatalogAnonThrottle(AnonRateThrottle):
    """Throttle para anonimos en el catalogo (30/min)."""
    scope = 'catalog'


class CatalogUserThrottle(UserRateThrottle):
    """Throttle para usuarios autenticados en el catalogo (120/min)."""
    scope = 'user'


class ProductPagination(PageNumberPagination):
    page_size = 12


class ProductListAPI(APIView):
    throttle_classes = [CatalogAnonThrottle, CatalogUserThrottle]

    def get(self, request):
        products = Product.objects.filter(is_available=True).select_related('store', 'category')
        
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
            products = products.filter(category__slug=category)
        
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
    throttle_classes = [CatalogAnonThrottle, CatalogUserThrottle]

    def get(self, request):
        store_id = request.GET.get('store')
        if not store_id:
            return Response({"error": "Store ID required"}, status=400)
        
        products = Product.objects.filter(
            store_id=store_id, is_available=True
        ).select_related('store', 'category')
        
        search = request.GET.get('search', '')
        if search:
            products = products.filter(
                Q(name__icontains=search) |
                Q(keywords__icontains=search)
            )

        category = request.GET.get('category', '')
        if category:
            products = products.filter(category__slug=category)
        
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

# ===== DETALLE DE PRODUCTO (AJAX, para modales) =====
def product_detail_ajax(request, product_id):
    """Devuelve el HTML parcial del producto para cargar en modal."""
    product = get_object_or_404(Product, id=product_id, is_available=True)
    return render(request, "products/_product_detail.html", {"product": product})

