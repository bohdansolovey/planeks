from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from rest_framework import status, serializers
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from api.models import Post, PostReviewStatus
from api.v1.model_serializers import FullPostSerializer, ShortPostSerializer, \
    CommentSerializer, UploadedImageSerializer
from api.v1.permissions import IsSignedIn
from api.v1.post.serializers import PostCreateSerializer
from planekstest.tasks import send_new_comment_email


def get_post_or_404(id, user, check_own=True):
    try:
        post = Post.objects.get(id=id)
    except ObjectDoesNotExist:
        raise Http404()

    if check_own and user.id != post.created_by_id:
        raise Http404()

    return post


class PostArchiveView(GenericAPIView):
    serializer_class = serializers.Serializer  # to pass docs generation
    permission_classes = (IsSignedIn,)

    @staticmethod
    def post(request, id):
        """
           Archive post

           If post doesn't belong to user - `404`.
           If post was archived - `200`
           """
        user = request.user
        post = get_post_or_404(id, user)
        post.is_archived = True
        post.save()
        return Response(
            FullPostSerializer(
                instance=post,
                context={'request': request}
            ).data,
            status=status.HTTP_200_OK
        )

    @staticmethod
    def delete(request, id):
        """
           Unarchive post

           If post doesn't belong to user - `404`.
           If post was onarchived - `200`
        """
        post = get_post_or_404(id, request.user)
        post.is_archived = False
        post.save()
        return Response(
            FullPostSerializer(
                instance=post, context={'request': request}
            ).data,
            status=status.HTTP_200_OK
        )


class MyLimitOffsetPagination(LimitOffsetPagination):
    # move pagination to utils
    max_limit = 100
    default_limit = 12


class PostListCreateView(GenericAPIView):
    serializer_class = ShortPostSerializer
    pagination_class = MyLimitOffsetPagination

    def get_permissions(self):
        if self.request.method == 'GET':
            self.permission_classes = ()
        else:
            self.permission_classes = (IsSignedIn,)
        return super(PostListCreateView, self).get_permissions()

    def get(self, request):
        """
            Get posts list

            posts are presented in short version

            pagination:
                `limit` - page size, max value 100, default 12
                `offset` - results offset
            `posts/?limit=50` - returns first 50 items
            `posts/?limit=50&offset=50` - returns 51..100 items
        """
        user = request.user
        if not user.is_anonymous and user.is_redactor:
            queryset = Post.objects.filter(
                created_by=user
            )
        elif not user.is_anonymous and user.is_staff:
            queryset = Post.objects.filter(
                created_by=user
            )
        else:
            queryset = Post.objects.filter(
                review_status=PostReviewStatus.approved
            )

        posts = queryset
        paginated_posts = self.paginator.paginate_queryset(
            posts, request,
        )
        serializer_class = self.get_serializer_class()
        posts_data = serializer_class(
            paginated_posts, many=True, context={'request': request},
        ).data

        return self.paginator.get_paginated_response(posts_data)

    def post(self, request):
        """ Create new post  """

        user = request.user
        serial = PostCreateSerializer(
            data=request.data, context={'user': user},
        )
        serial.is_valid(raise_exception=True)
        post = serial.save()
        serializer_data = FullPostSerializer(
            instance=post, context={'request': request},
        ).data
        return Response(serializer_data, status=status.HTTP_201_CREATED)


class PostDetailsView(GenericAPIView):
    serializer_class = FullPostSerializer

    def get(self, request, id):
        """
        Get full info about post
        """
        try:
            post = Post.objects.get(id=id)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer_data = self.serializer_class(
            post, context={'request': request},
        ).data

        return Response(serializer_data, status=status.HTTP_200_OK)


class CommentCreateView(GenericAPIView):
    serializer_class = CommentSerializer

    def post(self, request):
        """
           Add comment to post

        """
        post = get_post_or_404(
            request.data['post'], request.user, check_own=False
        )
        serial = self.serializer_class(
            data=request.data,
        )
        serial.is_valid(raise_exception=True)
        comment = serial.save()
        comment.post = post
        comment.save()
        post_link = post.get_url(request)
        send_new_comment_email.delay(post.created_by.email, post_link)
        serializer_data = self.serializer_class(
            instance=comment, context={'request': request},
        ).data
        return Response(serializer_data, status=status.HTTP_201_CREATED)


class ImageUploadView(GenericAPIView):
    serializer_class = UploadedImageSerializer
    permission_classes = (IsSignedIn,)

    def post(self, request):
        """
        Upload image

        Used to upload images and use them for product
        """
        serial = self.serializer_class(data=request.data)
        serial.is_valid(raise_exception=True)
        user = self.request.user
        image = serial.save(uploaded_by=user)
        return Response(
            self.serializer_class(
                instance=image, context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED,
        )
