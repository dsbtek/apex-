#!/usr/bin/env python
import os
import sys
from decouple import config

if __name__ == "__main__":
    environment = config('ENVIRONMENT')
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "atg_web.settings."+environment)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    from django.conf import settings
    if 'test' in sys.argv:
        if '--nomigrations' not in sys.argv:
            sys.argv.append('--nomigrations')
        settings.DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'test_database',
            }
        }

    
    execute_from_command_line(sys.argv)
