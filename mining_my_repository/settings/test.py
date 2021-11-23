from .base import *

print(f"SETTINGS test CARREGADO")

TESTING = True
os.environ.setdefault("DJANGO_SETTINGS_MODULE", __file__)
os.environ["ENVIRONMENT_VARIABLE"] = "test"

# DATABASES['default'] = dj_database_url.config()

# import django
# django.setup()
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

print(TESTS_IN_PROGRESS)

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '[%(levelname)s] %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'formatter': 'simple',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        '': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        }
    },
}
