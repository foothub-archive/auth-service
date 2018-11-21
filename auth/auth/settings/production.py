from .base import *  # noqa: F403


DEBUG = False

INSTALLED_APPS.append('gunicorn')  # noqa: F405

ALLOWED_HOSTS = ["*"]


JWT_AUTH: dict = {
    **JWT_AUTH,
    'JWT_VERIFY_EXPIRATION': True,
}


FRONTEND_URL = 'acciaioli.duckdns.org'
