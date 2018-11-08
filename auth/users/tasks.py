from celery import shared_task


@shared_task
def add(msg):
    print(f'\n\n-> {msg}\n\n')