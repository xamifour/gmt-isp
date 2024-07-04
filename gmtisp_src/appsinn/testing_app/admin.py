from django.contrib import admin
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from openwisp_utils.admin import (
    AlwaysHasChangedMixin,
    HelpTextStackedInline,
    ReadOnlyAdmin,
    ReceiveUrlAdmin,
    TimeReadonlyAdminMixin,
    UUIDAdmin,
)
from openwisp_utils.admin_theme.filters import (
    AutocompleteFilter,
    InputFilter,
    SimpleInputFilter,
)

from openwisp_users.multitenancy import (
    MultitenantAdminMixin,
    MultitenantOrgFilter,
    MultitenantRelatedOrgFilter,
)

from .models import (
    Book,
    Operator,
    Project,
    Shelf,
    Library, 
    Tag, 
    Template,
    OrganizationRadiusSettings,
    RadiusAccounting,
)

# admin.site.unregister(User)


class BaseAdmin(MultitenantAdminMixin, admin.ModelAdmin):
    pass


class AutoShelfFilter(AutocompleteFilter):
    title = _('shelf')
    field_name = 'shelf'
    parameter_name = 'shelf__id'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'is_staff', 'is_superuser', 'is_active']
    list_filter = [
        ('username', InputFilter),
        ('shelf', InputFilter),
        'is_staff',
        'is_superuser',
        'is_active',
    ]
    search_fields = ('username',)


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name']
    list_filter = ['project__name']  # DO NOT CHANGE: used for testing filters


class OperatorForm(AlwaysHasChangedMixin, ModelForm):
    pass


class OperatorInline(HelpTextStackedInline):
    model = Operator
    form = OperatorForm
    extra = 0
    help_text = {
        'text': _('Only added operators will have permission to access the project.'),
        'documentation_url': 'https://github.com/openwisp/openwisp-utils/',
    }


@admin.register(Project)
class ProjectAdmin(UUIDAdmin, ReceiveUrlAdmin):
    inlines = [OperatorInline]
    list_display = ('name',)
    fields = ('uuid', 'name', 'key', 'receive_url')
    readonly_fields = ('uuid', 'receive_url')
    receive_url_name = 'receive_project'



class ReverseBookFilter(AutocompleteFilter):
    title = _('Book')
    field_name = 'book'
    parameter_name = 'book'


class AutoOwnerFilter(AutocompleteFilter):
    title = _('owner')
    field_name = 'owner'
    parameter_name = 'owner_id'


# @admin.register(RadiusAccounting)
# class RadiusAccountingAdmin(ReadOnlyAdmin):
#     list_display = ['session_id', 'username']
#     fields = ['session_id', 'username']


# @admin.register(OrganizationRadiusSettings)
# class OrganizationRadiusSettingsAdmin(admin.ModelAdmin):
#     pass


class ShelfFilter(MultitenantRelatedOrgFilter):
    field_name = 'shelf'
    parameter_name = 'shelf'
    title = _('Shelf')

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(name__icontains=self.value())


class ShelfAdmin(TimeReadonlyAdminMixin, BaseAdmin):
    # DO NOT CHANGE: used for testing filters
    list_display = ['name', 'organization']
    fields = ['name', 'organization', 'tags', 'created', 'modified']
    search_fields = ['name']
    multitenant_shared_relations = ['tags']
    list_filter = [
        MultitenantOrgFilter,
        ShelfFilter,
        ['books_type', InputFilter],
        ['id', InputFilter],
        AutoOwnerFilter,
        'books_type',
        ReverseBookFilter,
    ]


class BookAdmin(BaseAdmin):
    list_display = ['name', 'author', 'organization', 'shelf']
    list_filter = [
        'name',
        MultitenantOrgFilter,
        ShelfFilter,
        AutoShelfFilter,
    ]
    fields = ['name', 'author', 'organization', 'shelf', 'created', 'modified']
    multitenant_shared_relations = ['shelf']

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(
            {
                'additional_buttons': [
                    {
                        'type': 'button',
                        'url': 'DUMMY',
                        'class': 'previewbook',
                        'value': 'Preview book',
                    },
                    {
                        'type': 'button',
                        'url': 'DUMMY',
                        'class': 'downloadbook',
                        'value': 'Download book',
                    },
                ]
            }
        )
        return super().change_view(request, object_id, form_url, extra_context)


class TemplateAdmin(BaseAdmin):
    pass


class TagAdmin(BaseAdmin):
    pass


admin.site.register(Shelf, ShelfAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Template, TemplateAdmin)
admin.site.register(Library)
admin.site.register(Tag, TagAdmin)