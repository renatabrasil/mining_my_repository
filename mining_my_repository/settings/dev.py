import os

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

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
        'loki': {
            'class': 'django_loki.LokiFormatter',  # required
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] [%(funcName)s] %(message)s',
            # optional, default is logging.BASIC_FORMAT
            'datefmt': '%Y-%m-%d %H:%M:%S',  # optional, default is '%Y-%m-%d %H:%M:%S'
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
        'loki': {
            'level': 'INFO',  # required
            'class': 'django_loki.LokiHttpHandler',  # required
            # 'url': 'http://loki:3100/loki/api/v1/push',
            # 'tags': {'app': 'django', 'env': 'dev'},
            'host': 'loki',  # required, your grafana/Loki server host, e.g:192.168.57.242
            'formatter': 'loki',  # required, loki formatter,
            'port': 3100,  # optional, your grafana/Loki server port, default is 3100
            'timeout': 0.5,  # optional, request Loki-server by http or https time out, default is 0.5
            'protocol': 'http',  # optional, Loki-server protocol, default is http
            'source': 'Loki',  # optional, label name for Loki, default is Loki
            'src_host': 'localhost',  # optional, label name for Loki, default is localhost
            'tz': 'UTC',  # optional, timezone for formatting timestamp, default is UTC, e.g:Asia/Shanghai
        },
    },
    'loggers': {
        'django': {
            'handlers': ['loki'],
            # 'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'level': 'INFO',
            'propagate': False,
        },
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
