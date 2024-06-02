import environ
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve(strict=True).parent

env = environ.Env()
env.read_env()

# ------------------------------------------------------------------------------ database
# DATABASES for different organisations

'''
Dynamically fetching database configurations based on the organization name 
from the environment variables.
'''

def get_organization_db_config(organization):
    try:
        return {
            'ENGINE': env('POSTGRES_ENGINE'),
            # 'ENGINE': env(f"{organization.upper()}_DB_ENGINE"),
            'NAME': env(f"{organization.upper()}_DB_NAME"),
            'USER': env(f"{organization.upper()}_DB_USER"),
            'PASSWORD': env(f"{organization.upper()}_DB_PASSWORD"),
            'HOST': env(f"{organization.upper()}_DB_HOST"),
            'PORT': env(f"{organization.upper()}_DB_PORT"),
        }
    except KeyError as e:
        logger.error(f"Missing environment variable for {organization}: {e}")
        raise

def get_default_db_config():
    return {
        'ENGINE': env('POSTGRES_ENGINE'),
        'NAME': env('DEFAULT_DB_NAME'),
        'USER': env('DEFAULT_DB_USER'),
        'PASSWORD': env('DEFAULT_DB_PASSWORD'),
        'HOST': env('DEFAULT_DB_HOST'),
        'PORT': env('DEFAULT_DB_PORT'),
    }

def get_organization_db(organization):
    if organization:
        return get_organization_db_config(organization)
    return get_default_db_config()

DATABASES = {
    'default': get_default_db_config(),
}



# # using a static dictionary for DATABASES
# import sys

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'gmtispdb.sqlite3',
#         'ATOMIC_REQUESTS': True,
#     },
#     'default': {
#         'ENGINE': env('POSTGRES_ENGINE'),
#         'NAME': env('DEFAULT_DB_NAME'),
#         'USER': env('DEFAULT_DB_USER'),
#         'PASSWORD': env('DEFAULT_DB_PASSWORD'),
#         'HOST': env('DEFAULT_DB_HOST'),
#         'PORT': env('DEFAULT_DB_PORT'),
#     },
#     'gies': {
#         'ENGINE': env('POSTGRES_ENGINE'),
#         'NAME': env('GIES_DB_NAME'),
#         'USER': env('GIES_DB_USER'),
#         'PASSWORD': env('GIES_DB_PASSWORD'),
#         'HOST': env('GIES_DB_HOST'),
#         'PORT': env('GIES_DB_PORT'),
#     },
#     'gigmeg': {
#         'ENGINE': env('POSTGRES_ENGINE'),
#         'NAME': env('GIGMEG_DB_NAME'),
#         'USER': env('GIGMEG_DB_USER'),
#         'PASSWORD': env('GIGMEG_DB_PASSWORD'),
#         'HOST': env('GIGMEG_DB_HOST'),
#         'PORT': env('GIGMEG_DB_PORT'),
#     },
# }

# if 'test' in sys.argv:
#     DATABASES['default'] = DATABASES['test']