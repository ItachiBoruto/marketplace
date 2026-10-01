"""
Django settings for market project.
"""

import os
import importlib
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api

# ===== CARGAR .env (desarrollo local) =====
load_dotenv()

# ===== SENTRY (solo si SENTRY_DSN esta configurado) =====
try:
    from apps.utils.sentry_config import init_sentry
    init_sentry()
except Exception as _sentry_err:
    import logging
    logging.getLogger(__name__).warning("Sentry no se pudo inicializar: %s", _sentry_err)

try:
    dj_database_url = importlib.import_module('dj_database_url')
except ModuleNotFoundError:
    dj_database_url = None

# ===== CONFIGURACIÓN BASE =====
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-dev-only-CHANGE-ME-before-deploy-xyz'
)

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()
]

# ===== APLICACIONES INSTALADAS =====
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',

    # Cloudinary (debe ir ANTES de staticfiles)
    'cloudinary_storage',

    'django.contrib.staticfiles',

    'rest_framework',
    'corsheaders',
    'cloudinary',
    'axes',

    # Nuestras apps
        'pwa',
    'pwa_custom',
    'backups',
    'dbbackup',
    'apps.accounts',
    'apps.stores',
    'apps.products',
    'apps.inventory',
    'apps.cart',
    'apps.orders',
    'apps.notifications',
    'apps.audit',
    'apps.utils',
]

# ===== MIDDLEWARE =====
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'apps.audit.middleware_nocache.NoCacheForAuthenticatedMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.audit.middleware.AuditMiddleware',
    'apps.audit.middleware_access.AccessAuditMiddleware',
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'market.urls'

# ===== TEMPLATES =====
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.cart.context_processors.cart_count',
                'apps.orders.context_processors.bcv_rate',
                'apps.notifications.context_processors.notifications_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'market.wsgi.application'

# ===== BASE DE DATOS =====
DATABASE_URL = os.environ.get('DATABASE_URL', '')

if DATABASE_URL and dj_database_url is not None:
    DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ===== VALIDACIÓN DE CONTRASEÑAS =====
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ===== HASHERS DE CONTRASEÑAS =====
# Argon2 es el recomendado por OWASP
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]

# ===== INTERNACIONALIZACIÓN =====
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Caracas'
USE_I18N = True
USE_TZ = True

# ===== ARCHIVOS ESTÁTICOS =====
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# ============================================================
# ===== CLOUDINARY CONFIGURATION =====
# ============================================================
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY', ''),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', ''),
}

cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=CLOUDINARY_STORAGE['API_KEY'],
    api_secret=CLOUDINARY_STORAGE['API_SECRET']
)

STORAGES = {
    'default': {
        'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
    'dbbackup': {
        'BACKEND': 'backups.storage.WindowsSafeDropBoxStorage',
        'OPTIONS': {
            'oauth2_access_token': os.environ.get('DROPBOX_ACCESS_TOKEN', ''),
            'timeout': 30,
            'root_path': '/mi-marketplace-backups/',
        },
    },
}

MEDIA_URL = '/media/'

# ============================================================
# ===== AUTENTICACIÓN Y SEGURIDAD =====
# ============================================================
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# ===== DJANGO-AXES (Rate limiting de login) =====
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'apps.accounts.backends.EmailOrUsernameBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=5)
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = ['ip_address', 'username']
AXES_LOCKOUT_CALLABLE = "apps.accounts.views.axes_lockout_response"
AXES_VERBOSE = False

AXES_IPWARE_META_PRECEDENCE_ORDER = [
    'HTTP_X_FORWARDED_FOR',
    'REMOTE_ADDR',
]

# ===== VISTA PERSONALIZADA DE CSRF FAILURE =====
def csrf_failure_view(request, reason=""):
    from django.shortcuts import render
    return render(request, "403.html", status=403)

CSRF_FAILURE_VIEW = "market.settings.csrf_failure_view"

# ============================================================
# ===== EMAIL / SMTP =====
# ============================================================
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend'
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get(
    'DEFAULT_FROM_EMAIL',
    'Mi Marketplace <noreply@marketplace.local>'
)
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Interruptor para deshabilitar el envio de emails (util en Render free)
EMAIL_ENABLED = os.environ.get('EMAIL_ENABLED', 'True') == 'True'

if DEBUG and not EMAIL_HOST_USER:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ===== SEGURIDAD SOLO EN PRODUCCIÓN =====
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    CSRF_TRUSTED_ORIGINS = [
        f"https://{host}"
        for host in ALLOWED_HOSTS
        if not host.startswith('.') and host not in ('localhost', '127.0.0.1')
    ]

# ============================================================
# ===== DATOS BANCARIOS PARA PAGOS =====
# ============================================================
BANK_INFO = {
    'bank_name': os.environ.get('BANK_NAME', 'Banco de Venezuela'),
    'account_number': os.environ.get('BANK_ACCOUNT', '0102-XXXX-XXXX-XXXX'),
    'account_holder': os.environ.get('BANK_HOLDER', 'Mi Marketplace'),
    'document': os.environ.get('BANK_DOCUMENT', ''),
    'email': os.environ.get('BANK_EMAIL', 'pagos@marketplace.com'),
    'phone': os.environ.get('BANK_PHONE', '+58 XXX-XXX-XXXX'),
}

# ============================================================
# ===== RESERVA DE STOCK EN PEDIDOS =====
# ============================================================
# Tiempo que la reserva de stock se mantiene antes de expirar.
# El cliente ya pago cuando crea el pedido, asi que este TTL es solo
# un backstop por si el comercio nunca revisa. 4320 minutos = 3 dias.
ORDER_RESERVATION_MINUTES = int(os.environ.get('ORDER_RESERVATION_MINUTES', 4320))

# Token para el endpoint cron de expiración de reservas
CRON_SECRET_TOKEN = os.environ.get('CRON_SECRET_TOKEN', '')

# ===== LOGGING =====
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'redact_pii': {
            '()': 'apps.utils.logging_filters.PIIRedactionFilter',
        },
    },
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['redact_pii'],
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django.security': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# ============================================================
# ===== DJANGO REST FRAMEWORK =====
# ============================================================
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        # Anonimos: 60 requests por minuto (scrapers normales se pasan)
        'anon': '60/min',
        # Usuarios autenticados: 120 requests por minuto
        'user': '120/min',
        # Scope especifico para APIs de catalogo
        'catalog': '30/min',
    },
}


# ============================================================
# PWA (Progressive Web App) - django-pwa
# ============================================================
PWA_APP_NAME = 'Mi Marketplace'
PWA_APP_DESCRIPTION = 'El marketplace de los comercios venezolanos'
PWA_APP_THEME_COLOR = '#1a1a2e'
PWA_APP_BACKGROUND_COLOR = '#ffffff'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'any'
PWA_APP_START_URL = '/'
PWA_APP_STATUS_BAR_COLOR = 'default'
PWA_APP_ICONS = [
    {'src': '/static/img/icons/icon-192x192.png', 'sizes': '192x192'},
    {'src': '/static/img/icons/icon-512x512.png', 'sizes': '512x512'},
]
PWA_APP_ICONS_APPLE = [
    {'src': '/static/img/apple-touch-icon.png', 'sizes': '180x180'},
]
PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'es-VE'

import os
PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, 'static/js/sw.js')


# ============================================================
# django-dbbackup - Backups automaticos a Dropbox
# ============================================================
import os as _os

# Mantener solo los ultimos 7 backups
DBBACKUP_CLEANUP_KEEP = 7
DBBACKUP_CLEANUP_KEEP_MEDIA = 7

# Comprimir backups
DBBACKUP_COMPRESS = True
DBBACKUP_SEND_EMAIL = False  # Evita el handler roto en Python 3.14



DBBACKUP_CLEANUP_KEEP = 7
DBBACKUP_CLEANUP_KEEP_MEDIA = 7
DBBACKUP_COMPRESS = True


# ============================================================
# WhiteNoise - Compresion Brotli + GZip para estaticos
# ============================================================
WHITENOISE_USE_BROTLI = True
WHITENOISE_COMPRESS_LEVEL = 6  # 1-9 (mas alto = mejor compresion, mas CPU)
WHITENOISE_MAX_AGE = 31536000  # 1 año de cache para archivos con hash
