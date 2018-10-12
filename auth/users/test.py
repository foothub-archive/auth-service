from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


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


class TestUserManager(TestCase):
    def test_create_user_success(self):
        self.assertEqual(User.objects.count(), 0)

        user = User.objects.create_user(**USER_VASCO)

        self.assertEqual(User.objects.count(), 1)

        self.assertEqual(user.username, USER_VASCO['username'])
        self.assertEqual(user.email, USER_VASCO['email'])
        self.assertTrue(user.check_password(USER_VASCO['password']))


class TestUserCreation(APITestCase):
    URL = '/create-user'
    CONTENT_TYPE = 'json'

    def setUp(self):
        self.user_vasco = User.objects.create_user(**USER_VASCO)

    def test_create_user_400_forbidden(self):
        self.assertEqual(User.objects.count(), 1)
        bad_user = dict(USER_VASCO)
        bad_user['username'] = 'me'

        response = self.client.post(self.URL, bad_user, format=self.CONTENT_TYPE)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_create_user_400_existing(self):
        self.assertEqual(User.objects.count(), 1)

        response = self.client.post(self.URL, USER_VASCO, format=self.CONTENT_TYPE)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_create_user_200(self):
        self.assertEqual(User.objects.count(), 1)

        response = self.client.post(self.URL, USER_JOAO, format=self.CONTENT_TYPE)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(User.objects.count(), 2)

        user_joao = User.objects.get(username=USER_JOAO['username'])

        self.assertEqual(user_joao.username, USER_JOAO['username'])
        self.assertEqual(user_joao.email, USER_JOAO['email'])
        self.assertTrue(user_joao.check_password(USER_JOAO['password']))


class TestJwtViews(APITestCase):
    def setUp(self):
        self.user_vasco = User.objects.create_user(**USER_VASCO)

