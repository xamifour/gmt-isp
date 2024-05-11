from django.urls import path

from . import views

urlpatterns = [
    path('items/', views.ItemListView.as_view(), name='item_list'),
    path('items/<int:item_id>/', views.ItemDetailView.as_view(), name='item_detail'),
]

# urlpatterns = [
#     path('items/', views.item_list, name='item-list'),
#     path('items/<int:item_id>/', views.item_detail, name='item-detail'),
# ]
