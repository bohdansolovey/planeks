from datetime import datetime

from django.core.validators import MaxLengthValidator
from django.db import transaction
from django.db.models import Q
from pytz import utc
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.models import Post, Tag, \
    PostReviewStatus
from api.v1.fields_serializers import ImageIdOnlySerializer


class PostCreateSerializer(serializers.ModelSerializer):
    tags = serializers.ListSerializer(
        child=serializers.CharField(max_length=20),
        allow_empty=False,
        allow_null=False,
        validators=[MaxLengthValidator(10)],
        write_only=True,
        required=False, )
    default_image = ImageIdOnlySerializer(required=False, allow_null=True, )
    images = serializers.ListSerializer(child=ImageIdOnlySerializer(),
                                        validators=[MaxLengthValidator(10)],
                                        allow_empty=True,
                                        write_only=True,
                                        required=False,
                                        allow_null=True, )

    class Meta:
        model = Post
        fields = (
            'title',
            'sub_title',
            'description',

            'default_image',
            'images',
            'tags',
        )

    def validate(self, vd):
        if 'user' not in self.context:
            raise ValueError('user not in serializer context')

        images = vd.get('images', [])
        if images is None:
            images = []

        default_image = vd.get('default_image', None)
        if default_image is not None and default_image not in images:
            raise ValidationError('This image must be in images too.')
        vd['default_image'] = default_image
        vd['images'] = images
        return vd

    def make_instances(self, validated_data):
        user = self.context['user']
        dirty_tags_vd = validated_data.pop('tags', [])
        # use only tags which are unique
        tags = []
        for tag_name in dirty_tags_vd:
            tag = Tag.objects.filter(
                Q(name=tag_name.upper()) or
                Q(name=tag_name.lower()) or
                Q(name=tag_name)
            ).first()
            if tag is None:
                tag = Tag(name=tag_name)
            tags.append(tag)

        default_image = validated_data.pop('default_image', None)
        images = validated_data.pop('images', None)
        validated_data['default_image'] = default_image
        validated_data['created_by_id'] = user.id
        if images is None:
            images = []
        post = self.Meta.model(**validated_data)
        return user, post, images, tags

    @transaction.atomic
    def create(self, validated_data):
        user, post, images, tags = self.make_instances(validated_data)
        post.date_published = datetime.now(tz=utc)
        if user.is_redactor or \
                user.is_staff:
            post.review_status = PostReviewStatus.approved
            post.date_published = datetime.now(tz=utc)
        elif user.is_default:
            post.review_status = PostReviewStatus.pending

        for image in images:
            if image.pk is None:
                image.save()

        for tag in tags:
            if tag.id is None:
                tag.save()
        post.save()
        post.tags.add(*tags)
        post.save()
        for image in images:
            image.post_id = post.id
            image.save()

        return post
