from django.conf.urls import url

from api.v1.post.views import PostListCreateView, PostDetailsView, \
    CommentCreateView, PostArchiveView, ImageUploadView
from api.v1.auth.views import LoginView, RefreshTokenView, \
    VerifyTokenView, RegistrationView

urlpatterns = [
    url(r'^register/?$', RegistrationView.as_view(), name='register'),
    url(r'^login/?$', LoginView.as_view(), name='login'),
    url(r'^token/refresh/?$', RefreshTokenView.as_view(), name='refresh-token'),
    url(r'^token/verify/?$', VerifyTokenView.as_view(), name='verify-token'),
    url(r'^upload-image/?$', ImageUploadView.as_view(), name='upload-image'),
    url(r'^posts/?$', PostListCreateView.as_view(), name='posts-lc'),
    url(
        r'^posts/(?P<id>\d+)/?$', PostDetailsView.as_view(),
        name='post-details'
    ),
    url(
        r'^posts/(?P<id>\d+)/archive/?$', PostArchiveView.as_view(),
        name='post-archive'
    ),
    url(r'^comments/?$', CommentCreateView.as_view(), name='comment-create')

]
