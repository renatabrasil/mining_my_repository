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
COPY ./ /usr/web/app

RUN chown -R 1001:1001 /usr/web/
USER 1001:1001
WORKDIR /usr/web/

ENTRYPOINT [ "/usr/web/docker-entrypoint-app.sh" ]