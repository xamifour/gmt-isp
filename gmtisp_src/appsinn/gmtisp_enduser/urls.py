from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('items/', views.ItemListView.as_view(), name='item_list'),
    path('items/<int:item_id>/', views.ItemDetailView.as_view(), name='item_detail'),

    path("", TemplateView.as_view(template_name="gmtisp_enduser/plans/index.html"), name='index'),
    path("plans1/", TemplateView.as_view(template_name="gmtisp_enduser/plans/d1.html"), name='plans1'),
    path("plans2/", TemplateView.as_view(template_name="gmtisp_enduser/plans/d2.html"), name='plans2'),
]

# urlpatterns = [
#     path('items/', views.item_list, name='item-list'),
#     path('items/<int:item_id>/', views.item_detail, name='item-detail'),
# ]
