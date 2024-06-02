# admin_mixins.py

from django.utils.functional import cached_property

from openwisp_utils.utils import get_db_for_user


class OrganizationDbAdminMixin:
    """
    Mixin to ensure admin actions are performed on the right database.
    """
    @cached_property
    def db(self):
        return get_db_for_user(self.request.user)

    def get_queryset(self, request):
        self.request = request
        qs = super().get_queryset(request)
        return qs.using(self.db)
    
    def save_model(self, request, obj, form, change):
        self.request = request
        obj.save(using=self.db)

    def delete_model(self, request, obj):
        self.request = request
        obj.delete(using=self.db)

    def get_object(self, request, object_id, from_field=None):
        self.request = request
        return super().get_object(request, object_id, from_field)



# class OrganizationDbAdminMixin(OrganizationDbMixin):
#     """
#     Mixin to ensure admin actions are performed on the right database.
#     """
#     def save_model(self, request, obj, form, change):
#         obj.save(using=get_db_for_user(request.user))

#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         return qs.using(get_db_for_user(request.user))# admin_mixins.py