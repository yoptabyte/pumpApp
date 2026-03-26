"""
Django settings for pampApp project.
"""

from datetime import timedelta
from pathlib import Path

from corsheaders.defaults import default_headers
from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', cast=bool)

ALLOWED_HOSTS = config(
    'DJANGO_ALLOWED_HOSTS',
    default='localhost,127.0.0.1,[::1],web,pumpapp.com',
    cast=Csv(),
)

BASE_API_URL = config('BASE_API_URL', default='http://localhost:8000')
BASE_APP_URL = config('BASE_APP_URL', default='http://localhost:3000')
FRONTEND_URL = config('FRONTEND_URL', default=BASE_APP_URL)

USE_S3_MEDIA_STORAGE = config(
    'USE_S3_MEDIA_STORAGE',
    default=config('USE_CEPH_MEDIA_STORAGE', default=False, cast=bool),
    cast=bool,
)
USE_CEPH_MEDIA_STORAGE = USE_S3_MEDIA_STORAGE
DEFAULT_USER_TIMEZONE = config('DEFAULT_USER_TIMEZONE', default='Europe/Lisbon')

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
FRONTEND_BUILD_STATIC = BASE_DIR / 'frontend' / 'build' / 'static'
STATICFILES_DIRS = [FRONTEND_BUILD_STATIC] if FRONTEND_BUILD_STATIC.exists() else []

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

if USE_S3_MEDIA_STORAGE:
    AWS_ACCESS_KEY_ID = config('S3_ACCESS_KEY_ID', default=config('CEPH_ACCESS_KEY_ID', default=''))
    AWS_SECRET_ACCESS_KEY = config('S3_SECRET_ACCESS_KEY', default=config('CEPH_SECRET_ACCESS_KEY', default=''))
    AWS_STORAGE_BUCKET_NAME = config('S3_MEDIA_BUCKET', default=config('CEPH_MEDIA_BUCKET', default=''))
    AWS_S3_ENDPOINT_URL = config('S3_ENDPOINT_URL', default=config('CEPH_ENDPOINT_URL', default=''))
    AWS_S3_REGION_NAME = config('S3_REGION', default=config('CEPH_REGION', default='us-east-1'))
    AWS_S3_ADDRESSING_STYLE = config('S3_ADDRESSING_STYLE', default=config('CEPH_ADDRESSING_STYLE', default='path'))
    AWS_S3_SIGNATURE_VERSION = config('S3_SIGNATURE_VERSION', default=config('CEPH_SIGNATURE_VERSION', default='s3v4'))
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = config(
        'S3_QUERYSTRING_AUTH',
        default=config('CEPH_QUERYSTRING_AUTH', default=True, cast=bool),
        cast=bool,
    )
    AWS_S3_FILE_OVERWRITE = False
    AWS_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }

    STORAGES = {
        'default': {
            'BACKEND': 'pamp_app.storage.S3MediaStorage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }

    s3_media_base_url = config('S3_MEDIA_BASE_URL', default=config('CEPH_MEDIA_BASE_URL', default='')).rstrip('/')
    if s3_media_base_url:
        if s3_media_base_url.endswith('/media'):
            MEDIA_URL = f'{s3_media_base_url}/'
        else:
            MEDIA_URL = f'{s3_media_base_url}/media/'

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default=(
        'http://localhost:3000,'
        'http://localhost:8000,'
        'http://localhost:8080,'
        'http://127.0.0.1:3000,'
        'http://127.0.0.1:8000,'
        'http://127.0.0.1:8080,'
        'http://web:3000,'
        'http://web:8000'
    ),
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default=(
        'http://localhost:3000,'
        'http://localhost:8000,'
        'http://localhost:8080,'
        'http://127.0.0.1:3000,'
        'http://127.0.0.1:8000,'
        'http://127.0.0.1:8080,'
        'http://web:3000,'
        'http://web:8000'
    ),
    cast=Csv(),
)

CORS_ALLOW_HEADERS = list(default_headers) + [
    'authorization',
    'content-type',
    'x-csrftoken',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'pamp_app.authentication.EmailAuthBackend',
    'social_core.backends.google.GoogleOAuth2',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config('GOOGLE_OAUTH2_KEY', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config('GOOGLE_OAUTH2_SECRET', default='')

SOCIALACCOUNT_ADAPTER = 'pamp_app.adapters.MySocialAccountAdapter'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email', 'openid'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'OAUTH_PKCE_ENABLED': True,
    }
}
SITE_ID = 1

ACCESS_TOKEN_LIFETIME_MINUTES = config('ACCESS_TOKEN_LIFETIME_MINUTES', default=15, cast=int)
REFRESH_TOKEN_LIFETIME_DAYS = config('REFRESH_TOKEN_LIFETIME_DAYS', default=1, cast=int)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=ACCESS_TOKEN_LIFETIME_MINUTES),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=REFRESH_TOKEN_LIFETIME_DAYS),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://redis:6379/1'),
    }
}
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default=config('REDIS_URL', default='redis://redis:6379/1'))
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default=CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_BEAT_SCHEDULE = {
    'dispatch-due-telegram-notifications-every-minute': {
        'task': 'pamp_app.tasks.dispatch_due_notifications',
        'schedule': 60.0,
    },
    'refresh-telegram-notifications-every-hour': {
        'task': 'pamp_app.tasks.refresh_training_notifications',
        'schedule': 3600.0,
    },
}

COOKIE_SECURE = config('COOKIE_SECURE', default=not DEBUG, cast=bool)
COOKIE_SAMESITE = config('COOKIE_SAMESITE', default='Lax')
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = COOKIE_SECURE
SESSION_COOKIE_SAMESITE = COOKIE_SAMESITE
CSRF_COOKIE_SECURE = COOKIE_SECURE
CSRF_COOKIE_SAMESITE = COOKIE_SAMESITE
CSRF_COOKIE_HTTPONLY = False
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=not DEBUG, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000 if not DEBUG else 0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=not DEBUG, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=not DEBUG, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
REFERRER_POLICY = 'strict-origin-when-cross-origin'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'dj_rest_auth.jwt_auth.JWTCookieAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': config('DRF_THROTTLE_ANON', default='30/min'),
        'user': config('DRF_THROTTLE_USER', default='120/min'),
        'auth': config('DRF_THROTTLE_AUTH', default='10/min'),
        'telegram_confirm': config('DRF_THROTTLE_TELEGRAM_CONFIRM', default='20/min'),
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Pamp App API',
    'DESCRIPTION': 'Versioned API for the Pamp App backend.',
    'VERSION': 'v1',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': r'/api/v1',
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
}

REST_USE_JWT = True
JWT_AUTH_COOKIE = config('JWT_AUTH_COOKIE', default='my-app-auth')
JWT_AUTH_REFRESH_COOKIE = config('JWT_AUTH_REFRESH_COOKIE', default='my-refresh-token')
JWT_AUTH_COOKIE_USE_CSRF = True
JWT_AUTH_COOKIE_ENFORCE_CSRF_ON_UNAUTHENTICATED = True
JWT_AUTH_SECURE = COOKIE_SECURE
JWT_AUTH_SAMESITE = COOKIE_SAMESITE
JWT_AUTH_HTTPONLY = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'django.contrib.sites',
    'rest_framework',
    'corsheaders',
    'django_extensions',
    'rest_framework.authtoken',
    'rest_framework_simplejwt.token_blacklist',
    'rest_framework_api_key',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'dj_rest_auth',
    'allauth',
    'allauth.account',
    'dj_rest_auth.registration',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'storages',
    'pamp_app.apps.PampAppConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'pampApp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'frontend' / 'build'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'pampApp.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='pampdb'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='db'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=60, cast=int),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
