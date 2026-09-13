from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.accounts.views import CustomLoginView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Login personalizado (con avisos de intentos)
    path('accounts/login/', CustomLoginView.as_view(), name='login'),

    path('accounts/', include('apps.accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),

    path('stores/', include('apps.stores.urls')),
    path('cart/', include('apps.cart.urls')),
    path('', include('apps.products.urls')),
]