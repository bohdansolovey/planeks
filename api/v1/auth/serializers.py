from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.models import AuthUser, AuthUserRegistrationType


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(validators=[validate_password])
    password_confirm = serializers.CharField(validators=[validate_password])
    email = serializers.EmailField()  # to override validation

    class Meta:
        model = AuthUser
        fields = (
            'email',
            'first_name',
            'last_name',
            'reg_type',
            'password',
            'password_confirm',
        )
        extra_kwargs = dict.fromkeys(
            (
                'reg_type', 'email', 'first_name',
                'last_name',  'password', 'password_confirm',
            ),
            {"required": True},
        )

    @staticmethod
    def validate_password_confirm_data(password_confirm, data):
        pass1 = data['password']
        if pass1 != password_confirm:
            raise ValidationError("Password doesn't match")
        return password_confirm

    @staticmethod
    def validate_reg_type(reg_type):
        if reg_type not in (
                AuthUserRegistrationType.redactor,
                AuthUserRegistrationType.default
        ):
            reg_type = AuthUserRegistrationType.default
        return reg_type

    @staticmethod
    def validate_email(email):
        user = AuthUser.objects.filter(email__iexact=email).first()
        if user is not None:
            raise ValidationError(
                'User with this email already exists. '
                'Try to login or restore password.'
            )
        return email
