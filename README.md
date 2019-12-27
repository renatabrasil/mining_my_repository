# Mining my repository

Pre-requisites:
- Python 3.7.4
- GitPython (3 or above): https://pypi.org/project/GitPython/3.0.2/
- PyDriller (1.9 or above): https://pydriller.readthedocs.io/en/latest/intro.html
- Django 3.0 (or above)
- Django-mathfilters: https://pypi.org/project/django-mathfilters/0.4.0/
- PyYAML (5.1.2 or above) = https://pypi.org/project/PyYAML/#history
- numPY
- unicoded
- whitenoise
- matplotlib: https://matplotlib.org/users/installing.html
- pandas: https://pandas.pydata.org/


Run:

- python manage.py migrate
- python manage.py loaddata init.yaml
- python manage.py runserver

Tests:

- python -m coverage run manage.py test contributions
- python -m coverage run manage.py test architecture

ou

- python -m coverage run --source '.' --omit 'manage.py,mining_my_repository/*,*/migrations/*,*__init__*' manage.py test contributions
- python -m coverage run --source '.' --omit '*/migrations/*,*__init__*' manage.py test contributions architecture

---

- coverage html