from .celery import celery_app

__all__ = ('celery_app',)

@celery_app.task
def t(msg):
    print(f'\n\n -> {msg}')

t.delay('HELLO REDIS')