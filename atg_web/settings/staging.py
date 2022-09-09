from datetime import timedelta
from .base import * 

base_path = '/var/www/PYTHON/smarteye_api'
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

CORS_ORIGIN_ALLOW_ALL = True

#Test pic date and time
# USE_TZ = True

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=30),
    'AUTH_HEADER_TYPES': ('Bearer', 'JWT')
}


#EMAIL CONFIG
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_USE_SSL = config('EMAIL_USE_SSL',cast=bool)
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

CELERY_BROKER_URL = CELERY_BROKER_URL = config('CELERY_BROKER_URL')


#staging logging for debugging


REQUEST_LOGGING_SENSITIVE_HEADERS = [True]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(name)s.%(funcName)s:%(lineno)s- %(message)s'
        }
    },
    'handlers': {
        'logfile': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(base_path, 'server.log'),
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['logfile'],
            'level': 'WARNING'
        },
    },
}