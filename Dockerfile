FROM python:3.6.5-alpine3.7

RUN mkdir -p /opt/docker

ADD requirements.txt /opt/docker

WORKDIR /opt/docker

RUN apk add --no-cache gcc musl-dev && \
    pip install -r requirements.txt && \
    apk --purge del gcc musl-dev

ADD . /opt/docker

EXPOSE 5000

CMD [ "gunicorn", "-c", "gunicorn.config.py", "app:app"]