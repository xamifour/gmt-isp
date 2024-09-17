import logging
from django.contrib.auth import get_user_model
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from allauth.account.models import EmailAddress

from gmtisp_billing.models import Plan, UserPlan, Order
from .forms import UserCreationForm, UserChangeForm, OrganizationForm
from .models import Organization, OrganizationUser

User = get_user_model()
logger = logging.getLogger(__name__)

def user_not_allowed_to_change_owner(user, obj):
    return (
        obj
        and not user.is_superuser
        and user.pk != obj.pk
        and obj.is_owner_of_any_organization
    )

class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'openwisp_users/users/user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.all()
        return User.objects.filter(openwisp_users_organizationuser__organization__in=self.request.user.organizations_managed)

class UserCreateView(LoginRequiredMixin, CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'openwisp_users/users/user_form.html'
    success_url = '/users/'  # Add the success_url attribute

    def form_valid(self, form):
        response = super().form_valid(form)
        EmailAddress.objects.add_email(self.request, user=self.object, email=self.object.email, confirm=True, signup=True)
        if not self.request.user.is_superuser:
            OrganizationUser.objects.create(user=self.object, organization_id=self.request.user.organizations_managed[0], is_admin=False)
        return response

class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserChangeForm
    template_name = 'openwisp_users/users/user_form.html'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if user_not_allowed_to_change_owner(self.request.user, obj) or (obj.is_superuser and not self.request.user.is_superuser):
            raise PermissionDenied
        return obj


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'openwisp_users/users/user_detail.html'
    context_object_name = 'user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        # user = self.request.user

        # user_plan = UserPlan.objects.select_related('plan').filter(user=self.object).first()
        # if user_plan:
        #     context['current_plan'] = user_plan.plan
        # else:
        #     logger.info(f'No UserPlan found for user {self.object.id}')
        #     context['current_plan'] = None

        # Get the current plan for the user, or return default plan
        if hasattr(user, 'userplan'):
            current_plan = user.userplan.get_current_plan()
        else:
            current_plan = None

        if current_plan:
            # Get the most recent 5 completed orders for the user
            recent_orders = Order.objects.filter(
                user=user,
                # plan=current_plan,
                status=Order.STATUS.COMPLETED
            ).order_by('-completed')[:5]

        context['current_plan'] = current_plan
        context['recent_orders'] = recent_orders  
        # Current order for the current plan of the logged in user
        context['current_order'] = recent_orders.first()
        return context


class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'openwisp_users/users/user_confirm_delete.html'
    success_url = '/users/'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if user_not_allowed_to_change_owner(self.request.user, self.object) or (self.object.is_superuser and not self.request.user.is_superuser):
            raise PermissionDenied
        success_url = self.get_success_url()
        self.object.delete()
        return redirect(success_url)

class OrganizationListView(LoginRequiredMixin, ListView):
    model = Organization
    template_name = 'openwisp_users/organizations/organization_list.html'
    context_object_name = 'organizations'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Organization.objects.all()
        return Organization.objects.filter(pk__in=self.request.user.organizations_managed)

class OrganizationCreateView(LoginRequiredMixin, CreateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'openwisp_users/organizations/organization_form.html'

class OrganizationUpdateView(LoginRequiredMixin, UpdateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'openwisp_users/organizations/organization_form.html'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not self.request.user.is_superuser and not self.request.user.is_manager(obj):
            raise PermissionDenied
        return obj

class OrganizationDetailView(LoginRequiredMixin, DetailView):
    model = Organization
    template_name = 'openwisp_users/organizations/organization_detail.html'
    context_object_name = 'organization'

class OrganizationDeleteView(LoginRequiredMixin, DeleteView):
    model = Organization
    template_name = 'openwisp_users/organizations/organization_confirm_delete.html'
    success_url = '/organizations/'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.request.user.is_superuser and not self.request.user.is_manager(self.object):
            raise PermissionDenied
        success_url = self.get_success_url()
        self.object.delete()
        return redirect(success_url)
