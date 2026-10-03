from django.urls import path

from apps.stores import views_payments as store_payment_views
from . import views, views_claims, views_panel

app_name = 'orders'

urlpatterns = [
    # ===== Sistema de reclamos (cliente) =====
    path('claim/create/<int:order_id>/', views_claims.claim_create, name='claim_create'),
    path('claim/<int:claim_id>/', views_claims.claim_detail, name='claim_detail'),
    path('claim/<int:claim_id>/message/', views_claims.claim_add_message, name='claim_add_message'),
    path('claim/<int:claim_id>/close/', views_claims.claim_close, name='claim_close'),
    path('claim/<int:claim_id>/escalate/', views_claims.claim_escalate, name='claim_escalate'),

    path('checkout/', views.checkout, name='checkout'),
    path('success/<int:order_id>/', views.order_success, name='success'),
    path('mis-pedidos/', views.order_list, name='list'),
    path('<int:order_id>/', views.order_detail, name='detail'),
    path('payment-qr/', views.payment_qr, name='payment_qr'),
    path('cron/expire/', views.cron_expire_reservations, name='cron_expire'),
    path('cron/bcv/', views.cron_update_bcv, name='cron_bcv'),
    # Panel global del superuser
    path("panel/", views_panel.SuperuserOrderListView.as_view(), name="superuser_orders"),
    path("panel/<int:order_id>/", views_panel.SuperuserOrderDetailView.as_view(), name="superuser_order_detail"),
    path("panel/<int:order_id>/confirm-payment/", views_panel.superuser_confirm_payment, name="superuser_confirm_payment"),
    path("panel/<int:order_id>/cancel/", views_panel.superuser_cancel_order, name="superuser_cancel_order"),
    path("panel/<int:order_id>/mark-delivered/", views_panel.superuser_mark_delivered, name="superuser_mark_delivered"),
    path("panel/<int:order_id>/revert-delivery/", views_panel.superuser_revert_delivery, name="superuser_revert_delivery"),
    path("panel/history/", views_panel.SalesHistoryView.as_view(), name="sales_history"),
    # Solicitudes de cambio de datos bancarios (superuser)
    path("panel/payment-requests/", store_payment_views.pending_payment_requests, name="payment_requests"),
    path("panel/payment-requests/<int:request_id>/approve/", store_payment_views.approve_payment_request, name="payment_request_approve"),
    path("panel/payment-requests/<int:request_id>/reject/", store_payment_views.reject_payment_request, name="payment_request_reject"),
]