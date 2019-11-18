from django.core.validators import MaxLengthValidator
from django.db import transaction
from rest_framework import serializers


from api.models import Post, Comment, AuthUser, UploadedImage
from api.v1.fields_serializers import ImageByIdSerializer


class UploadedImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UploadedImage
        fields = (
            'id',
            'img',
            'url',
        )

        extra_kwargs = {
            'id': {'read_only': True},
            'img': {'write_only': True},
        }

    def get_url(self, instance):
        if instance is not None:
            return self.context['request'].build_absolute_uri(instance.img.url)


class AuthUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthUser
        fields = (
            'id',
            'first_name',
            'last_name',
            'user_type',
            'reg_type',
            'email',

        )

        extra_kwargs = {
            'id': {'read_only': True},
            'user_type': {'read_only': True},
            'reg_type': {'read_only': True},
            'email': {'read_only': True},
        }


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = (
            'id',
            'name',
            'text',
            'date_created',
            'post'
        )


class FullPostSerializer(serializers.ModelSerializer):
    tags = serializers.ListSerializer(
        child=serializers.CharField(max_length=20),
        allow_empty=True,
        validators=[MaxLengthValidator(10)]
    )
    default_image = ImageByIdSerializer()
    images = serializers.ListSerializer(child=UploadedImageSerializer(),
                                        validators=[MaxLengthValidator(10)],
                                        allow_empty=False)
    comments = serializers.ListSerializer(child=CommentSerializer(),
                                          validators=[MaxLengthValidator(10)],
                                          allow_empty=False)

    class Meta:
        model = Post
        fields = (
            'id',

            'title',
            'sub_title',

            'default_image',
            'images',
            'tags',
            'is_archived',
            'review_status',

            'date_created',
            'date_published',
            'date_modified',
            'comments',
        )

    def to_representation(self, instance):
        data = super(FullPostSerializer, self).to_representation(instance)
        data['tags'] = list(map(lambda x: x.name, instance.tags.all()))
        return data


class ShortPostSerializer(serializers.ModelSerializer):
    default_image = ImageByIdSerializer()

    tags = serializers.ListSerializer(
        child=serializers.CharField(max_length=20,),
        allow_empty=True,
        validators=[MaxLengthValidator(10)]
    )

    class Meta:
        model = Post
        fields = (
            'id',
            'title',
            'default_image',
            'tags',
            'is_archived',
        )

    def to_representation(self, instance):
        data = super(ShortPostSerializer, self).to_representation(instance)
        data['tags'] = list(map(lambda x: x.name, instance.tags.all()))
        return data

