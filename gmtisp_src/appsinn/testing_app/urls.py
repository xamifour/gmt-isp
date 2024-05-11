from django.urls import path, re_path

from . import views

urlpatterns = [
    path('shelf_list/', views.shelf_list, name='shelf_list'),
    path('shelf/<int:pk>/', views.shelf, name='shelf'),
    path('project_list/', views.project_list, name='project_list'),
    re_path(
        r'^receive_project/(?P<pk>[^/\?]+)/$',
        views.receive_project,
        name='receive_project',
    )
]
