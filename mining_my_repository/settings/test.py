import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *

print(f"SETTINGS test CARREGADO")

TESTING = True
os.environ.setdefault("DJANGO_SETTINGS_MODULE", __file__)

import django

#
# #
django.setup()
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

print(TESTS_IN_PROGRESS)

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': os.path.join(BASE_DIR, 'test_db.sqlite3'),
}

INSTALLED_APPS += ['contributions', ]

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

# Observability
sentry_sdk.init(
    dsn="https://76f8b2c1a0f54883bcd435787eb68e5a@o1099084.ingest.sentry.io/6123558",
    integrations=[DjangoIntegration()],
    debug=True,
    environment="test",

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,

    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True
)
