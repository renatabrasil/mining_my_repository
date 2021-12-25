import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

DEBUG = False

# Observability
sentry_sdk.init(
    dsn="https://76f8b2c1a0f54883bcd435787eb68e5a@o1099084.ingest.sentry.io/6123558",
    integrations=[DjangoIntegration()],
    debug=True,
    environment="production",

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,

    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True
)
