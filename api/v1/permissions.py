import logging

from rest_framework.permissions import BasePermission
from django.utils.translation import ugettext_lazy as _
from rest_framework_jwt.utils import jwt_decode_handler

logger = logging.getLogger(__name__)

__all__ = (
    'IsSignedIn',
    'IsSeller',
)


class IsSignedIn(BasePermission):
    message = _('You must be fully registered.')

    def has_permission(self, request, view):
        return not request.user.is_anonymous


class IsRedactor(BasePermission):
    message = _('You must be seller.')

    def has_permission(self, request, view):
        user = request.user
        return not user.is_anonymous and user.is_redactor
