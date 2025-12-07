"""
Cloudflare-specific settings for sentiment_analyzer project.
Optimized for Cloudflare Workers, R2, and edge deployment.
"""

from .settings_production import *
from decouple import config
import os

# Cloudflare-specific configurations
CLOUDFLARE_DEPLOYMENT = True

# Trust Cloudflare headers
SECURE_PROXY_SSL_HEADER = ('HTTP_CF_VISITOR', '{"scheme":"https"}')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Cloudflare R2 Configuration for static and media files
if config('USE_CLOUDFLARE_R2', default=True, cast=bool):
    # R2 Storage Configuration
    AWS_ACCESS_KEY_ID = config('CLOUDFLARE_R2_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('CLOUDFLARE_R2_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('CLOUDFLARE_R2_BUCKET_NAME')
    AWS_S3_REGION_NAME = 'auto'  # Cloudflare R2 uses 'auto' region
    AWS_S3_ENDPOINT_URL = f'https://{config("CLOUDFLARE_ACCOUNT_ID")}.r2.cloudflarestorage.com'
    AWS_S3_CUSTOM_DOMAIN = config('CLOUDFLARE_R2_CUSTOM_DOMAIN', default='')
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=31536000',  # 1 year cache
    }
    
    # Static files
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/' if AWS_S3_CUSTOM_DOMAIN else f'{AWS_S3_ENDPOINT_URL}/static/'
    
    # Media files
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/' if AWS_S3_CUSTOM_DOMAIN else f'{AWS_S3_ENDPOINT_URL}/media/'

# Cloudflare-specific security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# CORS configuration for Cloudflare
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='', cast=Csv())
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False

# Cloudflare-specific middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # Add CORS middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Cloudflare Workers configuration
CLOUDFLARE_WORKERS_URL = config('CLOUDFLARE_WORKERS_URL', default='')
CLOUDFLARE_WORKERS_TOKEN = config('CLOUDFLARE_WORKERS_TOKEN', default='')

# Edge caching configuration
CACHE_TTL = config('CACHE_TTL', default=3600, cast=int)  # 1 hour default
CACHE_HEADERS = {
    'Cache-Control': f'max-age={CACHE_TTL}',
    'CDN-Cache-Control': f'max-age={CACHE_TTL}',
    'Cloudflare-CDN-Cache-Control': f'max-age={CACHE_TTL}',
}

# Cloudflare-specific logging
LOGGING['handlers']['cloudflare'] = {
    'level': 'INFO',
    'class': 'logging.handlers.HTTPHandler',
    'host': 'logs.cloudflare.com',
    'url': '/logs',
    'method': 'POST',
    'secure': True,
}

# API rate limiting for Cloudflare
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': f'{config("API_RATE_LIMIT", default=1000)}/hour',
    'user': f'{config("API_RATE_LIMIT", default=1000)}/hour',
    'cloudflare': f'{config("CLOUDFLARE_RATE_LIMIT", default=10000)}/hour',
}

# Cloudflare-specific static files configuration
STATICFILES_DIRS = [
    BASE_DIR / 'frontend' / 'static',
]

# Cloudflare Analytics (if using)
CLOUDFLARE_ANALYTICS_TOKEN = config('CLOUDFLARE_ANALYTICS_TOKEN', default='')

# Cloudflare Tunnel configuration
CLOUDFLARE_TUNNEL_TOKEN = config('CLOUDFLARE_TUNNEL_TOKEN', default='')

# Edge computing configuration
EDGE_COMPUTING = config('EDGE_COMPUTING', default=False, cast=bool)
EDGE_FUNCTIONS = config('EDGE_FUNCTIONS', default='', cast=Csv())

# Cloudflare-specific email configuration
if config('USE_CLOUDFLARE_EMAIL', default=False, cast=bool):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = config('CLOUDFLARE_EMAIL_HOST', default='smtp.cloudflare.com')
    EMAIL_PORT = config('CLOUDFLARE_EMAIL_PORT', default=587, cast=int)
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = config('CLOUDFLARE_EMAIL_USER')
    EMAIL_HOST_PASSWORD = config('CLOUDFLARE_EMAIL_PASSWORD')

# Cloudflare-specific database configuration (if using Cloudflare D1)
if config('USE_CLOUDFLARE_D1', default=False, cast=bool):
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': config('CLOUDFLARE_D1_DATABASE_PATH', default='/tmp/db.sqlite3'),
    }

# Cloudflare-specific cache configuration
if config('USE_CLOUDFLARE_CACHE', default=True, cast=bool):
    CACHES['default'] = {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,
        }
    }

# Cloudflare-specific session configuration
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Cloudflare-specific file upload configuration
FILE_UPLOAD_MAX_MEMORY_SIZE = config('FILE_UPLOAD_MAX_MEMORY_SIZE', default=10485760, cast=int)  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = config('DATA_UPLOAD_MAX_MEMORY_SIZE', default=10485760, cast=int)  # 10MB

# Cloudflare-specific admin configuration
ADMIN_URL = config('ADMIN_URL', default='admin/')

# Cloudflare-specific API configuration
API_VERSION = config('API_VERSION', default='v1')
API_BASE_URL = config('API_BASE_URL', default='https://your-domain.com/api/')

# Cloudflare-specific frontend configuration
FRONTEND_CDN_URL = config('FRONTEND_CDN_URL', default='')
FRONTEND_VERSION = config('FRONTEND_VERSION', default='1.0.0')

# Cloudflare-specific monitoring
CLOUDFLARE_MONITORING = config('CLOUDFLARE_MONITORING', default=True, cast=bool)
CLOUDFLARE_METRICS_TOKEN = config('CLOUDFLARE_METRICS_TOKEN', default='')

# Cloudflare-specific security
CLOUDFLARE_SECURITY_LEVEL = config('CLOUDFLARE_SECURITY_LEVEL', default='medium')
CLOUDFLARE_BOT_FIGHT_MODE = config('CLOUDFLARE_BOT_FIGHT_MODE', default=True, cast=bool)
CLOUDFLARE_CHALLENGE_PASSAGE = config('CLOUDFLARE_CHALLENGE_PASSAGE', default=True, cast=bool)
