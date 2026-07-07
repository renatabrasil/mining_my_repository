FROM bitnami/python:3.8.2-prod

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y git && \
    apt-get install -y dumb-init

RUN mkdir -p /usr/web/config/gunicorn

COPY requirements.txt /usr/web/
RUN pip install --upgrade pip && \
    pip install -r /usr/web/requirements.txt

COPY ./config/gunicorn/gunicorn-* /usr/web/config/gunicorn/
COPY ./docker-entrypoint-app.sh /usr/web/
COPY architecture /usr/web/app/architecture
COPY common /usr/web/app/common
COPY config /usr/web/app/config
COPY contributions /usr/web/app/contributions
COPY dataanalysis /usr/web/app/dataanalysis
COPY infrastructure /usr/web/app/infrastructure
COPY lambdas /usr/web/app/lambdas
COPY mining_my_repository /usr/web/app/mining_my_repository
COPY scripts /usr/web/app/scripts
COPY manage.py pytest.ini setup.cfg .coveragerc sonar-project.properties /usr/web/app/

RUN chown -R 1001:1001 /usr/web/
USER 1001:1001
WORKDIR /usr/web/

ENTRYPOINT [ "/usr/web/docker-entrypoint-app.sh" ]
