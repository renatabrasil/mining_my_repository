from .base import *

os.environ.setdefault("DJANGO_SETTINGS_MODULE", __file__)
# import django
# django.setup()
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        'TEST': {
            'NAME': 'test_database',
        },
    }
}

DEBUG = True
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
