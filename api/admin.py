from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group

from .admin_forms import UserPasswordChangeForm, UserCreationForm, \
    CommentAddForm
from .models import Post, UploadedImage, AuthUser, Tag, Comment

admin.site.unregister(Group)


class ProductUploadedImageInline(admin.StackedInline):
    model = UploadedImage
    max_num = 10
    min_num = 1
    extra = 0

    fk_name = 'post'

    fields = ('id', 'img', )
    readonly_fields = ('id', )


class PostCommentInline(admin.StackedInline):
    model = Comment
    max_num = 10
    min_num = 1
    extra = 0

    fk_name = 'post'

    fields = ('id','name', 'email', 'text',  )
    readonly_fields = ('id', )


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'review_status',
        'is_archived',
    )
    search_fields = ('description', 'title', 'created_by', )

    fieldsets = (
        (None, {
            'fields':
                (
                    'id',
                ),
        }),
        ('Post info', {
            'fields':
                (
                    'title', 'sub_title', 'description',
                    'tags',
                ),
        }),
        ('Important dates', {'fields': (
             'date_published', 'date_modified',
        )}),
        ('System status', {'fields': ('review_status',)}),
    )

    actions = None

    inlines = (
        ProductUploadedImageInline,
        PostCommentInline
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return (
                'id',  'date_created', 'date_published',
                'date_modified',
            )
        else:
            return 'id'


@admin.register(AuthUser)
class AuthUserAdmin(DjangoUserAdmin):
    form = UserPasswordChangeForm
    add_form = UserCreationForm
    search_fields = ('email', 'first_name', 'last_name',)
    ordering = ('email', 'id',)
    list_filter = ('is_superuser', 'user_type', 'reg_type')
    list_display = (
        'id', 'email', 'user_type', 'reg_type',
        'first_name', 'last_name', 'last_login',
    )

    fieldsets = (
        (None, {'fields': ('id', 'email', 'password', )}),
        ('Personal info', {
            'fields': (
                'first_name', 'last_name',
            ),
        }),
        ('Permissions', {
            'fields': ('user_type', 'reg_type', )
        }),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'fields': (
                'email', 'first_name', 'last_name',
                'password1', 'password2',
            ),
        }),
        ('Permissions', {'fields': ('user_type', 'reg_type',)}),
    )

    def get_readonly_fields(self, request, obj=None):
        return 'id'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', )
    search_fields = ('name',)

    fieldsets = (
        (None, {'fields': ('id', 'name', )}),
    )

    readonly_fields = ('id', )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'text', )
    search_fields = ('name', 'text', 'post')
    add_form = CommentAddForm

    readonly_fields = ('id', )
