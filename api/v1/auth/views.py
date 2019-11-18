from copy import deepcopy

from django.contrib.auth.signals import user_logged_in
from rest_framework import status
from rest_framework.generics import (
    GenericAPIView)
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.serializers import JSONWebTokenSerializer, \
    jwt_payload_handler, jwt_encode_handler
from rest_framework_jwt.views import RefreshJSONWebToken, \
    VerifyJSONWebToken, JSONWebTokenAPIView
from rest_framework_jwt.views import jwt_response_payload_handler

from api.mailing import send_register_email
from api.v1.auth.serializers import RegistrationSerializer
from api.models import AuthUserRegistrationType, AuthUser
from planekstest.tasks import send_verification_email


class TokenFromHeaderMixin:
    """
    If token not in request data, loads it from header
    """

    def get_serializer(self, *args, **kwargs):
        if 'data' in kwargs and 'token' not in kwargs['data']:
            authorizer = JSONWebTokenAuthentication()
            jwt_value = authorizer.get_jwt_value(self.request)
            if jwt_value is not None and len(jwt_value) > 0:
                kwargs['data']['token'] = jwt_value.decode('utf-8')
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)


class LoginView(JSONWebTokenAPIView):
    """
    Login

    To logout simply delete token from cookies/storage

    Returns token, information about user and his current rights (scope)

    """
    serializer_class = JSONWebTokenSerializer

    def post(self, request, *args, **kwargs):
        if request.data.get('email'):
            request_mutability = request.POST._mutable
            request.POST._mutable = True
            request.data['email'] = request.data['email'].lower()
            request.POST._mutable = request_mutability
            # Updating last_login date
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            user_logged_in.send(sender=user.__class__, request=request,
                                user=user)
        return super(LoginView, self).post(request, *args, **kwargs)


class RefreshTokenView(TokenFromHeaderMixin, RefreshJSONWebToken):
    """
    Refresh token

    API View that returns a refreshed token (with new expiration) based on
    existing token.

    """
    pass


class VerifyTokenView(TokenFromHeaderMixin, VerifyJSONWebToken):
    """
    Verify token

    API View that checks the veracity of a token, returning the token if it
    is valid.

    """
    pass


def create_token(user):
    payload = jwt_payload_handler(user)
    token = jwt_encode_handler(payload)
    return token


class RegistrationView(GenericAPIView):
    serializer_class = RegistrationSerializer

    def post(self, request, *args, **kwargs):
        """
        Registration

        Fill personal info.

        Returns user info and JWT token
        """
        serial = self.serializer_class(data=request.data)
        serial.is_valid(raise_exception=True)
        vd = serial.validated_data
        reg_type = vd.get('reg_type')

        extra_fields = deepcopy(vd)
        for extra_field in \
                ('reg_type', 'password', 'password_confirm', 'email'):
            if extra_fields.get(extra_field):
                extra_fields.pop(extra_field)

        if reg_type == AuthUserRegistrationType.default:
            user = AuthUser.objects.create_user(
                vd['email'], vd['password'], **extra_fields
            )
        elif reg_type == AuthUserRegistrationType.redactor:
            user = AuthUser.objects.create_redactor(
                vd['email'], vd['password'], **extra_fields
            )
        else:
            return Response(dict(), status=status.HTTP_400_BAD_REQUEST)
        if not user.is_email_confirmed:
            #
            #token = ConfirmationLink(user=user, type=ConfirmationLinkType.confirm_email)
            #token.save()
            user_id = user.id
            token = 'asdasdasdcalsdlasldalsdalsdl'
            send_verification_email.delay(user_id, token)
        return Response(
            jwt_response_payload_handler(
                token=create_token(user), user=user, request=request
            ),
            status=status.HTTP_200_OK
        )

#  approximate confirm email realization
#class ConfirmationLinkType:
#    password_reset = 0
#    confirm_email = 1
#    confirm_subscription = 2
#    confirm_email_change = 3

# class ConfirmationLink(models.Model):
    # date_created = models.DateTimeField(blank=True)
    # user = models.ForeignKey(AuthUser, null=True, blank=True, on_delete=models.CASCADE)
    # date_expire_after = models.DateTimeField(blank=True)
    # is_used = models.BooleanField(default=False)
    # attempt_number = models.IntegerField(default=0)
    # token = models.CharField(max_length=70, db_index=True, unique=True)  # 64 hash + 6 random salt
    # type = models.IntegerField(choices=ConfirmationLinkType.choices())

