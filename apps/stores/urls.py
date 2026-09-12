from django.urls import path

from apps.inventory.views_admin import MovementListView, StockAdjustView
from apps.products.views_admin import (
    ProductCreateView,
    ProductDeleteView,
    ProductUpdateView,
)

from . import views

app_name = "stores"

urlpatterns = [
    # Páginas públicas
    path("", views.store_list, name="list"),
    path("<int:store_id>/", views.store_detail, name="detail"),

    # Dashboard del vendedor
    path("dashboard/<int:store_id>/", views.DashboardView.as_view(), name="dashboard"),
    path("dashboard/<int:store_id>/products/", views.ProductListView.as_view(), name="product_list"),
    path("dashboard/<int:store_id>/products/create/", ProductCreateView.as_view(), name="product_create"),
    path("dashboard/<int:store_id>/products/<int:pk>/update/", ProductUpdateView.as_view(), name="product_update"),
    path("dashboard/<int:store_id>/products/<int:pk>/delete/", ProductDeleteView.as_view(), name="product_delete"),
    path("dashboard/<int:store_id>/products/<int:pk>/stock/", StockAdjustView.as_view(), name="stock_adjust"),
    path("dashboard/<int:store_id>/movements/", MovementListView.as_view(), name="movements"),
    path("dashboard/<int:store_id>/profile/", views.StoreProfileView.as_view(), name="store_edit"),
]
