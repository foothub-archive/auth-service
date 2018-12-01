import json
from typing import Optional
from unittest.mock import patch

from django.contrib.auth import authenticate
from django.core import mail
from django.conf import settings
from django.test import TestCase, override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from jwt import ExpiredSignature, DecodeError

from rest_framework_jwt.settings import api_settings

from .models import User
from .serializers import ConfirmEmailSerializer
from .tasks import broadcast_registration, send_confirmation_email, on_create


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
    BROADCAST_ENDPOINT = 'broadcast_registration'
    CONFIRM_ENDPOINT = 'confirm_email'
    SEND_ENDPOINT = 'send_confirmation_email'
    CONTENT_TYPE = 'application/json'

    @classmethod
    def instance_url(cls, username: str):
        return f'{cls.URL}/{username}'

    @classmethod
    def broadcast_registration_url(cls):
        return f'{cls.URL}/{cls.BROADCAST_ENDPOINT}'

    @classmethod
    def send_email_url(cls, username: str):
        return f'{cls.instance_url(username)}/{cls.SEND_ENDPOINT}'

    @classmethod
    def confirm_email_url(cls, token: Optional[str] = None):
        url = f'{cls.URL}/{cls.CONFIRM_ENDPOINT}'
        return f'{url}?token={token}' if token is not None else url

    def setUp(self):
        self.user_vasco = User.objects.create_user(**USER_VASCO)
        self.token = self.user_vasco.create_jwt()

        self.http_auth = {
            'HTTP_AUTHORIZATION': f'JWT {self.token}',
        }

    def test_options_401(self):
        response = self.client.options(self.URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_options_200(self):
        response = self.client.options(self.URL, **self.http_auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_405(self):
        response = self.client.get(self.URL, **self.http_auth)
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
            self.instance_url(USER_VASCO['username']))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_403(self):
        User.objects.create_user(**USER_JOAO)
        response = self.client.get(
            self.instance_url(USER_JOAO['username']), **self.http_auth)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_200(self):
        response = self.client.get(
            self.instance_url(USER_VASCO['username']), **self.http_auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 3)
        self.assertIn('uuid', response.json())
        self.assertEqual(response.json()['username'], USER_VASCO['username'])
        self.assertEqual(response.json()['email'], USER_VASCO['email'])

    def test_destroy_401(self):
        response = self.client.delete(
            self.instance_url(USER_VASCO['username']))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_destroy_403(self):
        User.objects.create_user(**USER_JOAO)
        response = self.client.delete(
            self.instance_url(USER_JOAO['username']), **self.http_auth)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_204(self):
        self.assertEqual(User.objects.count(), 1)

        response = self.client.delete(
            self.instance_url(USER_VASCO['username']), **self.http_auth)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(User.objects.count(), 0)

    @patch('users.views.broadcast_registration')
    def test_broadcast_registration_401(self, mock):
        response = self.client.get(self.broadcast_registration_url())
        self.assertEqual(response.status_code, 401)
        mock.assert_not_called()

    @patch('users.views.broadcast_registration')
    def test_broadcast_registration_204(self, mock):
        response = self.client.get(self.broadcast_registration_url(), **self.http_auth)
        self.assertEqual(response.status_code, 204)
        mock.assert_called_once_with(uuid=self.user_vasco.uuid, username=self.user_vasco.username)

    @patch('users.views.send_confirmation_email')
    def test_send_confirmation_email_204_user_not_found(self, mock):
        response = self.client.get(self.send_email_url('unknown'))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock.assert_not_called()

    @patch('users.views.send_confirmation_email')
    def test_send_confirmation_email_204_already_confirmed_username(self, mock):
        self.user_vasco.email_confirmed = True
        self.user_vasco.save()
        response = self.client.get(self.send_email_url(self.user_vasco.username))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock.assert_not_called()

    @patch('users.views.send_confirmation_email')
    def test_send_confirmation_email_204(self, mock):
        self.assertFalse(self.user_vasco.email_confirmed)
        response = self.client.get(self.send_email_url(self.user_vasco.username))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock.assert_called_once_with(user=ConfirmEmailSerializer(self.user_vasco).data)

    def test_confirm_400_no_token(self):
        self.assertFalse(User.objects.get(username=USER_VASCO['username']).email_confirmed)

        response = self.client.post(self.confirm_email_url(), data=json.dumps({}), content_type=self.CONTENT_TYPE)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('token', response.json())
        self.assertEqual(response.json()['token'], ["This field is required."])
        self.assertFalse(User.objects.get(username=USER_VASCO['username']).email_confirmed)

    def test_confirm_400_bad_token(self):
        self.assertFalse(User.objects.get(username=USER_VASCO['username']).email_confirmed)

        bad_token = f'{self.token}_bad'
        response = self.client.post(
            self.confirm_email_url(bad_token), data=json.dumps({}), content_type=self.CONTENT_TYPE)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.json())
        self.assertEqual(response.json()['non_field_errors'], ["Error decoding signature."])
        self.assertFalse(User.objects.get(username=USER_VASCO['username']).email_confirmed)

    def test_confirm_204(self):
        self.assertFalse(User.objects.get(username=USER_VASCO['username']).email_confirmed)

        response = self.client.post(
            self.confirm_email_url(self.token), data=json.dumps({}), content_type=self.CONTENT_TYPE)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertTrue(User.objects.get(username=USER_VASCO['username']).email_confirmed)


class TestUsersTasks(TestCase):

    def setUp(self):
        self.user_vasco = User.objects.create_user(**USER_VASCO)

    @patch('users.tasks.send_confirmation_email.delay')
    @patch('users.tasks.broadcast_registration.delay')
    def test_on_create(self, mock_broadcast, mock_confirmation):
        on_create(self.user_vasco)
        mock_broadcast.assert_called_once_with(uuid=self.user_vasco.uuid, username=self.user_vasco.username)
        mock_confirmation.assert_called_once_with(user=ConfirmEmailSerializer(self.user_vasco).data)

    def test_broadcast_registration(self):
        with patch('users.tasks.post') as mock:

            expected_subscribers = [
                'http://core:8000/profiles'
            ]

            def side_effect(url, json):
                self.assertIn(url, expected_subscribers)
                self.assertIn('token', json)
                payload = api_settings.JWT_DECODE_HANDLER(json['token'])
                self.assertEqual(payload['uuid'], self.user_vasco.uuid)
                self.assertEqual(payload['username'], self.user_vasco.username)
                return mock

            mock.side_effect = side_effect

            mock.status_code = 201
            self.assertTrue(broadcast_registration(self.user_vasco.uuid, self.user_vasco.username))
            self.assertEqual(mock.call_count, len(expected_subscribers))

            mock.reset_mock()

            mock.status_code = 404
            self.assertFalse(broadcast_registration(self.user_vasco.uuid, self.user_vasco.username))
            self.assertEqual(mock.call_count, len(expected_subscribers))

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_confirmation_email(self):
        user_dict = {
            'email': self.user_vasco.email,
            'token': 'jwt.mocked'
        }

        send_confirmation_email(user=user_dict)

        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]

        self.assertEqual(sent_mail.from_email, 'FootHub Team <no-reply@foothub.com>')
        self.assertEqual(sent_mail.subject, "FootHub Registration")
        self.assertIn("Use the link to confirm email: ", sent_mail.body)
        self.assertIn(f'{settings.FRONTEND_URL}/confirm-registration?token={user_dict["token"]}', sent_mail.body)
        self.assertEqual(sent_mail.to, [user_dict['email']])
