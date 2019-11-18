# coding=UTF-8
from datetime import datetime, timedelta

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from freezegun import freeze_time
from rest_framework.test import APIClient
from rest_framework_jwt.settings import api_settings

from api.models import AuthUser, AuthUserRegistrationType

__all__ = (
    'AuthTestCase',
)


class AuthTestCase(TestCase):
    @staticmethod
    def __create_test_user():
        test_data ={
            'email': 'email@test.com',
            'password': 'my_password',
            'first_name': 'FirstName',
            'last_name': 'LastName',
        }
        user = AuthUser.objects.create_redactor(**test_data)
        user.save()

    def __get_test_user_token(self):
        response = self.client.post(reverse('api_v1:login'),
                                    data={
                                        'email': 'email@test.com',
                                        'password': 'my_password',
                                    })
        self.assertIsNotNone(response.data.get('token'), 'No token in response')
        return response.data['token']

    def setUp(self):
        self.client = APIClient()
        self.__create_test_user()
        self.token = self.__get_test_user_token()

    def test_valid_login(self):
        response = self.client.post(
            reverse('api_v1:login'),
            data={
                'email': 'email@test.com',
                'password': 'my_password',
            },
            __docs__save__name='Ok, not completely registration',
        )
        self.assertEquals(response.status_code, 200, 'Can not login')
        self.assertIsNotNone(response.data.get('token'), 'No token in response')
        token = response.data['token']
        response = self.client.get(
            reverse('api_v1:posts-lc'),
            HTTP_AUTHORIZATION='JWT ' + token,
            __docs__save__name='ok')
        self.assertEquals(response.status_code, 200, 'Can not get access by token')

    def test_valid_login_with_uppercase_email(self):
        response = self.client.post(
            reverse('api_v1:login'), data={
                'email': 'EMAIL@TEST.COM',
                'password': 'my_password',
            },
            __docs__save__name='uppercase email login',
        )
        self.assertEquals(response.status_code, 200, 'Can not login')

    def test_invalid_get_profile_with_invalid_token(self):
        response = self.client.get(
            reverse('api_v1:posts-lc'), HTTP_AUTHORIZATION='JWT BAD_TOKEN',
            __docs__save__name='bad token',
        )
        self.assertEquals(response.status_code, 401, 'Can get access with bad token')

    def test_invalid_login_not_existed_user(self):
        response = self.client.post(
            reverse('api_v1:login'), data={
                'email': False,
                'password': False,
            }, __docs__save__name='invalid_credentials',
        )
        self.assertEquals(response.status_code, 400, 'Can preform login with wrong credentials')

    def test_valid_verify_token_header(self):
        response = self.client.post(
            reverse('api_v1:verify-token'),
            HTTP_AUTHORIZATION='JWT ' + self.token, __docs__save__name='ok',
        )
        self.assertEquals(response.status_code, 200, 'Can not verify token')
        self.assertIsNotNone(response.data['token'], 'No token in response')

    def test_valid_refresh_token_with_header(self):
        response = self.client.post(
            reverse('api_v1:refresh-token'),
            HTTP_AUTHORIZATION='JWT ' + self.token, __docs__save__name='ok',
        )
        self.assertEquals(response.status_code, 200, 'Can not refresh token')
        self.assertIsNotNone(response.data['token'], 'No token in response')

    def test_valid_refresh_token_with_body(self):
        response = self.client.post(
            reverse('api_v1:refresh-token'), data={'token': self.token}, __docs__save__name='ok',
        )
        self.assertEquals(response.status_code, 200, 'Can not refresh token')
        self.assertIsNotNone(response.data['token'], 'No token in response')

    def test_invalid_refresh_fully_expired_token(self):
        # 60s - small delay for test to pass
        with freeze_time(datetime.now() - api_settings.JWT_REFRESH_EXPIRATION_DELTA - timedelta(seconds=60)):
            token = self.__get_test_user_token()
        response = self.client.post(
            reverse('api_v1:refresh-token'),
            HTTP_AUTHORIZATION='JWT ' + token,
            __docs__save__name='token fully expired',
        )
        self.assertEquals(
            response.status_code, 400,
            'Can refresh token after JWT_REFRESH_EXPIRATION_DELTA'
        )

    def test_invalid_login_with_no_and_empty_data(self):
        response = self.client.post(
            reverse('api_v1:login'), data=None, __docs__save__name='no data',
        )
        self.assertEquals(response.status_code, 400, 'User can login with no data')

        response = self.client.post(
            reverse('api_v1:login'), data=dict(), __docs__save__name='no data',
        )
        self.assertEquals(response.status_code, 400, 'User can login with empty data')


class BaseSignUpTestCase(TestCase):
    def get_register_response(
            self, user_email=None, reg_type=None, data=None, is_data=True,
            docs__save__name='Ok', is_docs=True, url_name=None, token=None,
            data_format=None,
    ):
        if url_name:
            data = data \
                if data is not None or not is_data \
                else {
                    'email': 'email@go.com',
                    'password': 'my_password',
                    'password_confirm': 'my_password',
                    'reg_type': AuthUserRegistrationType.redactor,
                    'first_name': 'My first name',
                    'last_name': 'My last name',
                }
            kwargs = {'data': data}
            if user_email:
                data['email'] = user_email  # pragma: no cover
            if reg_type:
                data['reg_type'] = reg_type
            if is_docs:
                kwargs['__docs__save__name'] = docs__save__name
            if token:
                kwargs['HTTP_AUTHORIZATION'] = 'JWT ' + token
            if data_format:
                kwargs['format'] = data_format
            response = self.client.post(reverse(url_name), **kwargs)
            return response


class SignUpCase(BaseSignUpTestCase):
    def setUp(self):
        self.client = APIClient()

    def get_register_response(self, **kwargs):
        kwargs['url_name'] = 'api_v1:register'
        response = super(
            SignUpCase, self,
        ).get_register_response(**kwargs)
        return response

    def test_valid_register_redactor(self):
        response = self.get_register_response()

        self.assertEquals(response.status_code, 200, 'Can not register')
        self.assertIsNotNone(response.data['token'], 'No token in response')
        # self.assertEqual(len(mail.outbox), 1, 'No email in inbox')

    def test_valid_register_user(self):
        response = self.get_register_response(
            reg_type=AuthUserRegistrationType.default,
        )
        self.assertEquals(response.status_code, 200, 'Can not register')
        self.assertIsNotNone(response.data['token'], 'No token in response')
        # self.assertEqual(len(mail.outbox), 1, 'No email in inbox')

    def test_invalid_register_with_empty_data(self):
        response = self.get_register_response(
            is_data=False, docs__save__name='no data',
        )
        self.assertEquals(
            response.status_code, 400, 'User can register with no data',
        )

        response = self.get_register_response(data=dict(), is_docs=False)
        self.assertEquals(
            response.status_code, 400, 'User can register with empty data',
        )
        self.assertEqual(len(mail.outbox), 0, 'email in inbox')

    def test_invalid_register_with_duplicating_data(self):
        for i in range(2):
            response = self.get_register_response()
        self.assertEquals(
            response.status_code, 400, 'Registered user with duplicated data',
        )

