"""
Local development settings for Gensurv - SANITIZED, safe to hand to a
coworker testing on their own laptop. NOT the real production settings.py
(that file has real secrets and is intentionally excluded from GitHub via
.gitignore - this is a separate, purpose-built local-dev version).

Setup: copy this file to backend/gensurv_project/settings.py after cloning
the repo (see TUTORIAL.md in this same folder for the full walkthrough).

What's different from production:
- Freshly generated SECRET_KEY (never reuse production's).
- DATABASES points at a local Postgres database the coworker creates
  themselves - not the production database. No real credentials involved.
- MEDIA_ROOT is a local folder inside the project instead of the
  production NFS mount - nothing here needs /mnt/storage to exist.
- BACTOPIA_REPORT_PATH points to a local path that doesn't need to exist -
  the app handles a missing report file gracefully (QC status just shows
  "pending" for everything, which is expected with no real analysis data).
- EMAIL_BACKEND prints emails to the console instead of really sending -
  no real SMTP credentials needed for local testing.
- ALLOWED_HOSTS/CORS trimmed to localhost only.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Generate your own before running the server - never reuse this
# placeholder or production's key:
#   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY = 'CHANGE-ME-generate-your-own-local-secret-key'

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

CRISPY_TEMPLATE_PACK = "bootstrap5"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

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
    "corsheaders",
    'dbbackup',
    'storages',
    'hijack',
    'hijack.contrib.admin',
]

SITE_ID = 1
SITE_URL = 'http://localhost:5173'

DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': str(BASE_DIR / 'media' / 'DBBACKUP_STORAGE')}

DATA_UPLOAD_MAX_MEMORY_SIZE = None
DATA_UPLOAD_MAX_NUMBER_FILES = 1000
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440

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
        'DIRS': [BASE_DIR / 'templates'],
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

# Local Postgres database - create this yourself (see TUTORIAL.md), do NOT
# point this at the production database.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gensurv_db_local',
        'USER': 'gensurv_user_local',
        'PASSWORD': 'choose-your-own-local-password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

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

# Not strictly needed - the frontend dev server proxies /api requests to
# Django server-side (see vite.config.js), so the browser never makes a
# real cross-origin request during local dev. Left here in case the
# frontend is ever pointed at the backend directly instead.
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'register.CustomUser'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Local media folder inside the project - no dependency on production's
# /mnt/storage NFS mount.
MEDIA_ROOT = str(BASE_DIR / 'media')
MEDIA_URL = '/media/'

# Doesn't need to exist locally - the app handles a missing report file
# gracefully (QC status just shows as "pending" everywhere).
BACTOPIA_REPORT_PATH = str(BASE_DIR / 'media' / 'bactopia-report.tsv')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = '/login/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{levelname} {asctime} {module} {message}', 'style': '{'},
        'simple': {'format': '{levelname} {message}', 'style': '{'},
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
        'django': {'handlers': ['file'], 'level': 'DEBUG', 'propagate': True},
    },
}

# Prints emails to the terminal instead of really sending them - no SMTP
# credentials needed for local testing. Password-reset emails etc. will
# show up in the `runserver` console output.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'test@localhost'
SITE_DOMAIN = 'http://localhost:5173'
PASSWORD_RESET_URL = 'http://localhost:5173'
ADMIN_EMAIL = 'test@localhost'
ADMINS = [("Admin", ADMIN_EMAIL)]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

CRISPY_FAIL_SILENTLY = False
ENABLE_FTP_UPLOAD = False
