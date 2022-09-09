from .base import *
from decouple import config
#base_path = '/Users/smartflowtechnology/Desktop/sm/smart-eye-api'

#USE_TZ = True
ALLOWED_HOSTS = ['*']

CORS_ORIGIN_ALLOW_ALL = True

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=30),
    'AUTH_HEADER_TYPES': ('Bearer', 'JWT')
}


# EMAIL CONFIG
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_USE_SSL = config('EMAIL_USE_SSL', cast=bool)
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# EMAIL CONFIG test cicd test cicd
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


PASSWORD_RESET_TIMEOUT_DAYS = 1

CELERY_BROKER_URL = CELERY_BROKER_URL = config('CELERY_BROKER_URL')
REQUEST_LOGGING_SENSITIVE_HEADERS = [True]


# INTERNAL_IPS = ("127.0.0.1",)
# INSTALLED_APPS += ("debug_toolbar",)  # noqa
# MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'handlers': {
#         'logfile': {
#             'class': 'logging.handlers.RotatingFileHandler',
#             'filename': os.path.join(base_path, 'server.log'),
          
#         },
#     },
#     'loggers': {
#         'django.request': {
#             'handlers': ['logfile'],
#             'level': 'DEBUG',  # change debug level as appropiate
#             'propagate': False,
#         },
#     },
# }