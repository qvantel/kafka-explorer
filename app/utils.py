from functools import reduce
import json

from kafka.consumer.fetcher import ConsumerRecord


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


def headers_to_json(headers):
    """
    For getting a usable header array for the ui
    :param headers: Headers as a tuple array
    :return: Headers as a json object array with attributes for key and value
    """
    return list(map(lambda header: {'key': header[0], 'value': header[1].decode('utf-8')}, headers))


def message_to_sse(message: ConsumerRecord, key: str, value: str, consumed: int):
    """
    For building valid server-sent events from kafka messages
    :param message: Original kafka message object
    :param key: Parsed key of the message
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
                'headers': headers_to_json(message.headers),
                'key': key,
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


def get_timestamp_offsets(consumer, start):
    """
    For obtaining the offsets for the earliest messages in each partition with a timestamp greater or equal to the given
    :param consumer: Kafka consumer object
    :param start: Timestamp in milliseconds
    :return: TopicPartition to int (offset) dict
    """
    partitions = list(consumer.assignment())
    pairs = map(lambda item: {item: start}, partitions)
    acc = {}
    for pair in pairs:
        acc.update(pair)
    offsets = consumer.offsets_for_times(acc)
    end = consumer.end_offsets(partitions)
    result = {}
    for offset in offsets.items():
        if offset[1]:
            result.update({offset[0]: offset[1].offset})
        else:
            result.update({offset[0]: end[offset[0]]})
    return result


def get_message_count(consumer, start):
    """
    For obtaining the current total message count of all the assigned partitions for a kafka consumer, from the
    beginning or a given timestamp
    :param consumer: Kafka consumer object
    :param start: Timestamp in milliseconds (use -1 to disable)
    :return: Sum of the message counts
    """
    partitions = list(consumer.assignment())
    if start >= 0:
        beginning = get_timestamp_offsets(consumer, start)
    else:
        beginning = consumer.beginning_offsets(partitions)
    end = consumer.end_offsets(partitions)
    return reduce(lambda acc, key: acc + end[key] - beginning[key], end, 0)


def seek_to_timestamp(consumer, start):
    """
    For seeking a consumer's offsets to the first message with an equivalent or greater timestamp in each partition (be
    aware that if no message with the same or greater timestamp is present in a partition it will just seek to it's
    end to avoid failures)
    :param consumer: Kafka consumer object
    :param start: Timestamp in milliseconds
    :return: Nothing, it just modifies the state of the consumer
    """
    partitions = list(consumer.assignment())
    offsets = get_timestamp_offsets(consumer, start)
    for partition in partitions:
        consumer.seek(partition, offsets[partition])
