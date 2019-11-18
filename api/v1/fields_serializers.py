from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework import serializers

# ById serializers are used to get instance by id
from api.models import UploadedImage
from . import model_serializers


class ImageByIdSerializer(serializers.UUIDField):

    def to_internal_value(self, data):
        data = super(ImageByIdSerializer, self).to_internal_value(data)
        try:
            return UploadedImage.objects.get(id=data)
        except ObjectDoesNotExist:
            raise ValidationError('No image with this id')

    def to_representation(self, instance):
        return model_serializers.UploadedImageSerializer(
            instance=instance, context=self.context
        ).data


# IdOnly serializers are used to keep same structure in update/create queries,
# but prevent updating related model
class ImageIdOnlySerializer(serializers.Serializer):
    id = serializers.UUIDField()  # omit default validation

    def validate(self, data):
        try:
            return UploadedImage.objects.get(id=data['id'])
        except ObjectDoesNotExist:
            raise ValidationError('No image with this id')

    def to_representation(self, instance):
        return model_serializers.UploadedImageSerializer(instance=instance,
                                                         context=self.context).data
