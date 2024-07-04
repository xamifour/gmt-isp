import environ
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve(strict=True).parent

env = environ.Env()
env.read_env(BASE_DIR / '.env')  # Ensure the .env file is loaded

def get_organization_db_config(organization):
    """
    Fetch the database configuration for a specific organization from environment variables.
    """
    try:
        return {
            # 'ENGINE': env(f"{organization.upper()}_DB_ENGINE"),
            'ENGINE': env('POSTGRES_ENGINE'),
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
    """
    Fetch the default database configuration from environment variables.
    """
    return {
        'ENGINE': env('POSTGRES_ENGINE'),
        'NAME': env('DEFAULT_DB_NAME'),
        'USER': env('DEFAULT_DB_USER'),
        'PASSWORD': env('DEFAULT_DB_PASSWORD'),
        'HOST': env('DEFAULT_DB_HOST'),
        'PORT': env('DEFAULT_DB_PORT'),
    }

def get_organization_db(organization):
    """
    Returns the database configuration for a specific organization 
    or the default configuration if no organization is specified.
    """
    if organization:
        return get_organization_db_config(organization)
    return get_default_db_config()

# Dynamically populate the DATABASES setting
DATABASES = {
    'default': get_default_db_config(),
}

# # Example of adding a specific organization's database configuration
# organizations = ['org1', 'org2', 'org3']  # List of organization slugs
# for org in organizations:
#     db_alias = f"{org}_db"
#     DATABASES[db_alias] = get_organization_db(org)



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