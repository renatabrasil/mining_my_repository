# Mining my repository

SonarCloud: [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=renatabrasil_mining_my_repository&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=renatabrasil_mining_my_repository) [![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=renatabrasil_mining_my_repository&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=renatabrasil_mining_my_repository) [![Coverage](https://sonarcloud.io/api/project_badges/measure?project=renatabrasil_mining_my_repository&metric=coverage)](https://sonarcloud.io/summary/new_code?id=renatabrasil_mining_my_repository)

CodeClimate: [![Maintainability](https://api.codeclimate.com/v1/badges/a831076e1130f16dfada/maintainability)](https://codeclimate.com/github/renatabrasil/mining_my_repository/maintainability)

***

1. [Introduction](#introduction)
    1. [Next steps](#next-steps)
2. [Getting Started](#Getting-Started)
    1. [Prerequisites](#prerequisites)
3. [Running](#running)
    1. [Application](#application)
    2. [Tests](#tests)
4. [Built With](#built-with)
5. [Authors](#authors)
6. [License](#license)

## Introduction

Main functionalities: it collects the individual contributions of the developers and analyzes the impact of commits in
Java projects.

### Next steps:

* Implement unit tests
* Refactoring design to reach a sustainable level of maintainability
    * Change functions based view for class based views
    * Separate views from user cases
    * Bring some logic to models

## Getting Started

Choose a local directory and clone this repository using:

```shell
> git clone https://github.com/renatabrasil/mining_my_repository.git
```

### Prerequisites

* Python 3.7.4
* GitPython (3.1.3): https://pypi.org/project/GitPython/3.0.2/
* PyDriller (1.9.2): https://pydriller.readthedocs.io/en/latest/intro.html
* Django 3.0 (or above)
* Django-mathfilters: https://pypi.org/project/django-mathfilters/0.4.0/
* PyYAML (5.1.2 or above) = https://pypi.org/project/PyYAML/#history
* numPY
* unicoded
* whitenoise
* matplotlib: https://matplotlib.org/users/installing.html
* pandas: https://pandas.pydata.org/

## Running

Instructions for running the application and testing.

### Application

```shell
> python manage.py migrate
> python manage.py loaddata init.yaml
> python manage.py runserver
```

#### With docker

```shell
> docker-compose up --build
```

##### Logs

```shell
> http://localhost:3000
```

Loki query:

```logQL
> {container_name="mining_my_repository_app_1"} | json
```

### Tests

To run django unit tests:

```shell
> python manage.py test
```

To run and generate coverage report:

```shell
> coverage run manage.py test <module - or empty to run for all Apps>
```

To generate test coverage report:

```shell
> coverage html
```

## Built With

* [PyDriller](https://github.com/ishepard/pydriller/) - Python Framework to analyse Git repositories

## Authors

* **Renata Brasil**

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details
