import os
import sys
import environ

from pathlib import Path
from celery.schedules import crontab
from decimal import Decimal

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve(strict=True).parent
APPS_DIR = BASE_DIR / 'appsinn'

env = environ.Env()
env.read_env() # read the .env file

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.str('DEBUG') == '1' # 1 means True, 0 means False
SECRET_KEY = env.str('SECRET_KEY', default='98Yt4}56^&%@!+)7748*&_?><HT]E~lrl%606sm{ticbu20=pv{r')

# ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])
# ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]', '*']
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.88.252', '192.168.8.100']

TESTING = sys.argv[1] == 'test'
PARALLEL = '--parallel' in sys.argv
SHELL = 'shell' in sys.argv or 'shell_plus' in sys.argv
SAMPLE_APP = os.environ.get('SAMPLE_APP', False)

OPENWISP_RADIUS_FREERADIUS_ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '192.168.0.0/24']
OPENWISP_RADIUS_COA_ENABLED = True
OPENWISP_RADIUS_ALLOWED_MOBILE_PREFIXES = ['+44', '+39', '+237', '+595', '+233']

# ---------------------------------------------- Installed apps
DJANGO_APPS  = [
    # Django
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',
]
THIRD_PARTY_APPS = [
    'admin_auto_filters', # for autocomplete filter
    # all-auth
    'allauth',
    'allauth.account',  
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.google',
    # rest framework
    'rest_framework',
    # rest framework/registration
    'dj_rest_auth',
    'dj_rest_auth.registration',
    'rest_framework.authtoken', 
    # 
    'django_filters',
    #
    'private_storage',
    'drf_yasg',
    # 'related_admin',
    'payments',
    'sequences',
    'django_extensions',
    # 'integrations',
    'djangosaml2',
    'widget_tweaks',
    # 'registration',
]
LOCAL_APPS = [
    # openwisp admin theme must come before the django admin in order to override the admin login page
    'openwisp_utils.admin_theme',
    'openwisp_utils',
    'openwisp_users.accounts',
    'openwisp_users',
    'openwisp_radius',
    #
    'testing_app',   
    'gmtisp_enduser',
    'gmtisp_billing', 
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
INSTALLED_APPS += ['django.contrib.admin',] # django admin

AUTHENTICATION_BACKENDS = (
    'openwisp_users.backends.UsersAuthenticationBackend',
    'openwisp_radius.saml.backends.OpenwispRadiusSaml2Backend', # Single Sign-On (SAML) feature.
    'sesame.backends.ModelBackend',
)

SITE_ID = 1
AUTH_USER_MODEL = 'openwisp_users.User'

LOGIN_URL = 'account_login'
LOGIN_REDIRECT_URL = '/dashboard/'
# LOGOUT_URL = '/logout/'
LOGOUT_REDIRECT_URL = 'account_login'
# BASE_URL='http://127.0.0.1:8000'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'sesame.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'djangosaml2.middleware.SamlSessionMiddleware',
    'openwisp_users.middleware.PasswordExpirationMiddleware',
]
# if DEBUG:
#     MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'openwisp_users.password_validation.PasswordReuseValidator'}
]
# if DEBUG:
#     AUTH_PASSWORD_VALIDATORS = [] # WARNING: for development only!

ROOT_URLCONF = 'gmtisp.urls'
WSGI_APPLICATION = 'gmtisp.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(os.path.dirname(BASE_DIR), 'templates'),],
        'OPTIONS': {
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'openwisp_utils.loaders.DependencyLoader',
                'django.template.loaders.app_directories.Loader',
            ],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                'openwisp_utils.admin_theme.context_processor.menu_groups',
                'openwisp_utils.admin_theme.context_processor.admin_theme_settings', # For test
                'gmtisp_billing.context_processors.account_status',
                # 'openwisp_utils.context_processors.test_theme_helper',
            ],
            'libraries':{
                'sidebar_links': 'templatetags.sidebar_links',
                'payment_buttons': 'gmtisp_billing.templatetags.payment_buttons',
            }
        },
    }
]

SAML_ALLOWED_HOSTS = []
SAML_USE_NAME_ID_AS_USERNAME = True
SAML_CREATE_UNKNOWN_USER = True
SAML_CONFIG = {}

# ---------------------------------------------- database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        'ATOMIC_REQUESTS': True,
    }
}

if TESTING:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

# try:
#     from .db import *
# except ImportError:
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',
#             'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#             'ATOMIC_REQUESTS': True,
#         }
#     }

# ---------------------------------------------- logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {message}',
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
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'gmtisp_billing': {  # Replace with your actual app name
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Adjust logging behavior based on DEBUG
if not DEBUG:
    LOGGING['loggers']['django']['level'] = 'INFO'
    LOGGING['loggers']['gmtisp_billing']['level'] = 'INFO'

# Modify logging when not in testing
if not TESTING:
    LOGGING['handlers']['django.server'] = {
        'level': 'DEBUG',
        'class': 'logging.StreamHandler',
        'formatter': 'django.server',
    }
    # Note: It's better to not overwrite the loggers entirely; merge instead
    LOGGING['loggers']['django'].update({
        'handlers': ['console'],  # Only use console handler in production
        'level': 'INFO',
    })
    LOGGING['loggers']['django.server'] = {
        'handlers': ['django.server'],
        'level': 'INFO',
        'propagate': False,
    }
    LOGGING['loggers']['openwisp_radius'] = {
        'handlers': ['console'],
        'level': 'DEBUG',
        'propagate': False,
    }

# Special logging configuration for the shell
if not TESTING and SHELL:
    LOGGING['loggers']['django.db'] = {
        'level': 'DEBUG',
        'handlers': ['console'],
        'propagate': False,
    }
    LOGGING['loggers'][''] = {
        'handlers': ['console', 'django.server'],
        'level': 'DEBUG',
        'propagate': False,
    }

LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'UTC'
# TIME_ZONE = 'America/Asuncion'  # used to replicate timezone related bug, do not change!
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ---------------------------------------------- Static and Media Settings
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'openwisp_utils.staticfiles.DependencyFinder',
]
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
PRIVATE_STORAGE_ROOT = os.path.join(MEDIA_ROOT, 'private')
MEDIA_URL = '/media/'
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(os.path.dirname(BASE_DIR), "static"),]
STATIC_ROOT = os.path.join(os.path.dirname(os.path.dirname((BASE_DIR))), "static_cdn", "static_root")

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------- Email Settings
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

EMAIL_HOST = env('EMAIL_HOST')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_USE_TLS = env('EMAIL_USE_TLS')
EMAIL_SUBJECT_PREFIX = env('EMAIL_SUBJECT_PREFIX')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
NOTIFY_EMAIL = env('NOTIFY_EMAIL')
EMAIL_TIMEOUT = 5

ADMINS = [('Kwame Amissah', 'me@gmail.com'),]
MANAGERS = ADMINS

SOCIALACCOUNT_PROVIDERS = {
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'INIT_PARAMS': {'cookie': True},
        'FIELDS': ['id', 'email', 'name', 'first_name', 'last_name', 'verified'],
        'VERIFIED_EMAIL': True,
    },
    'google': {'SCOPE': ['profile', 'email'], 'AUTH_PARAMS': {'access_type': 'online'}},
}

ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = 'email_confirmation_success'
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = 'email_confirmation_success'

REST_AUTH = {
    'SESSION_LOGIN': False,
    'PASSWORD_RESET_SERIALIZER': 'openwisp_radius.api.serializers.PasswordResetSerializer',
    'REGISTER_SERIALIZER': 'openwisp_radius.api.serializers.RegisterSerializer',
}

# only for automated test purposes
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'testing_app.api.throttling.CustomScopedRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {'anon': '20/hour'},
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

# ---------------------------------------------- Celery Settings
redis_host = os.getenv('REDIS_HOST', 'localhost')

if not TESTING:
    CELERY_BROKER_URL = os.getenv('REDIS_URL', f'redis://{redis_host}/1')
    # CELERY_BROKER_URL = 'redis://localhost/6'
else:
    OPENWISP_RADIUS_GROUPCHECK_ADMIN = True
    OPENWISP_RADIUS_GROUPREPLY_ADMIN = True
    OPENWISP_RADIUS_USERGROUP_ADMIN = True
    OPENWISP_RADIUS_USER_ADMIN_RADIUSTOKEN_INLINE = True
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    CELERY_BROKER_URL = 'memory://'

TEST_RUNNER = 'openwisp_utils.tests.TimeLoggingTestRunner'

CELERY_BEAT_SCHEDULE = {
    'deactivate_expired_users': {
        'task': 'openwisp_radius.tasks.cleanup_stale_radacct',
        'schedule': crontab(hour=0, minute=0),
        'args': None,
        'relative': True,
    },
    'delete_old_users': {
        'task': 'openwisp_radius.tasks.delete_old_users',
        'schedule': crontab(hour=0, minute=10),
        'args': [365],
        'relative': True,
    },
    'cleanup_stale_radacct': {
        'task': 'openwisp_radius.tasks.cleanup_stale_radacct',
        'schedule': crontab(hour=0, minute=20),
        'args': [365],
        'relative': True,
    },
    'delete_old_postauth': {
        'task': 'openwisp_radius.tasks.delete_old_postauth',
        'schedule': crontab(hour=0, minute=30),
        'args': [365],
        'relative': True,
    },
    'delete_old_radacct': {
        'task': 'openwisp_radius.tasks.delete_old_radacct',
        'schedule': crontab(hour=0, minute=40),
        'args': [365],
        'relative': True,
    },
    'unverify_inactive_users': {
        'task': 'openwisp_radius.tasks.unverify_inactive_users',
        'schedule': crontab(hour=1, minute=30),
        'relative': True,
    },
    'delete_inactive_users': {
        'task': 'openwisp_radius.tasks.delete_inactive_users',
        'schedule': crontab(hour=1, minute=50),
        'relative': True,
    },
}

# ---------------------------------------------- Caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        # 'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    }
}
# if not PARALLEL:
#     CACHES = {
#         'default': {
#             'BACKEND': 'django_redis.cache.RedisCache',
#             'LOCATION': 'redis://localhost/0',
#             'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
#         }
#     }
# # parallel testing with redis cache does not work
# # so we use the local memory cache in this case
# # we still keep redis for the standard non parallel tests
# # to avoid having bad surprises in production
# else:
#     CACHES = {
#         'default': {
#             'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#             'LOCATION': 'openwisp-users',
#         }
#     }

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_SECURE = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

SENDSMS_BACKEND = 'sendsms.backends.console.SmsBackend'
if TESTING:
    OPENWISP_RADIUS_SMS_TOKEN_MAX_USER_DAILY = 3
    OPENWISP_RADIUS_SMS_TOKEN_MAX_ATTEMPTS = 3
    OPENWISP_RADIUS_SMS_TOKEN_MAX_IP_DAILY = 4
    SENDSMS_BACKEND = 'sendsms.backends.dummy.SmsBackend'
else:
    OPENWISP_RADIUS_SMS_TOKEN_MAX_USER_DAILY = 10

# Messages contrib app
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.ERROR: 'danger'
}

# ---------------------------------------------- OpenWISP Settings
# OPENWISP_RADIUS_PASSWORD_RESET_URLS = {
#     # use the uuid because the slug can change
#     # 'dabbd57a-11ca-4277-8dbb-ad21057b5ecd': 'https://org.com/{organization}/password/reset/confirm/{uid}/{token}',
#     # fallback in case the specific org page is not defined
#     '__all__': 'https://example.com/{{organization}/password/reset/confirm/{uid}/{token}',
# }

OPENWISP_RADIUS_PASSWORD_RESET_URLS = {
    '__all__': (
        'http://localhost:8080/{organization}/password/reset/confirm/{uid}/{token}'
    ),
}
OPENWISP_USERS_AUTH_API = True
OPENWISP_ADMIN_THEME_LINKS = [
    {
        'type': 'text/css',
        'href': 'admin/css/openwisp.css',
        'rel': 'stylesheet',
        'media': 'all',
    },
    {
        'type': 'text/css',
        'href': 'menu-test.css',
        'rel': 'stylesheet',
        'media': 'all',
    },  # custom css for testing menu icons
    {
        'type': 'image/x-icon',
        'href': 'ui/openwisp/images/favicon.png',
        'rel': 'icon',
    },
]
OPENWISP_ADMIN_THEME_JS = ['dummy.js']
# admin site interface
OPENWISP_ADMIN_SITE_HEADER = 'GMTISP'
OPENWISP_ADMIN_SITE_TITLE = 'GMTISP'
OPENWISP_RADIUS_EXTRA_NAS_TYPES = (
    ('cisco', 'Cisco Router'),
    ('mikrotik', 'Mikrotik'),
    )
if os.environ.get('SAMPLE_APP', False) and TESTING:
    # Required for openwisp-users tests
    OPENWISP_ORGANIZATION_USER_ADMIN = True
    OPENWISP_ORGANIZATION_OWNER_ADMIN = True
    OPENWISP_USERS_AUTH_API = True

# CORS headers, useful during development and testing
try:
    import corsheaders  # noqa

    INSTALLED_APPS.append('corsheaders')
    MIDDLEWARE.insert(
        MIDDLEWARE.index('django.middleware.common.CommonMiddleware'),
        'corsheaders.middleware.CorsMiddleware',
    )
    # WARNING: for development only!
    CORS_ORIGIN_ALLOW_ALL = True
except ImportError:
    pass

# testing_app
OPENWISP_ADMIN_SITE_CLASS = 'testing_app.site.CustomAdminSite'
OPENWISP_TEST_ADMIN_MENU_ITEMS = [{'model': 'testing_app.Project'}]

# ---------------------------------------------- plans
PLANS_ORDER_MODEL = 'gmtisp_billing.Order'
# This is required for django-plans
PLANS_INVOICE_ISSUER = {
    'issuer_name': 'My Company Ltd',
    'issuer_street': '48th Suny street',
    'issuer_zipcode': '111-456',
    'issuer_city': 'Django City',
    'issuer_country': 'PL',
    'issuer_tax_number': 'PL123456789',
}
PLANS_CURRENCY = 'GHS'
ENABLE_FAKE_PAYMENTS = True
# The value None means “TAX not applicable, rather than value Decimal('0') which is 0% TAX.
PLANS_TAX = Decimal('23.0')  # for 23% VAT
PLANS_TAXATION_POLICY = 'gmtisp_billing.taxation.eu.EUTaxationPolicy'
PLANS_TAX_COUNTRY = 'PL'
PLANS_DEFAULT_COUNTRY = 'CZ'
PLANS_GET_COUNTRY_FROM_IP = True
PLANS_VALIDATORS = {
    'MAX_PLAN_COUNT': 'gmtisp_billing.validators_my.max_plans_validator',
    'MAX_QUOTA_SIZE': 'gmtisp_billing.validators_my.max_quota_validator',
}
PLANS_VALIDATION = True
PLANS_VALIDATION_PERIOD = 30
# PLANS_INVOICE_COUNTER_RESET = Invoice.NUMBERING.MONTHLY
# PLANS_INVOICE_NUMBER_FORMAT = {{ invoice.issued|date:'d/m/Y' }}
# PLANS_INVOICE_NUMBER_FORMAT = '{{ invoice.number }}/{{ invoice.issued|date='m/FV/Y' }}'
from urllib.parse import urljoin
PLANS_INVOICE_LOGO_URL = urljoin(STATIC_URL, 'my_logo.png')
PLANS_INVOICE_TEMPLATE = 'gmtisp_billing/invoices/PL_EN.html'
PLANS_ORDER_EXPIRATION = 14
PLANS_EXPIRATION_REMIND = [1, 3 , 7] # User will receive notification before 7, 3 and 1 day to account expire.
PLANS_DEFAULT_GRACE_PERIOD = 30 # New account default plan expiration period counted in days.
SEND_PLANS_EMAILS = True

# ---------------------------------------------- plans payments
from typing import Dict, Tuple

PAYMENT_MODEL = 'gmtisp_billing.Payment'

if DEBUG:
    PAYMENT_VARIANTS: Dict[str, Tuple[str, Dict]] = {
        'dummy': ('payments.dummy.DummyProvider', {}),
    }

# Keep in mind that if you use `localhost`, external servers won't be
# able to reach you for webhook notifications.
PAYMENT_HOST = 'localhost:8000'
# 
PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY')
PAYSTACK_CALLBACK_URL = 'http://127.0.0.1/payment/verify/'
# PAYSTACK_CALLBACK_URL = 'https://yourdomain.com/payment/verify/'


# ---------------------------------------------- debug_toolbar
# debug_toolbar
# if DEBUG:
#     INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
    
#     # Rearrange DEBUG_TOOLBAR_PANELS
#     DEBUG_TOOLBAR_PANELS = [
#         'debug_toolbar.panels.versions.VersionsPanel',
#         'debug_toolbar.panels.timer.TimerPanel',
#         'debug_toolbar.panels.settings.SettingsPanel',
#         'debug_toolbar.panels.headers.HeadersPanel',
#         'debug_toolbar.panels.request.RequestPanel',
#         'debug_toolbar.panels.sql.SQLPanel',
#         'debug_toolbar.panels.staticfiles.StaticFilesPanel',
#         'debug_toolbar.panels.templates.TemplatesPanel',
#         'debug_toolbar.panels.cache.CachePanel',
#         'debug_toolbar.panels.signals.SignalsPanel',
#         'debug_toolbar.panels.logging.LoggingPanel',
#         'debug_toolbar.panels.redirects.RedirectsPanel',
#     ]

#     def show_toolbar(request):
#         return True

#     DEBUG_TOOLBAR_CONFIG = {
#         'DISABLE_PANELS': ['debug_toolbar.panels.redirects.RedirectsPanel'], 
#         'SHOW_TEMPLATE_CONTEXT': True,
#         'INTERCEPT_REDIRECTS': False,
#         'SHOW_TOOLBAR_CALLBACK': show_toolbar
#     }
# ------------------------------------------------------------------ end debug_toolbar

# from .settings_openwisp import *




# ------------------------------------------------------------------ production
if not DEBUG:
    # Load secret key and sensitive data from environment variables
    SECRET_KEY = env.str("SECRET_KEY_LIVE")
    PAYPAL_CLIENT_ID = env('PAYPAL_LIVE_CLIENT_ID')
    PAYPAL_SECRET_KEY = env('PAYPAL_LIVE_SECRET_KEY')

    # Restrict allowed hosts
    ALLOWED_HOSTS = env.list("ALLOWED_HOSTS_LIVE", default=['example.com'])

    # Enforce SSL/TLS settings
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HTTP Strict Transport Security (HSTS)
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Content security policies
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True

    # Frame Denial
    SECURE_FRAME_DENY = env.bool("SECURE_FRAME_DENY", default=True)

    # Redirect Exempt
    SECURE_REDIRECT_EXEMPT = []

    # CORS settings
    CORS_REPLACE_HTTPS_REFERER = env.bool("CORS_REPLACE_HTTPS_REFERER", default=True)

    # Scheme for absolute URLs
    HOST_SCHEME = "https://"

    # Logging configuration
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "mail_admins": {
                "level": "ERROR",
                "class": "django.utils.log.AdminEmailHandler",
                "include_html": True,
            },
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
            },
        },
        "loggers": {
            "django": {
                "handlers": ["console", "mail_admins"],
                "level": "ERROR",
                "propagate": True,
            },
        },
    }

# ------------------------------------------------------------------ end production