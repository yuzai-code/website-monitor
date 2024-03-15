# celery.py

from __future__ import absolute_import, unicode_literals

import logging
import os

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WebsiteMonitor.settings')

app = Celery('WebsiteMonitor')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


logger = logging.getLogger('Lottery_data')


