from typing import Dict, Any

from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task
from rest_framework_jwt.settings import api_settings
from requests import post

from .models import User
from .serializers import ConfirmEmailSerializer


@shared_task
def broadcast_registration(user_uuid: str) -> bool:
    subscribers = [
        'http://core:8000/profiles',
    ]

    responses = []

    signed_user_uuid = api_settings.JWT_ENCODE_HANDLER({'uuid': user_uuid})

    for subscriber in subscribers:
        responses.append(post(url=subscriber, json={'token': signed_user_uuid}))

    return all([response.status_code == 201 for response in responses])


@shared_task
def send_confirmation_email(user: Dict[str, Any]) -> bool:
    url = f'{settings.FRONTEND_URL}/confirm-registration'
    message = f'Use the link to confirm email: {url}?token={user["token"]}'

    sent_mails = send_mail(
        subject='FootHub Registration',
        message=message,
        from_email='FootHub Team <no-reply@foothub.com>',
        recipient_list=[user['email']],
        fail_silently=False,
    )

    return sent_mails == 1


def on_create(user: User) -> None:
    broadcast_registration.delay(user_uuid=user.uuid)
    send_confirmation_email.delay(user=ConfirmEmailSerializer(user).data)
