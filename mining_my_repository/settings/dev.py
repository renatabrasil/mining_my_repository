import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *

print("SETTINGS DEV CARREGADO")

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", __file__)

DEBUG = True

# logging.basicConfig(filename='architecture.log', encoding='utf-8', level=logging.DEBUG)
LOGGING_CONFIG = None
LOGLEVEL = os.getenv('DJ_LOGLEVEL', 'info').upper()
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
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': 'logs/mining_my_repository.log',
            'when': 'D',  # this specifies the interval
            'interval': 1,  # defaults to 1, only necessary for other values
            'backupCount': 10,  # how many backup file to keep, 10 days
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'formatter': 'simple',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            # 'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        '': {
            'handlers': ['file'],
            # 'level': 'INFO',
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        }
    },
}

# Observability
sentry_sdk.init(
    dsn="https://76f8b2c1a0f54883bcd435787eb68e5a@o1099084.ingest.sentry.io/6123558",
    integrations=[DjangoIntegration()],
    debug=False,
    environment="dev",

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,

    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True
)
