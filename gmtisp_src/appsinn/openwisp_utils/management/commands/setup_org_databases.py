# project dir/
# ├── management/
# │   ├── __init__.py
# │   ├── commands/
# │       ├── __init__.py
# │       ├── setup_org_databases.py

# project dir/management/commands/setup_org_databases.py

import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.cache import cache

from openwisp_users.models import Organization
from gmtisp.db import get_organization_db


logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Set up databases for all organizations'

    def handle(self, *args, **kwargs):
        try:
            orgs = cache.get('organizations')
            if not orgs:
                orgs = Organization.objects.all()
                cache.set('organizations', orgs, timeout=3600)  # Cache for 1 hour

            for org in orgs:
                db_name = f"db_{org.slug}"
                db_config = get_organization_db(org.slug)
                settings.DATABASES[db_name] = db_config
                logger.info(f"Added database configuration for {org.name}: {db_config}")

            logger.debug(f"Final DATABASES settings: {settings.DATABASES}")

        except Exception as e:
            logger.error(f"Error setting up databases: {e}")
            self.stderr.write(self.style.ERROR(f"Error: {e}"))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully set up databases for all organizations'))
