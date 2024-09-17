from django.urls import path
from .views import (
    UserListView, UserDetailView, UserCreateView, UserUpdateView, UserDeleteView,
    OrganizationListView, OrganizationDetailView, OrganizationCreateView, OrganizationUpdateView, OrganizationDeleteView
)

urlpatterns = [
    path('', UserListView.as_view(), name='user_list'),
    path('user/<uuid:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('user/create/', UserCreateView.as_view(), name='user_create'),
    path('user/<uuid:pk>/update/', UserUpdateView.as_view(), name='user_update'),
    path('user/<uuid:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),
    
    path('organizations/', OrganizationListView.as_view(), name='organization_list'),
    path('organization/<uuid:pk>/', OrganizationDetailView.as_view(), name='organization_detail'),
    path('organization/create/', OrganizationCreateView.as_view(), name='organization_create'),
    path('organization/<uuid:pk>/update/', OrganizationUpdateView.as_view(), name='organization_update'),
    path('organization/<uuid:pk>/delete/', OrganizationDeleteView.as_view(), name='organization_delete'),
]
