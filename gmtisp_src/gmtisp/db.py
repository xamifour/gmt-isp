import environ
import logging
import os
from pathlib import Path

# Initialize logger
logger = logging.getLogger(__name__)

# Determine base directory and load environment variables
BASE_DIR = Path(__file__).resolve().parent
env = environ.Env()
env_file = BASE_DIR / '.env'
env.read_env(str(env_file))  # Load environment variables from .env file

def get_organization_slugs():
    """
    Fetches organization slugs dynamically based on environment variables.
    Assumes organization slugs are defined as environment variables with '_DB_NAME' suffix.
    """
    slugs = []
    # Iterate over os.environ to fetch all environment variables
    for var_name, value in os.environ.items():
        if var_name.endswith('_DB_NAME'):
            slug = var_name[:-len('_DB_NAME')].lower().replace('_', '')  # Extract organization slug
            slugs.append(slug)
    return slugs

def get_organization_db_config(organization):
    """
    Fetches the database configuration for a specific organization from environment variables.
    If not available, uses default database configuration.
    """
    try:
        # Try to fetch organization-specific variables
        organization_vars = {
            'ENGINE': env('POSTGRES_ENGINE'),
            'NAME': env(f"{organization.upper()}_DB_NAME", default=None),
            'USER': env(f"{organization.upper()}_DB_USER", default=None),
            'PASSWORD': env(f"{organization.upper()}_DB_PASSWORD", default=None),
            'HOST': env(f"{organization.upper()}_DB_HOST", default=None),
            'PORT': int(env(f"{organization.upper()}_DB_PORT", default=5432)),  # Default to 5432 if not set
        }

        # Check if any required organization-specific variable is missing
        if None in organization_vars.values():
            logger.warning(f"Organization '{organization}' missing specific DB configuration, using default DB configuration.")
            # If organization-specific DB config is incomplete, fall back to default
            return get_default_db_config()
        
        return organization_vars

    except KeyError as e:
        logger.error(f"Missing environment variables for {organization}: {str(e)}")
        return get_default_db_config()

def get_default_db_config():
    """
    Fetches the default database configuration from environment variables.
    """
    try:
        default_vars = {
            'ENGINE': env('POSTGRES_ENGINE'),
            'NAME': env('DEFAULT_DB_NAME'),
            'USER': env('DEFAULT_DB_USER'),
            'PASSWORD': env('DEFAULT_DB_PASSWORD'),
            'HOST': env('DEFAULT_DB_HOST'),
            'PORT': int(env('DEFAULT_DB_PORT')),
        }

        # Check for missing default variables
        missing_vars = [key for key, value in default_vars.items() if not value]
        if missing_vars:
            missing_vars_str = ', '.join(missing_vars)
            logger.error(f"Missing default environment variables: {missing_vars_str}")
            raise KeyError(f"Missing default environment variables: {missing_vars}")
        
        return default_vars

    except KeyError as e:
        logger.error(f"Error fetching default DB config: {str(e)}")
        raise

def get_organization_db(organization=None):
    """
    Returns the database configuration for a specific organization or the default configuration 
    if no organization is specified.
    """
    if organization:
        return get_organization_db_config(organization)
    return get_default_db_config()

# Ensure default database is set up first
DATABASES = {
    'default': get_default_db_config(),  # Make sure the default DB config is applied
}

# # Add organization-specific configurations dynamically
# for org_slug in get_organization_slugs():
#     db_alias = f"db_{org_slug}"
#     DATABASES[db_alias] = get_organization_db(org_slug)  # Organization-specific configurations

# Logging for debugging
logger.info("DATABASES configured: %s", DATABASES)





# import environ
# import logging
# import os
# from pathlib import Path

# # Initialize logger
# logger = logging.getLogger(__name__)

# # Determine base directory and load environment variables
# BASE_DIR = Path(__file__).resolve().parent
# env = environ.Env()
# env_file = BASE_DIR / '.env'
# env.read_env(str(env_file))  # Load environment variables from .env file

# def get_organization_slugs():
#     """
#     Fetches organization slugs dynamically based on environment variables.
#     Assumes organization slugs are defined as environment variables with '_DB_NAME' suffix.
#     """
#     slugs = []
#     # Iterate over os.environ to fetch all environment variables
#     for var_name, value in os.environ.items():
#         if var_name.endswith('_DB_NAME'):
#             slug = var_name[:-len('_DB_NAME')].lower().replace('_', '')  # Extract organization slug
#             slugs.append(slug)
#     return slugs

# def get_organization_db_config(organization):
#     """
#     Fetches the database configuration for a specific organization from environment variables.
#     """
#     organization_vars = {
#         # 'ENGINE': env(f"{organization.upper()}_DB_ENGINE"),
#         'ENGINE': env('POSTGRES_ENGINE'),
#         'NAME': env(f"{organization.upper()}_DB_NAME"),
#         'USER': env(f"{organization.upper()}_DB_USER"),
#         'PASSWORD': env(f"{organization.upper()}_DB_PASSWORD"),
#         'HOST': env(f"{organization.upper()}_DB_HOST"),
#         'PORT': int(env(f"{organization.upper()}_DB_PORT")),  # Convert PORT to integer if necessary
#     }
#     # Check for missing variables
#     missing_vars = [key for key, value in organization_vars.items() if not value]
#     if missing_vars:
#         missing_vars_str = ', '.join(missing_vars)
#         logger.error(f"Missing environment variables for {organization}: {missing_vars_str}")
#         raise KeyError(f"Missing environment variables for {organization}: {missing_vars}")
#     return organization_vars

# def get_default_db_config():
#     """
#     Fetches the default database configuration from environment variables.
#     """
#     default_vars = {
#         'ENGINE': env('POSTGRES_ENGINE'),
#         'NAME': env('DEFAULT_DB_NAME'),
#         'USER': env('DEFAULT_DB_USER'),
#         'PASSWORD': env('DEFAULT_DB_PASSWORD'),
#         'HOST': env('DEFAULT_DB_HOST'),
#         'PORT': int(env('DEFAULT_DB_PORT')),
#     }
#     # Check for missing variables
#     missing_vars = [key for key, value in default_vars.items() if not value]
#     if missing_vars:
#         missing_vars_str = ', '.join(missing_vars)
#         logger.error(f"Missing default environment variables: {missing_vars_str}")
#         raise KeyError(f"Missing default environment variables: {missing_vars}")
    
#     return default_vars

# def get_organization_db(organization=None):
#     """
#     Returns the database configuration for a specific organization or the default configuration 
#     if no organization is specified.
#     """
#     if organization:
#         return get_organization_db_config(organization)
#     return get_default_db_config()

# # Dynamically populate the DATABASES setting with default and organization-specific configurations
# DATABASES = {
#     'default': get_organization_db(),  # Default configuration
# }

# # # Add organization-specific configurations dynamically
# # for org_slug in get_organization_slugs():
# #     db_alias = f"db_{org_slug}"
# #     DATABASES[db_alias] = get_organization_db(org_slug)  # Organization-specific configurations

# # Logging for debugging
# logger.info("DATABASES configured: %s", DATABASES)






# # using a static dictionary for DATABASES
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
