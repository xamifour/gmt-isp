import logging

from django.utils.functional import cached_property
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.views import View
from django.contrib.auth import get_user_model

from swapper import load_model

User = get_user_model()
OrganizationUser = load_model('openwisp_users', 'OrganizationUser')

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
            logger.error(f"Error determining database for user: {e}")
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
            logger.error(f"Error getting queryset: {e}")
            return super().get_queryset(request)

    def save_model(self, request, obj, form, change):
        self.request = request
        try:
            OrganizationUser = load_model('openwisp_users', 'OrganizationUser')
            organization_user = OrganizationUser.objects.get(user=request.user)
            obj.organization = organization_user.organization
        except OrganizationUser.DoesNotExist:
            raise ValidationError('The user is not associated with any organization.')
        except Exception as e:
            logger.error(f"Error setting organization for the model: {e}")
            raise ValidationError(f'Error setting organization for the plan: {e}')
        
        try:
            obj.save(using=self.db)
        except Exception as e:
            logger.error(f"Error saving model: {e}")
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
            logger.error(f"Error deleting model: {e}")
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
            logger.error(f"Error getting object: {e}")
            return super().get_object(request, object_id, from_field)


# for views
class MultiTenantMixin(View):
    """
    Mixin to filter views by user's organization.
    """
    organization_field = 'organization'  # Field name to filter by organization, override in subclass

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """
        Ensure the user is authenticated and has permission to access the view.
        """
        if not self.has_permission(request):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """
        Filter queryset based on the user's associated organizations.
        Superusers have access to all objects.
        """
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_superuser:
            return queryset
        return queryset.filter(**{self.organization_field + '__in': user.organizations_dict.keys()})

    def has_permission(self, request):
        """
        Override this method to provide custom permission logic.
        By default, it checks if the user is authenticated.
        """
        return request.user.is_authenticated

    def get_object(self, *args, **kwargs):
        """
        Ensure the user has permission to access the specific object.
        Superusers have access to all objects.
        """
        obj = super().get_object(*args, **kwargs)
        user = self.request.user
        if user.is_superuser or user.is_member(obj.organization):
            return obj
        raise PermissionDenied

    def form_valid(self, form):
        """
        Ensure the user is associated with the organization on form submission.
        Superusers can bypass this check.
        """
        user = self.request.user
        obj = form.save(commit=False)
        if user.is_superuser or user.is_member(obj.organization):
            return super().form_valid(form)
        raise PermissionDenied


class SuperuserPermissionMixin:
    def has_add_permission(self, request, obj=None):
        # Allow add permission only for superusers
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        # Allow delete permission only for superusers
        return request.user.is_superuser
    

