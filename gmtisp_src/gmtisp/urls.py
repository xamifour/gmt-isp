from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from django.views.generic import TemplateView
from django.views import defaults as default_views

# from . import views

urlpatterns = [
    # path('', views.LoginView.as_view(), name="login"),
    # path('', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
    # openwisp urls
    path('api/v1/', include('openwisp_utils.api.urls')),
    path('api/v1/', include('openwisp_users.api.urls')),
    path('accounts/', include('openwisp_users.accounts.urls')),
    path('radius/', include('openwisp_radius.urls')),
    # path('captive-portal-mock/login/', views.captive_portal_login, name='captive_portal_login_mock'),
    # path('captive-portal-mock/logout/', views.captive_portal_logout, name='captive_portal_logout_mock'),
    # other urls
    path('testapp/', include('testing_app.urls')),
    path('testapp_api/', include('testing_app.api.urls')),
    path('billing/', include('gmtisp_billing.urls')),
    path('billing_api/', include('gmtisp_billing.api.urls')),
    path('endusers/', include('gmtisp_enduser.urls')),

    path( 'menu-test-view/', TemplateView.as_view(template_name='testing_app/menu_test.html'), name='menu-test-view'),
    path('about/', TemplateView.as_view(template_name="gmtisp/pages/about.html"), name='about'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += staticfiles_urlpatterns()


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path('400/', default_views.bad_request, kwargs={"exception": Exception("Bad Request!")},),
        path('403/', default_views.permission_denied, kwargs={"exception": Exception("Permission Denied")},),
        path('404/', default_views.page_not_found, kwargs={"exception": Exception("Page not Found")},),
        path('500/', default_views.server_error),
    ]
    
    # if "debug_toolbar" in settings.INSTALLED_APPS:
    #     import debug_toolbar

    #     urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
    #     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    #     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)