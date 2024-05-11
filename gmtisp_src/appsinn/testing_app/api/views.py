from rest_framework import generics

from ..models import Shelf
from .serializers import ShelfSerializer

class ShelfListAPIView(generics.ListAPIView):
    queryset = Shelf.objects.all()
    serializer_class = ShelfSerializer

class ShelfDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Shelf.objects.all()
    serializer_class = ShelfSerializer