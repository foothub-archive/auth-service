from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

celery_app = Celery('auth')

celery_app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
celery_app.autodiscover_tasks()

@celery_app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))