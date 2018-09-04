# Kafka Explorer

![Build status](https://img.shields.io/docker/build/qvantel/kafka-explorer.svg)
![Docker pulls](https://img.shields.io/docker/pulls/qvantel/kafka-explorer.svg)

Welcome to the kafka explorer repo! This tool is a web app for searching kafka topics. It's been tested with kafka
0.10.x and 1.1.x but should have no problems with anything from 0.10.0 to 1.x and limited functionality with 0.9.x.

![Timestamp search screenshot](screenshots/timestamp_search.png)

## Deployment

To deploy simply use the following command filling in the broker list:

```shell
docker run -d -m 512m --log-driver json-file --log-opt max-size="1m" \
  -p 5000:5000 \
  -e "KAFKA_BOOTSTRAP_BROKERS=<list of bootstrap brokers>" \
  --name kafka-explorer qvantel/kafka-explorer:0.7.0
```

The following environment variables are available:

- `KAFKA_BOOTSTRAP_BROKERS`: List of comma separated broker `host:port` pairs.
- `LOG_LEVEL`: Gunicorn logging level, INFO by default
- `WORKERS`: Number of gevent workers, min(10, (cpus * 2) +  1) by default
- `REPORT_INTERVAL`: Interval at which a metadata event with a refreshed total message count will be generated (every
                     100 consumed messages by default)
- `BROKER_API_VERSION`: Kafka API version to use, '0.10.2.1' by default

## Use

Once deployed go to localhost:5000 on your web browser (assuming you're running it locally or have port forwarding
configured).

### Search Types

  - Plain text: To find messages that contain a certain string in a topic select plain and fill in the value field.

  - Json key value: To find specific key value pairs in the messages of a topic select json and fill in both parameters.
    In this type of search, messages that aren't valid json strings will be ignored (unless only exclusions are applied).

### Search Terms

At least one search term is required and up to four can be used in parallel. When using multiple terms, kafka explorer
will show results that don't match **any** of the excluded and match **all** of the included (if any).

### Start Timestamp

Search scope can be limited to messages newer than a certain moment in time. This is done by pressing the toggle to the
right of the "Start at" field and selecting a date and time.

### Limit

To avoid running out of memory in the client, the ui will show no more than 500 results at any given moment. The
normal behaviour is to show the results as a rolling window, showing the latest results first, but this can be
changed to stop upon reaching the limit.

### Export

It is possible to export the current result set (or a subset) to a csv file or a zip containing one file per message at
any moment.

Fist of all, if you want to export all the results make sure checkboxes aren't showing to the left of each item, if this
is happening just press the select all button next to the export button and they will disappear. On the other hand, if
you wish to select a subset, press the show checkboxes button at the same location and pick the messages you want to
save.

Once at least one message is selected, the export button will turn blue. At this point just press the button and then
select a mode. After picking, your browser will start the download (the file will be named `<topic>_<browser time>` with
an extension dependant on the export mode).