from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.accounts.views import CustomLoginView, custom_logout

urlpatterns = [
    path('admin/', admin.site.urls),

    # Login personalizado
    path('accounts/login/', CustomLoginView.as_view(), name='login'),

    # Custom logout que limpia mensajes (debe ir ANTES del include auth)
    path('accounts/logout/', custom_logout, name='logout'),

    path('accounts/', include('apps.accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),

    path('stores/', include('apps.stores.urls')),
    path('cart/', include('apps.cart.urls')),
    path('orders/', include('apps.orders.urls')),
    path('notifications/', include('apps.notifications.urls')),   # ← NUEVO
    path('legal/', include('apps.utils.urls_legal')),
    path('', include('apps.products.urls')),
]