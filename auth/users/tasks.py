from django.db.models import signals
from celery import shared_task

from .models import User


@shared_task
def create_core_profile(user_uuid: str) -> bool:
    pass


@shared_task
def send_confirmation_email(user_jwt: str) -> bool:
    pass


def on_create(user: User) -> None:
    create_core_profile.delay(user_uuid=user.uuid)
    send_confirmation_email(user_jwt=user.create_jwt())
