from django.urls import path

from apps.inventory.views_admin import MovementListView, StockAdjustView
from apps.products.views_admin import (
    ProductCreateView,
    ProductDeleteView,
    ProductUpdateView,
)

from . import views, views_orders, views_users

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
    # Pedidos del comercio
    path("dashboard/<int:store_id>/orders/", views_orders.StoreOrdersView.as_view(), name="orders"),
    path("dashboard/<int:store_id>/orders/<int:order_id>/", views_orders.StoreOrderDetailView.as_view(), name="order_detail"),
    path("dashboard/<int:store_id>/orders/<int:order_id>/items/<int:item_id>/approve/", views_orders.approve_order_item, name="order_item_approve"),
    path("dashboard/<int:store_id>/orders/<int:order_id>/items/<int:item_id>/reject/", views_orders.reject_order_item_view, name="order_item_reject"),
    path("dashboard/<int:store_id>/orders/<int:order_id>/items/<int:item_id>/ship/", views_orders.mark_item_shipped, name="order_item_ship"),
    # Usuarios del comercio (solo superuser)
    path("dashboard/<int:store_id>/users/", views_users.StoreUsersView.as_view(), name="users"),
    path("dashboard/<int:store_id>/users/search/", views_users.search_users, name="users_search"),
    path("dashboard/<int:store_id>/users/add/", views_users.add_store_user, name="users_add"),
    path("dashboard/<int:store_id>/users/<int:permission_id>/change-role/", views_users.change_user_role, name="users_change_role"),
    path("dashboard/<int:store_id>/users/<int:permission_id>/remove/", views_users.remove_store_user, name="users_remove"),
]
