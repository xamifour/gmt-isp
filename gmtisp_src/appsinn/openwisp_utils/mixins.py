from django.utils.functional import cached_property

from .utils import get_db_for_user


class OrganizationDbMixin:
    @cached_property
    def db(self):
        user = self.request.user
        if user.is_authenticated:
            return get_db_for_user(user)  # Modified to use get_db_for_user
        return 'default'

    def get_queryset(self):
        return super().get_queryset().using(self.db)  # Ensure queryset uses the correct db
    
    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return super().get_object(queryset=queryset)  # Ensure object retrieval uses the correct db