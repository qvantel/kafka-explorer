FROM python:3.9.16-alpine3.17

RUN mkdir -p /opt/docker

ADD requirements.txt /opt/docker

WORKDIR /opt/docker

RUN apk add --no-cache gcc g++ musl-dev libffi-dev make && \
    pip install -r requirements.txt && \
    apk --purge del gcc g++ musl-dev libffi-dev make

ADD . /opt/docker

ENV VERSION=0.10.0

EXPOSE 5000

ENTRYPOINT [ "gunicorn", "-c", "gunicorn.config.py", "app:app"]
