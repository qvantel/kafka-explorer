FROM python:3.9.1-alpine3.12

RUN mkdir -p /opt/docker

ADD requirements.txt /opt/docker

WORKDIR /opt/docker

RUN apk add --no-cache gcc musl-dev libffi-dev make && \
    pip install -r requirements.txt && \
    apk --purge del gcc musl-dev libffi-dev make

ADD . /opt/docker

ENV VERSION=0.9.2

EXPOSE 5000

ENTRYPOINT [ "gunicorn", "-c", "gunicorn.config.py", "app:app"]