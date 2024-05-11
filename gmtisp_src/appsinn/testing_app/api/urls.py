from django.urls import path

from .views import ShelfListAPIView, ShelfDetailAPIView

urlpatterns = [
    path('shelfs/', ShelfListAPIView.as_view(), name='shelf_list_api'),
    path('shelf/<int:pk>/', ShelfDetailAPIView.as_view(), name='shelf_detail_api'),
]
