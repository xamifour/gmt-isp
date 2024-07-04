from django.utils.functional import cached_property
from swapper import load_model
import logging

from .utils import get_db_for_user


logger = logging.getLogger(__name__)

class OrganizationDbAdminMixin:
    """
    Mixin to ensure admin actions are performed on the right database.
    """
    @cached_property
    def db(self):
        """
        Return the database alias for the current user.
        """
        try:
            return get_db_for_user(self.request.user)
        except Exception as e:
            # logger.error(f"Error determining database for user: {e}")
            return 'default'

    def get_queryset(self, request):
        """
        Return queryset using the correct database.
        """
        self.request = request
        try:
            qs = super().get_queryset(request)
            return qs.using(self.db)
        except Exception as e:
            # logger.error(f"Error getting queryset: {e}")
            return super().get_queryset(request)


    def save_model(self, request, obj, form, change):
        self.request = request
        try:
            OrganizationUser = load_model('openwisp_users', 'OrganizationUser')
            organization_user = OrganizationUser.objects.get(user=request.user)
            obj.organization = organization_user.organization
        except OrganizationUser.DoesNotExist:
            pass
        except Exception as e:
            # logger.error(f"Error setting organization for the model: {e}")
            pass

        try:
            obj.save(using=self.db)
        except Exception as e:
            # logger.error(f"Error saving model: {e}")
            pass
        else:
            super().save_model(request, obj, form, change)


    def delete_model(self, request, obj):
        """
        Delete the model using the correct database.
        """
        self.request = request
        try:
            obj.delete(using=self.db)
        except Exception as e:
            # logger.error(f"Error deleting model: {e}")
            obj.delete()  # Fallback to default behavior

    def get_object(self, request, object_id, from_field=None):
        """
        Retrieve an object using the correct database.
        """
        self.request = request
        try:
            queryset = self.get_queryset(request)
            return queryset.get(**{from_field or 'pk': object_id})
        except Exception as e:
            # logger.error(f"Error getting object: {e}")
            return super().get_object(request, object_id, from_field)
        
