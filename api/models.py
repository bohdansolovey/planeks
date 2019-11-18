import os
import uuid

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.urls import reverse
from werkzeug.utils import secure_filename


class AuthUserManager(BaseUserManager):
    def _create_user(
            self, email, password, user_type, reg_type=None, **extra_fields
    ):
        if not email:
            raise ValueError('The Email must be set')
        user = self.model(
            email=email, user_type=user_type,
            reg_type=reg_type, **extra_fields
        )
        if password:
            user.set_password(password)
        user.save()
        return user

    def create_redactor(self, email, password, **extra_fields):
        return self._create_user(
            email, password, AuthUserType.client,
            AuthUserRegistrationType.redactor, **extra_fields
        )

    def create_user(self, email, password, **extra_fields):
        return self._create_user(
            email, password, AuthUserType.client,
            AuthUserRegistrationType.default, **extra_fields
        )

    def redactors(self):
        return self.filter(
            user_type=AuthUserType.client,
            reg_type=AuthUserRegistrationType.redactor
        )

    def users(self):
        return self.filter(
            user_type=AuthUserType.client,
            reg_type=AuthUserRegistrationType.default
        )

    def create_superuser(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Cannot create super user without email')
        if not password:
            raise ValueError('Cannot create super user without password')
        user = self.model(
            email=email, user_type=AuthUserType.system, **extra_fields
        )
        if password:
            user.set_password(password)
        user.save()
        return user


class AuthUserType:
    system = 'system'
    client = 'client'


class AuthUserRegistrationType:
    default = 'user'
    redactor = 'redactor'


class AuthUser(AbstractBaseUser, PermissionsMixin):
    # used to separate support and authors/users
    AUTH_USER_TYPE_CHOICES = [
        (AuthUserType.system, 'system'),
        (AuthUserType.client, 'client'),
    ]
    AUTH_USER_REGISTRATION_TYPE_CHOICES = [
        (AuthUserRegistrationType.default, 'user'),
        (AuthUserRegistrationType.redactor, 'redactor'),
    ]

    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    user_type = models.CharField(
        choices=AUTH_USER_TYPE_CHOICES, max_length=12, db_index=True,
        default=AuthUserType.client
    )
    reg_type = models.CharField(
        choices=AUTH_USER_REGISTRATION_TYPE_CHOICES, max_length=12,
        db_index=True, null=True
    )
    is_email_confirmed = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'

    objects = AuthUserManager()

    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    @property
    def is_staff(self):
        # admin, moderator...
        return self.user_type == AuthUserType.system

    @property
    def is_redactor(self):
        return self.user_type == AuthUserType.client and \
               self.reg_type == AuthUserRegistrationType.redactor

    @property
    def is_default(self):
        return self.user_type == AuthUserType.client and \
               self.reg_type == AuthUserRegistrationType.default

    def save(self, *args, **kwargs):
        if self.email is not None:
            self.email = self.email.lower()
        if self.user_type == AuthUserType.system:
            self.is_superuser = True
            self.reg_type = None
        return super(AuthUser, self).save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(
        max_length=20, unique=True,
    )

    class Meta:
        db_table = 'tag'
        verbose_name = 'tag'
        verbose_name_plural = 'tags'
        ordering = ('name',)

    def __str__(self):
        return self.name


class PostReviewStatus:
    not_applied = 0
    pending = 1
    approved = 2
    declined = 3


class Post(models.Model):
    POST_REVIEW_CHOICES = [
        (PostReviewStatus.not_applied, 'not_applied'),
        (PostReviewStatus.pending, 'pending'),
        (PostReviewStatus.approved, 'approved'),
        (PostReviewStatus.declined, 'declined'),
    ]

    created_by = models.ForeignKey(
        'AuthUser', on_delete=models.CASCADE, null=True, blank=True,
    )
    is_archived = models.BooleanField(default=False)

    title = models.CharField(
        db_index=True, max_length=50, blank=True,
        verbose_name='Title', help_text='Title of the Post, '
                                        'length is limited to 50 characters',
    )
    sub_title = models.CharField(
        max_length=100, blank=True, verbose_name='Sub title',
        help_text='Sub title of the Post, length is limited'
                  ' to 100 characters',
    )
    description = models.TextField(
        blank=True, help_text='Detailed description of the Post',
    )
    default_image = models.ForeignKey(
        'UploadedImage', null=True, on_delete=models.CASCADE,
        related_name='product_with_default',
     )
    tags = models.ManyToManyField(Tag)

    review_status = models.IntegerField(
        choices=POST_REVIEW_CHOICES,
        default=PostReviewStatus.not_applied,
    )

    date_created = models.DateTimeField(auto_now_add=True)
    date_published = models.DateTimeField(null=True)
    date_modified = models.DateTimeField(null=True)

    def get_url(self, request):
        return request.build_absolute_uri(
            reverse('api_v1:post-details', kwargs={'id': self.id})
        )
    class Meta:
        db_table = 'post'
        verbose_name = 'post'
        verbose_name_plural = 'posts'

    def __str__(self):
        return "%s" % self.title


class Comment(models.Model):
    name = models.CharField(max_length=42)
    email = models.EmailField(max_length=75)
    text = models.TextField()
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='comments'
    )
    date_created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.text


def _get_filename_in_dir(upload_dir, filename):
    filename, file_extension = os.path.splitext(filename)
    file_name = str(uuid.uuid4()) + '_' + secure_filename(filename)
    if file_extension is not None and len(file_extension) > 0:
        file_name += file_extension
    return os.path.join(upload_dir, file_name)


def image_upload_to(instance, filename):
    return _get_filename_in_dir('uploaded_images', filename)


class UploadedImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    uploaded_by = models.ForeignKey(
        'AuthUser', null=True, blank=True, on_delete=models.CASCADE
    )
    post = models.ForeignKey(
        'Post', null=True, blank=True,
        on_delete=models.CASCADE, related_name='images'
    )
    img = models.ImageField(upload_to=image_upload_to, verbose_name='Image')
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'uploaded_image'
        verbose_name = 'uploaded image'
        verbose_name_plural = 'uploaded images'
        ordering = ['date_created']
