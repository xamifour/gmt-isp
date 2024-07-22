from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from openwisp_utils.admin_theme.filters import AutocompleteFilter
from swapper import load_model

from .widgets import SHARED_SYSTEMWIDE_LABEL, OrganizationAutocompleteSelect

User = get_user_model()
OrganizationUser = load_model('openwisp_users', 'OrganizationUser')


class MultitenantAdminMixin:
    """
    Mixin to make a ModelAdmin class multitenant.
    Users will see only the objects related to the organizations
    they are associated with.
    """
    multitenant_shared_relations = None  # List of related fields that should be considered shared across organizations.
    multitenant_parent = None

    def __init__(self, *args, **kwargs):
        """
        Initialize the mixin, ensuring shared relations are set.
        """
        super().__init__(*args, **kwargs)
        parent = self.multitenant_parent
        shared_relations = self.multitenant_shared_relations or []
        shared_relations = list(shared_relations)  # Copy to avoid modifying class attribute
        if parent and parent not in shared_relations:
            shared_relations.append(parent)  # Add multitenant_parent to multitenant_shared_relations if necessary
        self.multitenant_shared_relations = shared_relations

    def get_queryset(self, request):
        """
        Return queryset filtered by the user's associated organizations.
        """
        qs = super().get_queryset(request)
        user = request.user

        # Allow superusers to see all data
        if user.is_superuser:
            return qs

        # Handle different model cases
        if self.model == User:
            return self.multitenant_behaviour_for_user_admin(request)
        elif hasattr(self.model, 'organization'):
            return qs.filter(organization__in=user.organizations_managed)
        elif self.model.__name__ == 'Organization':
            return qs.filter(pk__in=user.organizations_managed)
        elif self.multitenant_parent:
            qsarg = f'{self.multitenant_parent}__organization__in'
            return qs.filter(**{qsarg: user.organizations_managed})
        else:
            return qs

    def multitenant_behaviour_for_user_admin(self, request):
        """
        Filter users based on the operator's managed organizations and hide superusers.
        """
        user = request.user
        qs = super().get_queryset(request)
        if user.is_superuser:
            return qs

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
        fields = form.base_fields
        user = request.user
        org_field = fields.get('organization')

        if user.is_superuser and org_field and not org_field.required:
            org_field.empty_label = 'Shared Systemwide'
        elif not user.is_superuser:
            orgs_pk = user.organizations_managed
            if org_field:
                org_field.queryset = org_field.queryset.filter(pk__in=orgs_pk)
                org_field.empty_label = None
            q = Q(organization__in=orgs_pk) | Q(organization=None)
            for field_name in self.multitenant_shared_relations:
                if field_name in fields:
                    fields[field_name].queryset = fields[field_name].queryset.filter(q)

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
