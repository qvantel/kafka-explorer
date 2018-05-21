from functools import reduce
import json


def decode_search_pairs(raw_pairs):
    """
    For converting serialized search pairs into usable objects
    :param raw_pairs: String representation of a search pair list
    :return: List of search pair objects
    """
    clean = filter(lambda pair: '<|,|>' in pair, raw_pairs.split('<|;|>'))
    return list(map(lambda pair: {'key': pair.split('<|,|>')[0], 'value': pair.split('<|,|>')[1]}, clean))


def find(key, value, dictionary):
    """
    For performing recursive json key pair searches
    :param key: Target object key
    :param value: Target object value
    :param dictionary: Collection in which to look
    :return: True if a match is found, nothing if not
    """
    for k, v in dictionary.items():
        if k == key and value in str(v):
            yield True
        elif isinstance(v, dict):
            for result in find(key, value, v):
                yield result
        elif isinstance(v, list):
            for d in v:
                if isinstance(d, dict) or isinstance(d, list):
                    for result in find(key, value, d):
                        yield result
                elif k == key and value in str(d):
                    yield True


def is_present(key, value, dictionary):
    """
    Wrapper for the find function
    :param key: Target object key
    :param value: Target object value
    :param dictionary: Collection in which to look
    :return: True if a match is found, False if not
    """
    return reduce(lambda x, y: x or y, list(find(key, value, dictionary)), False)


def message_to_sse(message, value, consumed):
    """
    For building valid server-sent events from kafka messages
    :param message: Original kafka message object
    :param value: Parsed payload of the message
    :param consumed: Current consumed count
    :return: Json string for the resulting SSE
    """
    data = {
                'topic': message.topic,
                'consumed': consumed,
                'timestamp': message.timestamp,
                'partition': message.partition,
                'offset': message.offset,
                'key': message.key if isinstance(message.key, str) else 'not a string',
                'value': value
            }
    return "data: %s\n\n" % (json.dumps(data))


def consumer_meta_to_sse(consumer, count, consumed):
    """
    For building valid named server-side events from kafka consumer metadata
    :param consumer: Kafka consumer object
    :param count: Last total message count
    :param consumed: Current consumed count
    :return: Json string for the resulting SSE
    """
    partitions = list(consumer.assignment())
    data = {
                'partitions': len(partitions),
                'total': count,
                'consumed': consumed
           }
    return "event: metadata\ndata: %s\n\n" % (json.dumps(data))


def get_message_count(consumer):
    """
    For obtaining the current total message count of all the assigned partitions for a kafka consumer
    :param consumer: Kafka consumer object
    :return: Sum of the message counts
    """
    partitions = list(consumer.assignment())
    start = consumer.beginning_offsets(partitions)
    end = consumer.end_offsets(partitions)
    return reduce(lambda acc, key: acc + end[key] - start[key], end, 0)
