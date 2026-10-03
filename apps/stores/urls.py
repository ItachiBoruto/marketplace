from . import views_claims
from django.urls import path

from apps.inventory.views_admin import MovementListView, StockAdjustView
from apps.products.views_admin import (
    ProductCreateView,
    ProductDeleteView,
    ProductUpdateView,
)

from . import views, views_analytics, views_orders, views_payments, views_schedule, views_users

app_name = "stores"

urlpatterns = [
    # Páginas públicas
    path("", views.store_list, name="list"),
    path("<int:store_id>/", views.store_detail, name="detail"),

    # Dashboard del vendedor
    path("dashboard/<int:store_id>/", views.DashboardView.as_view(), name="dashboard"),
    path("dashboard/<int:store_id>/analytics/", views_analytics.AnalyticsView.as_view(), name="analytics"),
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
    path("dashboard/<int:store_id>/orders/<int:order_id>/approve/", views_orders.order_confirm_payment, name="order_confirm_payment"),
    path("dashboard/<int:store_id>/orders/<int:order_id>/reject/", views_orders.order_reject_payment, name="order_reject_payment"),
    path("dashboard/<int:store_id>/orders/<int:order_id>/ship/", views_orders.order_mark_shipped, name="order_mark_shipped"),
    path("dashboard/<int:store_id>/orders/<int:order_id>/deliver/", views_orders.order_mark_delivered, name="order_mark_delivered"),
    # ===== Sistema de reclamos =====
    path("dashboard/<int:store_id>/claims/", views_claims.StoreClaimsListView.as_view(), name="store_claims_list"),
    path("dashboard/<int:store_id>/claims/<int:claim_id>/", views_claims.store_claim_detail, name="store_claim_detail"),
    path("dashboard/<int:store_id>/claims/<int:claim_id>/message/", views_claims.store_claim_add_message, name="store_claim_add_message"),
    path("dashboard/<int:store_id>/claims/<int:claim_id>/resolve/", views_claims.store_claim_resolve, name="store_claim_resolve"),
    path("dashboard/<int:store_id>/claims/<int:claim_id>/escalate/", views_claims.store_claim_escalate, name="store_claim_escalate"),
    # Usuarios del comercio (solo superuser)
    path("dashboard/<int:store_id>/users/", views_users.StoreUsersView.as_view(), name="users"),
    path("dashboard/<int:store_id>/users/search/", views_users.search_users, name="users_search"),
    path("dashboard/<int:store_id>/users/add/", views_users.add_store_user, name="users_add"),
    path("dashboard/<int:store_id>/users/<int:permission_id>/change-role/", views_users.change_user_role, name="users_change_role"),
    path("dashboard/<int:store_id>/users/<int:permission_id>/remove/", views_users.remove_store_user, name="users_remove"),
    # Solicitudes de cambio de datos bancarios (owner)
    path("dashboard/<int:store_id>/payment-change/", views_payments.request_payment_change, name="payment_change_request"),
    path("dashboard/<int:store_id>/payment-change/status/", views_payments.payment_change_status, name="payment_change_status"),
    # Horario del comercio
    path("dashboard/<int:store_id>/schedule/", views_schedule.ScheduleConfigView.as_view(), name="schedule_config"),
    path("dashboard/<int:store_id>/schedule/toggle/<int:day>/", views_schedule.toggle_day, name="schedule_toggle_day"),
]