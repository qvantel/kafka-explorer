from flask import render_template, Response, request
from kafka import KafkaConsumer
from app import app
from app import utils

import json
import uuid
import os

try:
    servers = os.environ['KAFKA_BOOTSTRAP_BROKERS']
except KeyError:
    print('Error: The env var KAFKA_BOOTSTRAP_BROKERS needs to be defined!')
    raise

try:
    api_version = tuple(map(lambda x: int(x), os.environ.get('BROKER_API_VERSION', '0.10').split('.')))
except ValueError:
    print('Error: The env var BROKER_API_VERSION has to be a string formed by numbers and dots!')
    raise

report_interval = int(os.environ.get('REPORT_INTERVAL', 100))


@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Pablo'}
    return render_template('index.html', title='Home', user=user)


@app.route('/topics')
def topics():
    consumer = KafkaConsumer(bootstrap_servers=servers)
    results = consumer.topics()
    consumer.close()
    return json.dumps(list(results))


@app.route('/count')
def count():
    topic = request.args.get('topic')
    consumer = KafkaConsumer(
        topic,
        group_id='kafka-explorer-' + str(uuid.uuid4()),
        bootstrap_servers=servers,
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        api_version=api_version
    )
    consumer.poll(1)
    result = utils.get_message_count(consumer)
    consumer.close()
    return str(result)


@app.route('/search')
def search():
    def generate(args):
        topic = args.get('topic')
        search_type = args.get('type')
        exclude = utils.decode_search_pairs(args.get('exclude'))
        include = utils.decode_search_pairs(args.get('include'))

        consumer = KafkaConsumer(
            topic,
            group_id='kafka-explorer-' + str(uuid.uuid4()),
            bootstrap_servers=servers,
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            api_version=api_version
        )

        consumed = 0
        consumer.poll(1)  # Poll to load metadata
        last_count = utils.get_message_count(consumer)
        yield utils.consumer_meta_to_sse(consumer, last_count, consumed)
        consumer.seek_to_beginning()  # Reset offsets in case poll consumed any messages

        for message in consumer:
            value = message.value.decode('utf-8')
            consumed = consumed + 1
            if consumed % report_interval == 0 or consumed >= last_count:
                last_count = utils.get_message_count(consumer)
                yield utils.consumer_meta_to_sse(consumer, last_count, consumed)
            if search_type == 'json':
                try:
                    jdata = json.loads(value)
                    if not any(utils.is_present(pair['key'], pair['value'], jdata) for pair in exclude):
                        if len(include) == 0 or all(utils.is_present(pair['key'], pair['value'], jdata) for pair in include):
                            yield utils.message_to_sse(message, value, consumed)
                except ValueError:
                    pass
            elif not any(pair['value'] in value for pair in exclude):
                if len(include) == 0 or all(pair['value'] in value for pair in include):
                    yield utils.message_to_sse(message, value, consumed)
        consumer.close()

    return Response(generate(request.args.copy()), mimetype='text/event-stream')
