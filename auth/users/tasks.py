from django.core.mail import send_mail
from django.conf import settings

from celery import shared_task

from .models import User


@shared_task
def send_confirmation_email(user: User) -> bool:
    url = f'{settings.FRONTEND_URL}/confirm-registration'
    user_email = user.email
    user_jwt = user.create_jwt()
    message = f'Use the link to confirm email: {url}?token={user_jwt}'

    sent_mails = send_mail(
        subject='FootHub Registration',
        message=message,
        from_email='FootHub Team <no-reply@foothub.com>',
        recipient_list=[user_email],
        fail_silently=False,
    )

    return sent_mails == 1


def on_create(user: User) -> None:
    send_confirmation_email.delay(user=user)
