from django.core.mail import send_mail

from celery import shared_task

from .models import User


@shared_task
def create_core_profile(user_uuid: str) -> bool:
    pass


@shared_task
def send_confirmation_email(user_email: str, user_jwt: str, url: str) -> bool:
    message = f'Use the link to confirm email: {url}?jwt={user_jwt}'

    send_mail(
        subject='FootHub Registration',
        message=message,
        from_email='FootHub Team <no-reply@foothub.com>',
        recipient_list=[user_email],
        fail_silently=False,
    )


def on_create(user: User) -> None:
    assert False
    create_core_profile.delay(user_uuid=user.uuid)
    send_confirmation_email.delay(
        user_email=user.email,
        user_jwt=user.create_jwt(),
    )
