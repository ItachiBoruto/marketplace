from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='list'),
    path('product/<int:product_id>/', views.product_detail, name='detail'),
    path('api/products/', views.ProductListAPI.as_view(), name='api_products'),
    path('api/store-products/', views.StoreProductListAPI.as_view(), name='api_store_products'),
]