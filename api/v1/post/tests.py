from django.core import mail
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from api.models import AuthUser, Post
from api.utils import test_file


class PostTestCase(TestCase):
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

    def test_post_comments_lc(self):
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
        images = [self.client.post(
            reverse('api_v1:upload-image'),
            HTTP_AUTHORIZATION='JWT ' + token,
            data={'img': test_file()},
        ).data]
        default_image = images[0]
        response = self.client.post(
            reverse('api_v1:posts-lc'),
            data={
                'title': 'NEW post',
                'sub_title': 'sub title',
                'description': 'description',
                'is_archived': False,
                'default_image': default_image,
                'images': images,
                'tags': [
                    'my_tag_1',
                    'my_second_tag'
                ],
            },
            HTTP_AUTHORIZATION='JWT ' + token,
            __docs__save__name='ok',
            format='json'
        )
        self.assertEquals(response.status_code, 201, 'Can not create post')
        response = self.client.post(
            reverse('api_v1:comment-create'),
            data={
                'name': 'myusername',
                'email': 'email@example.com',
                'text': 'text',
                'post': 1,
            },
            HTTP_AUTHORIZATION='JWT ' + token,
            __docs__save__name='ok'
        )
        self.assertEquals(response.status_code, 201, 'Can not create comment')
        response = self.client.get(
            reverse('api_v1:posts-lc'),
            HTTP_AUTHORIZATION='JWT ' + token,
            __docs__save__name='ok')
        self.assertEquals(
            response.status_code, 200, 'Cant get posts'
        )
        self.assertEquals(response.data['count'], 1, 'bad count')
        # self.assertEqual(len(mail.outbox), 1, 'No email in inbox')
        response = self.client.get(
            reverse('api_v1:post-details', kwargs={'id': 1}),
            __docs__save__name='ok')
        self.assertEquals(
            response.status_code, 200, 'Cant get post detail'
        )

