

from pathlib import Path
import os
from datetime import datetime
from django.utils import timezone
import logging
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv



# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, '.env'))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Application definition

INSTALLED_APPS = [
    # 'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',   # django app name
    'HR',
    'EHS',
    'STORE',
    'PRODUCTION',
    'ETP',
    'CANTEEN',
    'django_browser_reload',   # browser auto reload
    'import_export',           # file import export from admin panel
    'django_select2',
    'UTILITY',
    'QC',
    'CREDENTIALS',
    'CONTRACT',
    'HR_BUDGET',
]



MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',                       #For production static files load when debug=False
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "django_browser_reload.middleware.BrowserReloadMiddleware",

]


ROOT_URLCONF = 'oneSource.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'oneSource.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


DATABASE_ROUTERS = ['main.db_router.ReadOnlyDBRouter']

DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': os.getenv('DB_DEFAULT_NAME'),
        'USER': os.getenv('DB_DEFAULT_USER'),
        'PASSWORD': os.getenv('DB_DEFAULT_PASSWORD'),
        'HOST': os.getenv('DB_DEFAULT_HOST'),
        'PORT': os.getenv('DB_DEFAULT_PORT'),
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
            'extra_params': 'TrustServerCertificate=yes;',
            'trusted_connection': 'yes',
        },
    },
    'readonly_db': {
        'ENGINE': 'mssql',
        'NAME': os.getenv('DB_READONLY_NAME'),
        'USER': os.getenv('DB_READONLY_USER'),
        'PASSWORD': os.getenv('DB_READONLY_PASSWORD'),
        'HOST': os.getenv('DB_READONLY_HOST'),
        'PORT': os.getenv('DB_READONLY_PORT'),
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
            'extra_params': 'TrustServerCertificate=yes;',
            'trusted_connection': 'yes',
        },
    },
    'production_scheduler': {
        'ENGINE': 'mssql',
        'NAME': os.getenv('DB_PRODSCHED_NAME'),
        'USER': os.getenv('DB_PRODSCHED_USER'),
        'PASSWORD': os.getenv('DB_PRODSCHED_PASSWORD'),
        'HOST': os.getenv('DB_PRODSCHED_HOST'),
        'PORT': os.getenv('DB_PRODSCHED_PORT'),
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
            'extra_params': 'TrustServerCertificate=yes;',
            'trusted_connection': 'yes',
        },
    },
}





# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'                                                 #WHen using whitenoice need to do this setting
# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"      #WHen using whitenoice need to do this setting
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'          #WHen using whitenoice need to do this setting

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



# Unauthencated User redirected below path
LOGIN_URL = '/'
LOGOUT_REDIRECT_URL = '/'  



#Email Configuration
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp-mail.outlook.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)








"""==== Logging Related ===="""


BASE_LOG_DIR = os.path.join(BASE_DIR, 'logs')


def get_log_dir():
    now = timezone.localtime(timezone.now())
    month_str = now.strftime('%Y-%B')         # '2025-June'
    today_str = now.strftime('%Y-%m-%d')      # '2025-06-19'
    month_dir = os.path.join(BASE_LOG_DIR, month_str)
    log_dir = os.path.join(month_dir, today_str)
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

class DailyFolderTimedRotatingFileHandler(TimedRotatingFileHandler):
    """Writes logs to a daily folder, rotates at midnight, always uses new folder after 12AM."""
    def _open(self):
        # On every rotate, recalculate the log_dir
        self.baseFilename = os.path.join(get_log_dir(), os.path.basename(self.baseFilename))
        return super()._open()


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'access_file': {
            'level': 'INFO',
            'class': 'oneSource.settings.DailyFolderTimedRotatingFileHandler',  # Update the path to wherever you put the class
            'filename': os.path.join(get_log_dir(), 'access.log'),
            'when': 'midnight',
            'backupCount': 30,
            'formatter': 'verbose',
            'encoding': 'utf8',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'oneSource.settings.DailyFolderTimedRotatingFileHandler',
            'filename': os.path.join(get_log_dir(), 'error.log'),
            'when': 'midnight',
            'backupCount': 30,
            'formatter': 'verbose',
            'encoding': 'utf8',
        },
        'debug_file': {
            'level': 'DEBUG',
            'class': 'oneSource.settings.DailyFolderTimedRotatingFileHandler',
            'filename': os.path.join(get_log_dir(), 'debug.log'),
            'when': 'midnight',
            'backupCount': 30,
            'formatter': 'verbose',
            'encoding': 'utf8',
        },
        'warning_file': {
            'level': 'WARNING',
            'class': 'oneSource.settings.DailyFolderTimedRotatingFileHandler',
            'filename': os.path.join(get_log_dir(), 'warning.log'),
            'when': 'midnight',
            'backupCount': 30,
            'formatter': 'verbose',
            'encoding': 'utf8',
        },
        'critical_file': {
            'level': 'CRITICAL',
            'class': 'oneSource.settings.DailyFolderTimedRotatingFileHandler',
            'filename': os.path.join(get_log_dir(), 'critical.log'),
            'when': 'midnight',
            'backupCount': 30,
            'formatter': 'verbose',
            'encoding': 'utf8',
        },
    },
    'loggers': {
        'django': {
            'handlers': [
                'access_file',
                'error_file',
                'debug_file',
                'warning_file',
                'critical_file',
            ],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['debug_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'custom_logger': {
            'handlers': [
                'access_file',
                'error_file',
                'debug_file',
                'warning_file',
                'critical_file',
            ],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}





