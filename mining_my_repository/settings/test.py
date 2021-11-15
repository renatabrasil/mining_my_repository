from .base import *

os.environ.setdefault("DJANGO_SETTINGS_MODULE", __file__)
os.environ["ENVIRONMENT_VARIABLE"] = "test"
# import django
# django.setup()
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

print(TESTS_IN_PROGRESS)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        'TEST': {
            'NAME': 'test_database',
        },
    }
}

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
