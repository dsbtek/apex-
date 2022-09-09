"""
WSGI config for atg_web project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os
from decouple import config
from django.core.wsgi import get_wsgi_application


environment = config('ENVIRONMENT')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "atg_web.settings."+environment)

application = get_wsgi_application()
