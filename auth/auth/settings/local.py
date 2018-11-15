from .base import *  # noqa: F403 F401


DEBUG = True

ALLOWED_HOSTS = [
    '0.0.0.0'
]

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025

FRONTEND_URL = '0.0.0.0:8080'
