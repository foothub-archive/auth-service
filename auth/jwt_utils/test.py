from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework_jwt.settings import api_settings

from jwt_utils.handlers import jwt_payload_handler, jwt_response_payload_handler

User = get_user_model()


USER_CHI = {
    'username': 'Chi',
    'email': 'chi@foothub.com',
    'password': 'verystrong3'
}


class TestPayLoadHandler(TestCase):

    def test_settings(self):
        self.assertEqual(api_settings.JWT_PAYLOAD_HANDLER, jwt_payload_handler)

    def test_payload_generation(self):
        user_chi = User.objects.create_user(**USER_CHI)

        payload = jwt_payload_handler(user_chi)

        self.assertEqual(len(payload), 4)
        self.assertIn('uuid', payload)
        self.assertIn('exp', payload)
        self.assertEqual(payload['username'], USER_CHI['username'])
        self.assertEqual(payload['email'], USER_CHI['email'])


class TestResponsePayLoadHandler(TestCase):

    def test_settings(self):
        self.assertEqual(api_settings.JWT_RESPONSE_PAYLOAD_HANDLER, jwt_response_payload_handler)

    def test_payload_generation(self):
        user_chi = User.objects.create_user(**USER_CHI)

        payload = jwt_response_payload_handler('dummy_token', user_chi)

        self.assertEqual(len(payload), 2)
        self.assertIn('token', payload)
        self.assertIn('user', payload)

        self.assertIn(payload['token'], 'dummy_token')

        self.assertIn('uuid', payload['user'])
        self.assertIn('username', payload['user'])
        self.assertIn('email', payload['user'])
        self.assertEqual(payload['user']['username'], USER_CHI['username'])
        self.assertEqual(payload['user']['email'], USER_CHI['email'])
