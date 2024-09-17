# gmtisp_enduser/views.py
#  ka@Kwames-MacBook-Pro ~ % curl -H "Authorization: Bearer <your_token>" http://127.0.0.1:8000/api/v1/users/user/
# curl -H "Authorization: Bearer <your_token>" http://127.0.0.1:8000/api/v1/users/user/

from requests.exceptions import HTTPError
from django.views.generic import FormView, TemplateView, RedirectView
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
import logging
from .services import OpenWispAPIClient
from .forms import LoginForm

class LoginView(FormView):
    template_name = 'gmtisp_enduser/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('profile')
    logger = logging.getLogger(__name__)

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        client = OpenWispAPIClient()
        try:
            token_response = client.get_auth_token(username, password)
            token = token_response.get('token')

            # Use username directly to fetch details
            user_details = client.get_user_details(token, username)

            self.request.session['token'] = token
            self.logger.debug('User details: %s', user_details)  # Log the user details

            if 'username' not in user_details:
                messages.error(self.request, "Failed to retrieve user details.")
                return self.form_invalid(form)

            # Store all relevant user details in the session
            self.request.session['user_details'] = user_details

            messages.success(self.request, f'Welcome {user_details["first_name"]}')
            return super().form_valid(form)
        except ValueError as ve:
            messages.error(self.request, str(ve))
            return self.form_invalid(form)
        except HTTPError as http_err:
            messages.error(self.request, f'Login failed: {http_err}')
            return self.form_invalid(form)
        except Exception as err:
            messages.error(self.request, f'Login failed: {err}')
            return self.form_invalid(form)

class ProfileView(TemplateView):
    template_name = 'gmtisp_enduser/profile.html'

    def get(self, request, *args, **kwargs):
        if not request.session.get('token'):
            messages.error(request, 'You must be logged in to view this page.')
            return redirect('login')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_details'] = self.request.session.get('user_details', {})
        return context

class LogoutView(RedirectView):
    url = reverse_lazy('login')

    def get(self, request, *args, **kwargs):
        logout(request)
        request.session.flush()
        messages.success(request, 'You have been logged out successfully.')
        return super().get(request, *args, **kwargs)
