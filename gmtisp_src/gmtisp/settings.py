import os
import sys
import environ

from pathlib import Path
from celery.schedules import crontab
from decimal import Decimal


# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
BASE_DIR = Path(__file__).resolve(strict=True).parent
APPS_DIR = BASE_DIR / 'appsinn'

env = environ.Env()
env.read_env() # read the .env file
# environ.Env.read_env() # read the .env file

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = str(env('DEBUG')) == '1' # 1 == True, 0 == False
SECRET_KEY = env.str('SECRET_KEY', default='98Yt456^&%@!+)7748*&_?><HTE~lrl%606smticbu20=pvr')
# ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
ALLOWED_HOSTS = ['*']

TESTING = sys.argv[1] == 'test'
PARALLEL = '--parallel' in sys.argv
SHELL = 'shell' in sys.argv or 'shell_plus' in sys.argv
SAMPLE_APP = os.environ.get('SAMPLE_APP', False)

OPENWISP_RADIUS_FREERADIUS_ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
OPENWISP_RADIUS_COA_ENABLED = True
OPENWISP_RADIUS_ALLOWED_MOBILE_PREFIXES = ['+44', '+39', '+237', '+595', '+233']

INSTALLED_APPS = [
    # Django
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # openwisp admin theme
    # must come before the django admin in order to override the admin login page
    'openwisp_utils.admin_theme',
    'openwisp_users.accounts',

    # all-auth
    'django.contrib.sites',
    'allauth',
    'allauth.account',  
    
    # admin
    'admin_auto_filters',
    'django.contrib.admin',

    # rest framework
    'rest_framework',
    'django_filters',

    # registration
    'rest_framework.authtoken',
    'dj_rest_auth',
    'dj_rest_auth.registration',

    # social login
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.google',
  
   # ---------------------------------- openwisp
    'testing_app',    
    'openwisp_users',
    'openwisp_radius',
    'openwisp_utils',
    'private_storage',
    'drf_yasg',

    # plans
    # 'related_admin',
    'plans',
    'ordered_model',
    # 'bootstrap3',
    'enduser',
    
    # other
    'django_extensions',
    # 'integrations',
    'djangosaml2',
]

LOGIN_REDIRECT_URL = 'admin:index'

AUTHENTICATION_BACKENDS = (
    'openwisp_users.backends.UsersAuthenticationBackend',
    'openwisp_radius.saml.backends.OpenwispRadiusSaml2Backend',
    'sesame.backends.ModelBackend',
)

AUTH_USER_MODEL = 'openwisp_users.User'
SITE_ID = 1

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'openwisp_utils.staticfiles.DependencyFinder',
]

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

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'openwisp_users.password_validation.PasswordReuseValidator'}
]

SESSION_COOKIE_SECURE = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SAML_ALLOWED_HOSTS = []
SAML_USE_NAME_ID_AS_USERNAME = True
SAML_CREATE_UNKNOWN_USER = True
SAML_CONFIG = {}

ROOT_URLCONF = 'gmtisp.urls'
WSGI_APPLICATION = 'gmtisp.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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
                
                # For test
                'openwisp_utils.admin_theme.context_processor.admin_theme_settings',
                # 'openwisp_utils.context_processors.test_theme_helper',
            ],
        },
    }
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        'ATOMIC_REQUESTS': True,
    }
}

# POSTGRES_ENGINE = env("POSTGRES_ENGINE") # database engine
# POSTGRES_DB = env("POSTGRES_DB") # database name
# POSTGRES_PASSWORD = env("POSTGRES_PASSWORD") # database user password
# POSTGRES_USER = env("POSTGRES_USER") # database username
# POSTGRES_HOST = env("POSTGRES_HOST") # database host
# POSTGRES_PORT = env("POSTGRES_PORT") # database port

# POSTGRES_READY = (
#     POSTGRES_DB is not None
#     and POSTGRES_PASSWORD is not None
#     and POSTGRES_USER is not None
#     and POSTGRES_HOST is not None
#     and POSTGRES_PORT is not None
# )

# if POSTGRES_READY:
#     DATABASES = {
#         'default': {
#             'ENGINE': POSTGRES_ENGINE,
#             'NAME': POSTGRES_DB,
#             'USER': POSTGRES_USER,
#             'PASSWORD': POSTGRES_PASSWORD,
#             'HOST': POSTGRES_HOST,
#             'PORT': POSTGRES_PORT,
#             'ATOMIC_REQUESTS': True,
#         }
#     }

LOGGING = {
    'version': 1,
    'disable_existing_loggers': TESTING,
    'filters': {'require_debug_true': {'()': 'django.utils.log.RequireDebugTrue'}},
    'formatters': {
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {message}',
            'style': '{',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
    },
}

if not TESTING:
    LOGGING['handlers'].update(
        {
            'django.server': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'django.server',
            },
        }
    )
    LOGGING['loggers'] = {
        'django': {'handlers': ['console'], 'level': 'INFO'},
        'django.server': {
            'handlers': ['django.server'],
            'level': 'INFO',
            'propagate': False,
        },
        'openwisp_radius': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }

if not TESTING and SHELL:
    LOGGING['loggers'] = {
        'django.db': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        '': {
            # this sets root level logger to log debug and higher level
            # logs to console. All other loggers inherit settings from
            # root level logger.
            'handlers': ['console', 'django.server'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }

# AUTH_PASSWORD_VALIDATORS = [] # WARNING: for development only!

LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'America/Asuncion'  # used to replicate timezone related bug, do not change!
USE_I18N = True
USE_L10N = True
USE_TZ = True

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
PRIVATE_STORAGE_ROOT = os.path.join(MEDIA_ROOT, 'private')
MEDIA_URL = '/media/'
STATIC_URL = '/static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# for development only
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
EMAIL_PORT = '1025'


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

redis_host = os.getenv('REDIS_HOST', 'localhost')

OPENWISP_RADIUS_PASSWORD_RESET_URLS = {
    '__all__': (
        'http://localhost:8080/{organization}/password/reset/confirm/{uid}/{token}'
    ),
}

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

SENDSMS_BACKEND = 'sendsms.backends.console.SmsBackend'
OPENWISP_RADIUS_EXTRA_NAS_TYPES = (('cisco', 'Cisco Router'),('mikrotik', 'Mikrotik'),)

REST_AUTH = {
    'SESSION_LOGIN': False,
    'PASSWORD_RESET_SERIALIZER': 'openwisp_radius.api.serializers.PasswordResetSerializer',
    'REGISTER_SERIALIZER': 'openwisp_radius.api.serializers.RegisterSerializer',
}

ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = 'email_confirmation_success'
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = 'email_confirmation_success'

if not PARALLEL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://localhost/0',
            'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
        }
    }
# parallel testing with redis cache does not work
# so we use the local memory cache in this case
# we still keep redis for the standard non parallel tests
# to avoid having bad surprises in production
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'openwisp-users',
        }
    }

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# OPENWISP_RADIUS_PASSWORD_RESET_URLS = {
#     # use the uuid because the slug can change
#     # 'dabbd57a-11ca-4277-8dbb-ad21057b5ecd': 'https://org.com/{organization}/password/reset/confirm/{uid}/{token}',
#     # fallback in case the specific org page is not defined
#     '__all__': 'https://example.com/{{organization}/password/reset/confirm/{uid}/{token}',
# }

if TESTING:
    OPENWISP_RADIUS_SMS_TOKEN_MAX_USER_DAILY = 3
    OPENWISP_RADIUS_SMS_TOKEN_MAX_ATTEMPTS = 3
    OPENWISP_RADIUS_SMS_TOKEN_MAX_IP_DAILY = 4
    SENDSMS_BACKEND = 'sendsms.backends.dummy.SmsBackend'
else:
    OPENWISP_RADIUS_SMS_TOKEN_MAX_USER_DAILY = 10

OPENWISP_USERS_AUTH_API = True

# if os.environ.get('SAMPLE_APP', False):
#     INSTALLED_APPS.remove('openwisp_radius')
#     INSTALLED_APPS.append('openwisp_radius')
#     INSTALLED_APPS.remove('openwisp_users')
#     INSTALLED_APPS.append('openwisp_users')
#     EXTENDED_APPS = ('openwisp_utils', 'openwisp_users', 'plans')
#     OPENWISP_USERS_GROUP_MODEL = 'openwisp_users.Group'
#     OPENWISP_USERS_ORGANIZATION_MODEL = 'openwisp_users.Organization'
#     OPENWISP_USERS_ORGANIZATIONUSER_MODEL = 'openwisp_users.OrganizationUser'
#     OPENWISP_USERS_ORGANIZATIONOWNER_MODEL = 'openwisp_users.OrganizationOwner'
#     OPENWISP_USERS_ORGANIZATIONINVITATION_MODEL = 'openwisp_users.OrganizationInvitation'
#     OPENWISP_RADIUS_RADIUSREPLY_MODEL = 'openwisp_radius.RadiusReply'
#     OPENWISP_RADIUS_RADIUSGROUPREPLY_MODEL = 'openwisp_radius.RadiusGroupReply'
#     OPENWISP_RADIUS_RADIUSCHECK_MODEL = 'openwisp_radius.RadiusCheck'
#     OPENWISP_RADIUS_RADIUSGROUPCHECK_MODEL = 'openwisp_radius.RadiusGroupCheck'
#     OPENWISP_RADIUS_RADIUSACCOUNTING_MODEL = 'openwisp_radius.RadiusAccounting'
#     OPENWISP_RADIUS_NAS_MODEL = 'openwisp_radius.Nas'
#     OPENWISP_RADIUS_RADIUSUSERGROUP_MODEL = 'openwisp_radius.RadiusUserGroup'
#     OPENWISP_RADIUS_REGISTEREDUSER_MODEL = 'openwisp_radius.RadiusUserGroup'
#     OPENWISP_RADIUS_RADIUSPOSTAUTH_MODEL = 'openwisp_radius.RadiusPostAuth'
#     OPENWISP_RADIUS_RADIUSBATCH_MODEL = 'openwisp_radius.RadiusBatch'
#     OPENWISP_RADIUS_RADIUSGROUP_MODEL = 'openwisp_radius.RadiusGroup'
#     OPENWISP_RADIUS_RADIUSTOKEN_MODEL = 'openwisp_radius.RadiusToken'
#     OPENWISP_RADIUS_PHONETOKEN_MODEL = 'openwisp_radius.PhoneToken'
#     OPENWISP_RADIUS_REGISTEREDUSER_MODEL = 'openwisp_radius.RegisteredUser'
#     OPENWISP_RADIUS_ORGANIZATIONRADIUSSETTINGS_MODEL = (
#         'openwisp_radius.OrganizationRadiusSettings'
#     )
#     # Rename sample_app database
#     DATABASES['default']['NAME'] = os.path.join(BASE_DIR, 'openwisp_radius.db')
#     CELERY_IMPORTS = ('openwisp_radius.tasks', 'openwisp_notifications.tasks')

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


# ------------------------------------------------------------------ admin
OPENWISP_ADMIN_SITE_HEADER = 'GMTISP'
OPENWISP_ADMIN_SITE_TITLE = 'GMTISP Admin'



# ------------------------------------------------------------------ testing_app
OPENWISP_ADMIN_SITE_CLASS = 'testing_app.site.CustomAdminSite'
# only for automated test purposes
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'testing_app.api.throttling.CustomScopedRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {'anon': '20/hour'},
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        # 'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    }
}
OPENWISP_TEST_ADMIN_MENU_ITEMS = [{'model': 'testing_app.Project'}]



# ------------------------------------------------------------------ plans
    
PLANS_PLAN_MODEL = 'plans.Plan'
PLANS_BILLINGINFO_MODEL = 'plans.BillingInfo'
PLANS_USERPLAN_MODEL = 'plans.UserPlan'
PLANS_PRICING_MODEL = 'plans.Pricing'
PLANS_PLANPRICING_MODEL = 'plans.PlanPricing'
PLANS_QUOTA_MODEL = 'plans.Quota'
PLANS_PLANQUOTA_MODEL = 'plans.PlanQuota'
PLANS_ORDER_MODEL = 'plans.Order'
PLANS_INVOICE_MODEL = 'plans.Invoice'
PLANS_RECURRINGUSERPLAN_MODEL = 'plans.RecurringUserPlan'

# This is required for django-plans
PLANS_INVOICE_ISSUER = {
    'issuer_name': 'My Company Ltd',
    'issuer_street': '48th Suny street',
    'issuer_zipcode': '111-456',
    'issuer_city': 'Django City',
    'issuer_country': 'PL',
    'issuer_tax_number': 'PL123456789',
}

MANAGE_PY_PATH = os.environ.get('MANAGE_PY_PATH', './manage.py')
PLANS_CURRENCY = 'EUR'
ENABLE_FAKE_PAYMENTS = True
PLANS_TAX = Decimal('23.0')
PLANS_TAXATION_POLICY = 'plans.taxation.eu.EUTaxationPolicy'
PLANS_TAX_COUNTRY = 'PL'
PLANS_DEFAULT_COUNTRY = 'CZ'
PLANS_GET_COUNTRY_FROM_IP = True

PLANS_VALIDATORS = {
    'MAX_FOO_COUNT': 'example.foo.validators.max_foos_validator',
}

# PLANS_INVOICE_COUNTER_RESET = Invoice.NUMBERING.MONTHLY
# PLANS_INVOICE_NUMBER_FORMAT = {{ invoice.issued|date:'d/m/Y' }}
# PLANS_INVOICE_NUMBER_FORMAT = '{{ invoice.number }}/{{ invoice.issued|date='m/FV/Y' }}'
# from urllib.parse import urljoin
# PLANS_INVOICE_LOGO_URL = urljoin(STATIC_URL, 'my_logo.png')
# PLANS_INVOICE_TEMPLATE = 'plans/invoices/PL_EN.html'
# PLANS_ORDER_EXPIRATION = 14
# PLANS_EXPIRATION_REMIND = [1, 3 , 7] # User will receive notification before 7 , 3 and 1 day to account expire.
# PLANS_DEFAULT_GRACE_PERIOD = 30 # New account default plan expiration period counted in days.
# SEND_PLANS_EMAILS = True



# ------------------------------------------------------------------ plans payments
from typing import Dict, Tuple

PAYMENT_MODEL = 'plans.Payment'

PAYMENT_VARIANTS: Dict[str, Tuple[str, Dict]] = {
    'default': ('payments.dummy.DummyProvider', {}),
}

