'''
URL configuration for gmtisp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
'''


import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from django.views.generic import TemplateView

from openwisp_radius.urls import get_urls

from . import views

if os.environ.get('SAMPLE_APP', False):
    # If you are extending the API views or social views,
    # please import them, otherwise pass `None` in place
    # of these values
    from openwisp_radius.api import views as api_views
    from openwisp_radius.saml import views as saml_views
    from openwisp_radius.social import views as social_views

    radius_urls = path(
        '', include((get_urls(api_views, social_views, saml_views), 'radius'))
    )
else:
    api_views = None
    social_views = None
    saml_views = None
    radius_urls = path('', include('openwisp_radius.urls'))


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('openwisp_utils.api.urls')),
    path('api/v1/', include('openwisp_users.api.urls')),
    path('accounts/', include('openwisp_users.accounts.urls')),
    radius_urls,

    path('testapp/', include('testing_app.api.urls')),
    path(
        'captive-portal-mock/login/',
        views.captive_portal_login,
        name='captive_portal_login_mock',
    ),
    path(
        'captive-portal-mock/logout/',
        views.captive_portal_logout,
        name='captive_portal_logout_mock',
    ),
    path(
        'menu-test-view/',
        TemplateView.as_view(template_name='openwisp_utils/menu_test.html'),
        name='menu-test-view',
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += staticfiles_urlpatterns()
