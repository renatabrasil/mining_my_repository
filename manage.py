#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

settings = {'runserver': 'mining_my_repository.settings.dev', 'test': 'mining_my_repository.settings.test',
            'prod': 'mining_my_repository.settings.prod'}


def __get_settings_file(arg):
    if len(arg) == 0 or arg[1] not in settings:
        return 'mining_my_repository.settings.base'
    else:
        return settings[arg[1]]


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', __get_settings_file(sys.argv))
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
