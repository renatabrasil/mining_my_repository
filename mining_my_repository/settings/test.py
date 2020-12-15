from .base import *
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", __file__)
import django
django.setup()
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

DEBUG = True
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

