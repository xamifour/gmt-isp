
import logging

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils.functional import cached_property

from openwisp_utils.admin_theme.filters import AutocompleteFilter
from swapper import load_model

from openwisp_utils.utils import get_db_for_user
from .widgets import SHARED_SYSTEMWIDE_LABEL, OrganizationAutocompleteSelect
from .models import Organization

logger = logging.getLogger(__name__)
User = get_user_model()
OrganizationUser = load_model('openwisp_users', 'OrganizationUser')


class MultitenantAdminMixin:
    """
    A mixin that combines multitenant filtering with organization-based database selection.
    Ensures that the queryset is retrieved from the correct database and filtered based on
    the user's associated organizations.
    """
    multitenant_shared_relations = None  
    multitenant_parent = None

    def __init__(self, *args, **kwargs):
        """
        Initialize the mixin, ensuring shared relations are set.
        """
        super().__init__(*args, **kwargs)
        self._initialize_shared_relations()

    def _initialize_shared_relations(self):
        """
        Initialize the multitenant_shared_relations attribute.
        Ensures it is a list and includes multitenant_parent if defined.
        """
        shared_relations = list(self.multitenant_shared_relations or [])
        if self.multitenant_parent and self.multitenant_parent not in shared_relations:
            shared_relations.append(self.multitenant_parent)
        self.multitenant_shared_relations = shared_relations

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
        Return queryset filtered by the user's associated organizations
        and using the correct database.
        """
        self.request = request
        try:
            qs = super().get_queryset(request)
            qs = qs.using(self.db) # Apply database context
            user = request.user
            
            # Allow superusers full access
            if user.is_superuser:
                return qs
            
            return self._filter_queryset_by_user(qs, user)
        except Exception as e:
            logger.error(f"Error getting queryset: {e}")
            return super().get_queryset(request)
        
    def _filter_queryset_by_user(self, qs, user):
        """
        Filter the queryset based on the user's associated organizations.
        """
        if self.model == User:
            return self._filter_users_for_admin(qs, user)
        elif hasattr(self.model, 'organization'):
            return qs.filter(organization__in=user.organizations_managed)
        elif self.model.__name__ == 'Organization':
            return qs.filter(pk__in=user.organizations_managed)
        elif self.multitenant_parent:
            qsarg = f'{self.multitenant_parent}__organization__in'
            return qs.filter(**{qsarg: user.organizations_managed})
        return qs

    def _filter_users_for_admin(self, qs, user):
        user_ids = (
            OrganizationUser.objects.filter(
                organization_id__in=user.organizations_managed
            )
            .values_list('user_id', flat=True)
            .distinct()
        )
        return qs.filter(id__in=user_ids, is_superuser=False)

    def _edit_form(self, request, form):
        """
        Modify form querysets to show only relevant organizations and relations.
        """
        user = request.user
        org_field = form.base_fields.get('organization')

        if user.is_superuser and org_field and not org_field.required:
            org_field.empty_label = 'Shared Systemwide'
        elif not user.is_superuser:
            self._restrict_form_fields(form, user)

    def _restrict_form_fields(self, form, user):
        orgs_pk = user.organizations_managed
        org_field = form.base_fields.get('organization')

        if org_field:
            org_field.queryset = org_field.queryset.filter(pk__in=orgs_pk)
            org_field.empty_label = None
        
        q = Q(organization__in=orgs_pk) | Q(organization=None)
        for field_name in self.multitenant_shared_relations:
            if field_name in form.base_fields:
                form.base_fields[field_name].queryset = form.base_fields[field_name].queryset.filter(q)

    def get_form(self, request, obj=None, **kwargs):
        """
        Return the form, modified for multitenant behavior.
        """
        form = super().get_form(request, obj, **kwargs)
        self._edit_form(request, form)
        return form

    def get_formset(self, request, obj=None, **kwargs):
        """
        Return the formset, modified for multitenant behavior.
        """
        formset = super().get_formset(request, obj, **kwargs)
        self._edit_form(request, formset.form)
        return formset

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Customize the form field for foreign keys to use the organization autocomplete widget.
        """
        if db_field.name == 'organization':
            kwargs['widget'] = OrganizationAutocompleteSelect(
                db_field, self.admin_site, using=kwargs.get('using')
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        """
        Save the model using the correct database.
        """
        self.request = request
        try:
            OrganizationUser = load_model('openwisp_users', 'OrganizationUser')

            # For superusers, allow saving without organization
            if request.user.is_superuser:
                obj.organization = None  # Set to None or handle accordingly
            elif isinstance(obj, User):  # Check if we're saving a User
                if request.user.organizations_managed:
                    # Get the current user's organization
                    organization_user = OrganizationUser.objects.get(user=request.user)
                    obj.organization = organization_user.organization
                else:
                    # Raise error if the user has no organizations and is not a superuser
                    raise ValidationError('The user is not associated with any organization.')
            else:
                # For other models, get organization from the current user
                organization_user = OrganizationUser.objects.get(user=request.user)
                obj.organization = organization_user.organization

        except OrganizationUser.DoesNotExist:
            raise ValidationError('The user is not associated with any organization.')
        except Exception as e:
            logger.error(f"Error setting organization for the model: {e}")
            raise ValidationError(f'Error setting organization for the model: {e}')

        try:
            obj.save(using=self.db)
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            raise e  # Consider raising the error here to propagate it
        else:
            super().save_model(request, obj, form, change)

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
            
    # def has_add_permission(self, request):
    #     """
    #     Allow add permission only if the user belongs to an organization.
    #     """
    #     return request.user.is_superuser or bool(request.user.organizations_managed)

    # def has_change_permission(self, request, obj=None):
    #     """
    #     Allow change permission only if the user is associated with the object's organization.
    #     """
    #     if request.user.is_superuser:
    #         return True
    #     if obj and hasattr(obj, 'organization'):
    #         return obj.organization in request.user.organizations_managed
    #     return False

    # def has_delete_permission(self, request, obj=None):
    #     """
    #     Allow delete permission only if the user is associated with the object's organization.
    #     """
    #     if request.user.is_superuser:
    #         return True
    #     if obj and hasattr(obj, 'organization'):
    #         return obj.organization in request.user.organizations_managed
    #     return False


class MultitenantOrgFilter(AutocompleteFilter):
    """
    Admin filter that shows only organizations the current
    user is associated with in its available choices
    """

    field_name = 'organization'
    parameter_name = 'organization'
    org_lookup = 'id__in'
    title = _('organization')
    widget_attrs = AutocompleteFilter.widget_attrs.copy()
    widget_attrs.update({'data-empty-label': SHARED_SYSTEMWIDE_LABEL})


class MultitenantRelatedOrgFilter(MultitenantOrgFilter):
    """
    Admin filter that shows only objects which have a relation with
    one of the organizations the current user is associated with
    """

    org_lookup = 'organization__in'
