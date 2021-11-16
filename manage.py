#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

settings = {'runserver': 'mining_my_repository.settings.dev', 'test': 'mining_my_repository.settings.test',
            'prod': 'mining_my_repository.settings.prod'}


def __get_settings_file(arg):
    if arg not in settings:
        return 'mining_my_repository.settings.dev'
    else:
        return settings[arg]


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mining_my_repository.settings.dev')
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
