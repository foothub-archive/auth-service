from django.test import TestCase


class TestLocalSettings(TestCase):

    def setUp(self):
        import auth.settings.local as settings
        self.settings = settings

    def test_settings(self):
        self.assertTrue(self.settings.DEBUG)
        self.assertFalse(self.settings.JWT_AUTH['JWT_VERIFY_EXPIRATION'])

        self.assertEqual(self.settings.FRONTEND_URL, '0.0.0.0:8080')


class TestProductionSettings(TestCase):

    def setUp(self):
        import auth.settings.production as settings
        self.settings = settings

    def test_settings(self):
        self.assertFalse(self.settings.DEBUG)

        self.assertIn('gunicorn', self.settings.INSTALLED_APPS)

        self.assertTrue(self.settings.JWT_AUTH['JWT_VERIFY_EXPIRATION'])

        self.assertEqual(self.settings.FRONTEND_URL, 'acciaioli.duckdns.org')
