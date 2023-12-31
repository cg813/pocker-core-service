import os

from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
# ALERT in production env 'config.settings' needs to CHANGE
os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.environ.get("PROJECT_SETTINGS"))

app = Celery('mima')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object(settings, namespace='CELERY')

app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
