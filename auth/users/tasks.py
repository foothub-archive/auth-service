from typing import Dict, Any
from django.core.mail import send_mail
from django.conf import settings

from celery import shared_task

from .models import User
from .serializers import ConfirmEmailSerializer


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
    send_confirmation_email.delay(user=ConfirmEmailSerializer(user).data)
