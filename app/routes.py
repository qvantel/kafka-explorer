from flask import render_template, Response, request
from kafka import KafkaConsumer
from app import app
from app import utils

import logging
import json
import uuid
import os

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

# Required vars

try:
    servers = os.environ['KAFKA_BOOTSTRAP_BROKERS']
except KeyError:
    print('Error: The env var KAFKA_BOOTSTRAP_BROKERS needs to be defined!')
    raise

# Optional vars

try:
    api_version = tuple(map(lambda x: int(x), os.environ.get('BROKER_API_VERSION', '1.1.1').split('.')))
except ValueError:
    print('Error: The env var BROKER_API_VERSION has to be a string formed by numbers and dots!')
    raise

report_interval = int(os.environ.get('REPORT_INTERVAL', 100))
security_protocol = os.environ.get('SECURITY_PROTOCOL', 'PLAINTEXT')
ssl_args = {
    'ssl_check_hostname': os.environ.get('SSL_CHECK_HOSTNAME', 'True').lower() == 'true',
    'ssl_cafile': os.environ.get('SSL_CAFILE', None),
    'ssl_certfile': os.environ.get('SSL_CERTFILE', None),
    'ssl_keyfile': os.environ.get('SSL_KEYFILE', None),
    'ssl_password': os.environ.get('SSL_PASSWORD', None),
    'ssl_ciphers': os.environ.get('SSL_CIPHERS', None)
}

if security_protocol != 'PLAINTEXT':
    app.logger.debug(json.dumps(ssl_args))


@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Pablo'}
    return render_template('index.html', title='Home', user=user)


@app.route('/topics')
def topics():
    consumer = KafkaConsumer(
        bootstrap_servers=servers,
        api_version=api_version,
        security_protocol=security_protocol,
        ssl_context=utils.get_ssl_context(app.logger, ssl_args)
    )
    app.logger.debug(f'Consumer config: {consumer.config}')
    results = consumer.topics()
    consumer.close()
    return json.dumps(sorted(results))


@app.route('/count')
def count():
    topic = request.args.get('topic')
    consumer = KafkaConsumer(
        topic,
        group_id='kafka-explorer-' + str(uuid.uuid4()),
        bootstrap_servers=servers,
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        api_version=api_version,
        security_protocol=security_protocol,
        ssl_context=utils.get_ssl_context(app.logger, ssl_args)
    )
    consumer.poll(1)
    result = utils.get_message_count(consumer, -1)
    consumer.close()
    return str(result)


@app.route('/search')
def search():
    def generate(args):
        topic = args.get('topic')
        search_type = args.get('type')
        exclude = utils.decode_search_pairs(args.get('exclude'))
        include = utils.decode_search_pairs(args.get('include'))
        start = int(args.get('start', '-1'))

        consumer = KafkaConsumer(
            topic,
            group_id='kafka-explorer-' + str(uuid.uuid4()),
            bootstrap_servers=servers,
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            api_version=api_version,
            security_protocol=security_protocol,
            ssl_context=utils.get_ssl_context(app.logger, ssl_args)
        )

        consumed = 0
        consumer.poll(1)  # Poll to load metadata
        last_count = utils.get_message_count(consumer, start)
        yield utils.consumer_meta_to_sse(consumer, last_count, consumed)
        if start >= 0:
            utils.seek_to_timestamp(consumer, start)  # Seek to start point
        else:
            consumer.seek_to_beginning()  # Reset offsets in case poll consumed any messages

        for message in consumer:
            key = 'None' if message.key is None else message.key.decode('utf-8')
            value = message.value.decode('utf-8')
            consumed = consumed + 1
            if consumed % report_interval == 0 or consumed >= last_count:
                last_count = utils.get_message_count(consumer, start)
                yield utils.consumer_meta_to_sse(consumer, last_count, consumed)
            if search_type == 'json':
                try:
                    jdata = json.loads(value)
                    if not any(utils.is_present(pair['key'], pair['value'], jdata) for pair in exclude):
                        if len(include) == 0 or \
                                all(utils.is_present(pair['key'], pair['value'], jdata) for pair in include):
                            yield utils.message_to_sse(message, key, value, consumed)
                except ValueError:
                    pass
            elif not any((pair['value'] in value or (key != 'None' and pair['value'] in key)) for pair in exclude):
                if len(include) == 0 or \
                        all((pair['value'] in value or (key != 'None' and pair['value'] in key)) for pair in include):
                    yield utils.message_to_sse(message, key, value, consumed)
        consumer.close()

    return Response(generate(request.args.copy()), mimetype='text/event-stream')
