# gmtisp_enduser/urls.py

from django.urls import path
from django.views.generic import TemplateView

from .views import LoginView, LogoutView, ProfileView

urlpatterns = [
    path('', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('logout/', LogoutView.as_view(), name='logout'), 

    path("home/", TemplateView.as_view(template_name="gmtisp_enduser/home.html"), name='home'),
]
