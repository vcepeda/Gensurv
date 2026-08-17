"""
Django settings for gensurv_project project.

This is a TEMPLATE - it contains no real credentials. To deploy:

    cp settings_template.py settings.py

...then fill in every CHANGE-ME placeholder below. `settings.py` is
gitignored (see backend/gensurv_project/README.md) so your real values
never get committed.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
# Generate one with:
#   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY = 'CHANGE-ME-generate-your-own-secret-key'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['CHANGE-ME-your-domain.example', 'localhost', '127.0.0.1']
CSRF_TRUSTED_ORIGINS = ['https://CHANGE-ME-your-domain.example']

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CRISPY_TEMPLATE_PACK = "bootstrap5"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    "gensurvapp",
    "register",
    "crispy_forms",
    "crispy_bootstrap5",
    "rest_framework",
    "corsheaders",  # for local development, since vue.js runs on a different port
    'dbbackup',  # django-dbbackup
    'storages',
    'hijack',  # act as another user
    'hijack.contrib.admin',
]

SITE_ID = 1
SITE_URL = 'https://CHANGE-ME-your-domain.example'  # Replace with your actual domain

DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': 'CHANGE-ME-/absolute/path/to/dbbackup-storage'}

DATA_UPLOAD_MAX_MEMORY_SIZE = None
DATA_UPLOAD_MAX_NUMBER_FILES = 1000  # Limit to 1000 files per upload
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5MB threshold before writing to disk

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'hijack.middleware.HijackUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "corsheaders.middleware.CorsMiddleware",
]

ROOT_URLCONF = 'gensurv_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
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

WSGI_APPLICATION = 'gensurv_project.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'CHANGE-ME-db-name',
        'USER': 'CHANGE-ME-db-user',
        'PASSWORD': 'CHANGE-ME-db-password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Rest API
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}

# CORS
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'https://CHANGE-ME-your-domain.example',
]

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'register.CustomUser'

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Media files
MEDIA_ROOT = 'CHANGE-ME-/absolute/path/to/media'
MEDIA_URL = '/media/'

# Bactopia's `bactopia summary` report (rank/reason per sample), used by the
# results dashboard to show which samples passed/failed QC cutoffs.
BACTOPIA_REPORT_PATH = 'CHANGE-ME-/absolute/path/to/bactopia-report.tsv'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = '/login/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'django_debug.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Email settings (using Gmail as an example)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'CHANGE-ME-your-email@example.com'
EMAIL_HOST_PASSWORD = 'CHANGE-ME-your-app-password'

# Default sender email
DEFAULT_FROM_EMAIL = 'CHANGE-ME-your-email@example.com'
# Domain for password reset links
SITE_DOMAIN = 'https://CHANGE-ME-your-domain.example'
# Optionally add the protocol
PASSWORD_RESET_URL = 'https://CHANGE-ME-your-domain.example'

# Admin email (where registration notifications will be sent)
ADMIN_EMAIL = 'CHANGE-ME-your-email@example.com'

ADMINS = [
    ("Admin", ADMIN_EMAIL),
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

CRISPY_FAIL_SILENTLY = False
ENABLE_FTP_UPLOAD = False  # Set to False if you don't want to upload to FTP
