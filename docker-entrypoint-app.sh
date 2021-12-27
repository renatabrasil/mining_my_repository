#!/usr/bin/dumb-init /bin/sh

cd /usr/web/app;

python manage.py migrate --settings=mining_my_repository.settings.dev;

eval "$@";