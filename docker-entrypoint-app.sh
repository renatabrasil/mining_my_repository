#!/usr/bin/dumb-init /bin/sh

cd /usr/web/app;

python manage.py makemigrations;
python manage.py migrate;
python manage.py loaddata init4.yaml;
#python manage.py runserver --settings=mining_my_repository.settings.dev;

eval "$@";