from django.urls import path
from . import views

app_name = 'stores'

urlpatterns = [
    # Páginas públicas
    path('', views.store_list, name='list'),
    path('<int:store_id>/', views.store_detail, name='detail'),
    path('product-detail/<int:product_id>/', views.product_detail_ajax, name='product_detail_ajax'),

    # Registro de usuarios
    path('register/', views.register, name='register'),  # <--- Esta línea es la clave

    # Dashboard del vendedor
    path('dashboard/<int:store_id>/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/<int:store_id>/products/', views.ProductListView.as_view(), name='product_list'),
    path('dashboard/<int:store_id>/products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('dashboard/<int:store_id>/products/<int:pk>/update/', views.ProductUpdateView.as_view(), name='product_update'),
    path('dashboard/<int:store_id>/products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    path('dashboard/<int:store_id>/products/<int:pk>/stock/', views.StockAdjustView.as_view(), name='stock_adjust'),
    path('dashboard/<int:store_id>/movements/', views.MovementListView.as_view(), name='movements'),
    path('dashboard/<int:store_id>/profile/', views.StoreProfileView.as_view(), name='store_edit'),
]