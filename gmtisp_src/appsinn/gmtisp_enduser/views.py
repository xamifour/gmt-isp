#  ka@Kwames-MacBook-Pro ~ % curl -H "Authorization: Bearer <your_token>" http://127.0.0.1:8000/api/v1/users/user/
# curl -H "Authorization: Bearer <your_token>" http://127.0.0.1:8000/api/v1/users/user/

# gmtisp_enduser/views.py

from django.views import View
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.generic import RedirectView
from django.urls import reverse_lazy
from django.contrib.auth import logout

from .services import OpenWispAPIClient

class LoginView(View):
    def get(self, request):
        return render(request, 'gmtisp_enduser/login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        client = OpenWispAPIClient()

        try:
            client.authenticate(username, password)
            request.session['username'] = username
            messages.success(request, 'Login successful!')
            return redirect('home')
        except Exception as e:
            messages.error(request, f'Login failed: {e}')
            return redirect('login')

class ProfileView(View):
    def get(self, request):
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, 'You need to log in to view your profile.')
            return redirect('login')

        client = OpenWispAPIClient()
        try:
            user_details = client.get_user(user_id)
            return render(request, 'gmtisp_enduser/profile.html', {'user': user_details})
        except Exception as e:
            messages.error(request, f'Failed to fetch user details: {e}')
            return redirect('login')

class LogoutView(RedirectView):
    url = reverse_lazy('login')

    def get(self, request, *args, **kwargs):
        logout(request)
        request.session.flush()
        messages.success(request, 'You have been logged out successfully.')
        return super().get(request, *args, **kwargs)
