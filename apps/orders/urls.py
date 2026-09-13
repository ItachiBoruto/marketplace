from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('success/<int:order_id>/', views.order_success, name='success'),
    path('mis-pedidos/', views.order_list, name='list'),
    path('<int:order_id>/', views.order_detail, name='detail'),
]