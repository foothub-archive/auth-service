from django.core.mail import send_mail
from django.conf import settings

from rest_framework_jwt.settings import api_settings


from celery import shared_task

from requests import post

from .models import User


@shared_task
def create_core_profile(user_uuid: str) -> bool:
    core_service_url = 'http://core/profiles'
    signed_user_uuid = api_settings.JWT_ENCODE_HANDLER({'uuid': user_uuid})
    response = post(url=core_service_url, json={'token': signed_user_uuid})
    return response.status_code == 201


@shared_task
def send_confirmation_email(user_email: str, user_jwt: str, url: str) -> bool:
    message = f'Use the link to confirm email: {url}?jwt={user_jwt}'

    sent_mails = send_mail(
        subject='FootHub Registration',
        message=message,
        from_email='FootHub Team <no-reply@foothub.com>',
        recipient_list=[user_email],
        fail_silently=False,
    )

    return sent_mails == 1


def on_create(user: User) -> None:
    create_core_profile.delay(user_uuid=user.uuid)
    send_confirmation_email.delay(
        user_email=user.email,
        user_jwt=user.create_jwt(),
        url=settings.FRONTEND_URL,
    )
