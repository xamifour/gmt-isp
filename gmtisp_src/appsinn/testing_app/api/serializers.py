from openwisp_utils.api.serializers import ValidatedModelSerializer
from testing_app.models import Shelf


class ShelfSerializer(ValidatedModelSerializer):
    class Meta:
        model = Shelf
        fields = '__all__'
