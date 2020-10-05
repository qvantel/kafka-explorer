FROM python:3.8.2-alpine3.11

RUN mkdir -p /opt/docker

ADD requirements.txt /opt/docker

WORKDIR /opt/docker

RUN apk add --no-cache gcc musl-dev && \
    pip install -r requirements.txt && \
    apk --purge del gcc musl-dev

ADD . /opt/docker

ENV VERSION=0.9.1

EXPOSE 5000

ENTRYPOINT [ "gunicorn", "-c", "gunicorn.config.py", "app:app"]