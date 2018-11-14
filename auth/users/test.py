import json
from unittest.mock import patch

from django.contrib.auth import authenticate
from django.test import TestCase, override_settings
from django.core import mail

from rest_framework import status
from rest_framework.test import APITestCase

from jwt import ExpiredSignature, DecodeError

from rest_framework_jwt.settings import api_settings

from .models import User
from .tasks import on_create, send_confirmation_email, create_core_profile


USER_VASCO = {
    'username': 'VasmV',
    'email': 'vasco@foothub.com',
    'password': 'verystrong1'
}

USER_JOAO = {
    'username': 'Jefe',
    'email': 'joao@foothub.com',
    'password': 'verystrong2'
}


class TestUserBackend(TestCase):
    def setUp(self):
        User.objects.create_user(**USER_VASCO)
        User.objects.create_user(**USER_JOAO)

    def test_no_username_fail(self):
        self.assertIsNone(authenticate())

    def test_no_user_fail(self):
        self.assertIsNone(authenticate(username='bad_username'))

    def test_username_authentication_fail(self):
        self.assertIsNone(authenticate(username=USER_VASCO['username'], password=USER_JOAO['password']))

    def test_username_authentication_success(self):
        self.assertIsNotNone(authenticate(username=USER_VASCO['username'], password=USER_VASCO['password']))

    def test_email_authentication_fail(self):
        self.assertIsNone(authenticate(username=USER_VASCO['email'], password=USER_JOAO['password']))

    def test_email_authentication_success(self):
        self.assertIsNotNone(authenticate(username=USER_VASCO['email'], password=USER_VASCO['password']))


class TestUserManager(TestCase):
    def test_create_user_success(self):
        self.assertEqual(User.objects.count(), 0)

        user = User.objects.create_user(**USER_VASCO)

        self.assertEqual(User.objects.count(), 1)

        self.assertEqual(user.username, USER_VASCO['username'])
        self.assertEqual(user.email, USER_VASCO['email'])
        self.assertTrue(user.check_password(USER_VASCO['password']))


class TestUserModel(TestCase):
    def test_create_jwt(self):
        user = User.objects.create_user(**USER_VASCO)
        token = user.create_jwt()

        try:
            api_settings.JWT_DECODE_HANDLER(token)
        except (ExpiredSignature, DecodeError):
            self.assertTrue(False)

        bad_token = f'{token}_taint'
        with self.assertRaises(DecodeError):
            api_settings.JWT_DECODE_HANDLER(bad_token)


class TestUsersApi(APITestCase):
    URL = '/users'
    CONTENT_TYPE = 'application/json'

    @classmethod
    def instance_url(cls, username: str):
        return f'{cls.URL}/{username}'

    def setUp(self):
        user_vasco = User.objects.create_user(**USER_VASCO)
        token = user_vasco.create_jwt()

        self.http_auth = {
            'HTTP_AUTHORIZATION': f'JWT {token}',
        }

    def test_list_405(self):
        response = self.client.get(
            self.URL, content_type=self.CONTENT_TYPE, **self.http_auth)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_405(self):
        response = self.client.put(
            self.instance_url(USER_VASCO['username']),
            data=json.dumps({}), content_type=self.CONTENT_TYPE, **self.http_auth)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_create_user_403(self):
        response = self.client.post(
            self.URL, data=json.dumps(USER_JOAO), content_type=self.CONTENT_TYPE, **self.http_auth)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(User.objects.count(), 1)

    def test_create_user_400_invalid(self):
        self.assertEqual(User.objects.count(), 1)
        bad_user = {
            'username': 'username@foothub.com',
            'email': 'email@foothub.com',
            'password': 'legitpw123',
        }

        response = self.client.post(
            self.URL, data=json.dumps(bad_user), content_type=self.CONTENT_TYPE)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_create_user_400_forbidden(self):
        self.assertEqual(User.objects.count(), 1)
        bad_user = dict(USER_VASCO)
        bad_user['username'] = 'me'

        response = self.client.post(
            self.URL, data=json.dumps(bad_user), content_type=self.CONTENT_TYPE)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_create_user_400_existing(self):
        self.assertEqual(User.objects.count(), 1)

        response = self.client.post(
            self.URL, data=json.dumps(USER_VASCO), content_type=self.CONTENT_TYPE)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_create_user_200(self):
        self.assertEqual(User.objects.count(), 1)

        with patch('users.views.on_create') as mock:
            response = self.client.post(
                self.URL, data=json.dumps(USER_JOAO), content_type=self.CONTENT_TYPE)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(User.objects.count(), 2)
            mock.assert_called_once()

        user_joao = User.objects.get(username=USER_JOAO['username'])

        self.assertEqual(user_joao.username, USER_JOAO['username'])
        self.assertEqual(user_joao.email, USER_JOAO['email'])
        self.assertTrue(user_joao.check_password(USER_JOAO['password']))

    def test_retrieve_401(self):
        response = self.client.get(
            self.instance_url(USER_VASCO['username']), content_type=self.CONTENT_TYPE)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_403(self):
        User.objects.create_user(**USER_JOAO)
        response = self.client.get(
            self.instance_url(USER_JOAO['username']), content_type=self.CONTENT_TYPE, **self.http_auth)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_200(self):
        response = self.client.get(
            self.instance_url(USER_VASCO['username']), content_type=self.CONTENT_TYPE, **self.http_auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertIn('uuid', response.data)
        self.assertEqual(response.data['username'], USER_VASCO['username'])
        self.assertEqual(response.data['email'], USER_VASCO['email'])

    def test_destroy_401(self):
        response = self.client.delete(
            self.instance_url(USER_VASCO['username']), content_type=self.CONTENT_TYPE)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_destroy_403(self):
        User.objects.create_user(**USER_JOAO)
        response = self.client.delete(
            self.instance_url(USER_JOAO['username']), content_type=self.CONTENT_TYPE, **self.http_auth)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_204(self):
        self.assertEqual(User.objects.count(), 1)

        response = self.client.delete(
            self.instance_url(USER_VASCO['username']), content_type=self.CONTENT_TYPE, **self.http_auth)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(User.objects.count(), 0)


class TestUsersTasks(TestCase):

    def setUp(self):
        self.user_vasco = User.objects.create_user(**USER_VASCO)

    @patch('users.tasks.send_confirmation_email.delay')
    @patch('users.tasks.create_core_profile.delay')
    def test_on_create(self, mocked_ccp, mocked_sce):
        on_create(self.user_vasco)
        mocked_ccp.assert_called_once()
        mocked_sce.assert_called_once()

    def test_create_core_profile(self):
        assert False

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_confirmation_email(self):
        user_email = self.user_vasco.email
        token = self.user_vasco.create_jwt()
        url = 'auth.sercice.com/users/confirm'
        send_confirmation_email(user_email=user_email, user_jwt=token, url=url)

        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]

        self.assertEqual(sent_mail.from_email, 'FootHub Team <no-reply@foothub.com>')
        self.assertEqual(sent_mail.subject, "FootHub Registration")
        self.assertIn("Use the link to confirm email: ", sent_mail.body)
        self.assertIn(f'{url}?jwt={token}', sent_mail.body)
        self.assertEqual(sent_mail.to, [user_email])
