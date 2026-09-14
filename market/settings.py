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
    'apps.accounts',
    'apps.stores',
    'apps.products',
    'apps.inventory',
    'apps.cart',
    'apps.orders',       # ← NUEVO
    'apps.audit',
    'apps.utils',
]

# ===== MIDDLEWARE =====
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.audit.middleware.AuditMiddleware',
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
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
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
    'document': os.environ.get('BANK_DOCUMENT', ''),  # Cédula o RIF
    'email': os.environ.get('BANK_EMAIL', 'pagos@marketplace.com'),
    'phone': os.environ.get('BANK_PHONE', '+58 XXX-XXX-XXXX'),
}

# ============================================================
# ===== RESERVA DE STOCK EN PEDIDOS =====
# ============================================================
ORDER_RESERVATION_MINUTES = int(os.environ.get('ORDER_RESERVATION_MINUTES', 30))

# Token para el endpoint cron de expiración de reservas
CRON_SECRET_TOKEN = os.environ.get('CRON_SECRET_TOKEN', '')


# ===== LOGGING =====
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'django.security': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}