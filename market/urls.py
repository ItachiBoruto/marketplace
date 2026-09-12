from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Cuenta: registro propio + auth estándar de Django
    path('accounts/', include('apps.accounts.urls')),         # ← NUEVO
    path('accounts/', include('django.contrib.auth.urls')),   # login, logout, password reset

    path('stores/', include('apps.stores.urls')),
    path('cart/', include('apps.cart.urls')),
    path('', include('apps.products.urls')),
]

# No servir archivos estáticos desde Django en producción
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)