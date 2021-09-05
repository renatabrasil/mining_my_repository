# Mining my repository

SonarCloud: [![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=renatabrasil_mining_my_repository&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=renatabrasil_mining_my_repository)

CodeClimate: [![Maintainability](https://api.codeclimate.com/v1/badges/a831076e1130f16dfada/maintainability)](https://codeclimate.com/github/renatabrasil/mining_my_repository/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/a831076e1130f16dfada/test_coverage)](https://codeclimate.com/github/renatabrasil/mining_my_repository/test_coverage)

Main functionalities: it collects the individual contributions of the developers and analyzes the impact of commits in Java projects.

**Next steps:**

- Clear the code and prepare the first release
- Implement the infrastructure for testing
- Implement unit tests
- Set up test and production environment

## Getting Started

Choose a local directory and clone this repository using:
```
git clone https://github.com/renatabrasil/mining_my_repository.git
```

### Prerequisites


- Python 3.7.4
- GitPython (3.1.3): https://pypi.org/project/GitPython/3.0.2/
- PyDriller (1.9.2): https://pydriller.readthedocs.io/en/latest/intro.html
- Django 3.0 (or above)
- Django-mathfilters: https://pypi.org/project/django-mathfilters/0.4.0/
- PyYAML (5.1.2 or above) = https://pypi.org/project/PyYAML/#history
- numPY
- unicoded
- whitenoise
- matplotlib: https://matplotlib.org/users/installing.html
- pandas: https://pandas.pydata.org/

## Running

Instructions for running the application and testing.

### Application

```
python manage.py migrate
python manage.py loaddata init.yaml
python manage.py runserver
```


### Tests

```
coverage run manage.py test <module - or empty to run for all Apps>
```
To generate test coverage report:

```
coverage html
```

## Built With

* [PyDriller](https://github.com/ishepard/pydriller/) - Python Framework to analyse Git repositories


## Authors

* **Renata Brasil**

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details
