# Kafka Explorer

[![Build status](https://img.shields.io/docker/cloud/build/qvantel/kafka-explorer.svg)](https://hub.docker.com/r/qvantel/kafka-explorer/builds)
[![Docker pulls](https://img.shields.io/docker/pulls/qvantel/kafka-explorer.svg)](https://hub.docker.com/r/qvantel/kafka-explorer)
[![Release](https://img.shields.io/github/v/release/qvantel/kafka-explorer.svg)](https://github.com/qvantel/kafka-explorer/releases/latest)

Welcome to the Kafka Explorer repo! This tool is a web app for searching Kafka topics. It's been tested with Kafka
0.10.x, 1.1.x and 2.1.x but should have no problems with anything from 0.11.0.0 to 2.x and
limited functionality with 0.9.x and 0.10.0 (as headers weren't introduced till 0.11.0.0).

![Timestamp search screenshot](https://github.com/qvantel/kafka-explorer/raw/master/screenshots/timestamp_search.png)

## Deployment

For a simple deployment, the following command can be used (filling in the broker list):

```shell
docker run -d -m 256m --log-driver json-file --log-opt max-size="1m" \
  -p 5000:5000 \
  -e "KAFKA_BOOTSTRAP_BROKERS=<list of bootstrap brokers>" \
  --name kafka-explorer qvantel/kafka-explorer:0.9.3
```

Enabling one-way auth TLS (without server validation):

```shell
docker run -d -m 256m --log-driver json-file --log-opt max-size="1m" \
  -p 5000:5000 \
  -e "KAFKA_BOOTSTRAP_BROKERS=<list of bootstrap brokers>" \
  -e "SECURITY_PROTOCOL=SSL" \
  -e "SSL_CHECK_HOSTNAME=false" \
  -e "SSL_CIPHERS=<list of ssl ciphers>" \
  --name kafka-explorer qvantel/kafka-explorer:0.9.3
```

Enabling two-way auth TLS:

```shell
docker run -d -m 256m --log-driver json-file --log-opt max-size="1m" \
  -p 5000:5000 \
  -v <local directory containing client certificate, client key and CARoot>:<container path> \
  -e "LOG_LEVEL=DEBUG" \
  -e "KAFKA_BOOTSTRAP_BROKERS=<list of bootstrap brokers>" \
  -e "SECURITY_PROTOCOL=SSL" \
  -e "SSL_CHECK_HOSTNAME=false" \
  -e "SSL_CIPHERS=<list of ssl ciphers>" \
  -e "SSL_CAFILE=<container path to pem ca>" \
  -e "SSL_CERTFILE=<container path to pem cert>" \
  -e "SSL_KEYFILE=<container path to client key>" \
  --name kafka-explorer qvantel/kafka-explorer:0.9.3
```

The following environment variables are available:

| Variable                  | Required | Default                            | Description                                                                                                                                                                        |
|---------------------------|----------|------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| KAFKA_BOOTSTRAP_BROKERS   | YES      | N/A                                | List of comma separated broker `host:port` pairs                                                                                                                                   |
| LOG_LEVEL                 | NO       | INFO                               | Application/root log level, supported values are `TRACE`, `DEBUG`, `INFO`, `WARNING`, `ERROR` and `CRITICAL`                                                                       |
| GUNICORN_LOG_LEVEL        | NO       | INFO                               | Gunicorn log level, supported values are `DEBUG`, `INFO`, `WARNING`, `ERROR` and `CRITICAL`                                                                                        |
| KAFKA_LOG_LEVEL           | NO       | ERROR                              | Kafka log level, supported values are `DEBUG`, `INFO`, `WARNING`, `ERROR` and `CRITICAL`                                                                                           |
| MARATHON_APP_DOCKER_IMAGE | NO       | qvantel/kafka-explorer:${VERSION}? | Included in the `artifact_id` field of log messages, gets filled in automatically when ran through Marathon                                                                        |
| SERVICE_5000_NAME         | NO       | $SERVICE_NAME                      | Included in the `service_name` field of the log messages. If set, overrides whatever is defined in `$SERVICE_NAME`                                                                 |
| SERVICE_NAME              | NO       | kafka-explorer                     | Included in the `service_name` field of the log messages                                                                                                                           |
| WORKERS                   | NO       | min(10, (cpus * 2) +  1)           | Number of gevent workers or in simpler terms, how many processes are started to handle client requests                                                                             |
| REPORT_INTERVAL           | NO       | 100                                | Interval at which a metadata event with a refreshed total message count will be generated, defined as number of consumed messages between reports                                  |
| BROKER_API_VERSION        | NO       | 2.1.1                              | Kafka API version to use                                                                                                                                                           |
| SECURITY_PROTOCOL         | NO       | PLAINTEXT                          | Protocol used to communicate with brokers. Valid values are: PLAINTEXT (by default), SSL                                                                                           |
| SSL_CHECK_HOSTNAME        | NO       | true                               | Flag to configure whether ssl handshake should verify that the certificate matches the broker's hostname (case insensitive, anything other than 'true' will be evaluated to false) |
| SSL_CAFILE                | NO       | None                               | Optional filename of ca file to use in certificate verification                                                                                                                    |
| SSL_CERTFILE              | NO       | None                               | Optional filename of file in pem format containing the client certificate, as well as any ca certificates needed to establish the certificate’s authenticity                       |
| SSL_KEYFILE               | NO       | None                               | Optional filename containing the client private key                                                                                                                                |
| SSL_PASSWORD              | NO       | None                               | Optional password to be used when loading the certificate chain                                                                                                                    |
| SSL_CIPHERS               | NO       | None                               | Optionally set the available ciphers for ssl connections. It should be a string in the OpenSSL cipher list format                                                                  |

## Use

Once deployed go to localhost:5000 on your web browser (assuming you're running it locally or have port forwarding
configured).

### Search Types

  - Plain text: To find messages that contain a certain string in a topic select plain and fill in the value field. This
    type of search will also check the key of the Kafka message if present.

  - Json key value: To find specific attribute value pairs in the messages of a topic select json and fill in both
    parameters. In this type of search, messages that aren't valid json strings will be ignored (unless only exclusions
    are applied).

### Search Terms

At least one search term is required and up to four can be used in parallel. When using multiple terms, Kafka Explorer
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
an extension dependent on the export mode).

Note that headers and key will only be included in the csv export.

## Testing TLS

In order to test the TLS functionality, we will need to create a CA and client and server certificates. To do so, we
can follow these steps:

### In the server
##### We create a server keystore
```shell
keytool -keystore kafka.server.keystore.jks -alias localhost -validity 999 -genkey
```
##### We create CA certificate and key (to sign other certificates)
```shell
openssl req -new -x509 -keyout ca-key -out ca-cert -days 999
```
##### We add ca certificate to client truststore
```shell
keytool -keystore kafka.client.truststore.jks -alias CARoot -import -file ca-cert
```
##### We add CA certificate to client truststore
```shell
keytool -keystore kafka.server.truststore.jks -alias CARoot -importcert -file ca-cert
```
##### We create a certificate for the server
```shell
keytool -keystore kafka.server.keystore.jks -alias localhost -certreq -file cert-file
```
##### We sign the server certificate with the CA created before
```shell
openssl x509 -req -CA ca-cert -CAkey ca-key -in cert-file -out cert-signed -days 999 -CAcreateserial -passin pass:password
```
##### We store the CA certificate in the server keystore
```shell
keytool -keystore kafka.server.keystore.jks -alias CARoot -import -file ca-cert
```
##### We store the signed certificate in the server keystore
```shell
keytool -keystore kafka.server.keystore.jks -alias localhost -import -file cert-signed
```

### In the client
##### We create the client keystore
```shell
keytool -genkey -keystore kafka.client.keystore.jks -validity 365 -storepass "MyClientPassword123" -keypass "MyClientPassword123" -dname "CN=mylaptop1" -alias my-local-pc1 -storetype pkcs12
```
##### We create the client certificate (that we want to sign with the CA)
```shell
keytool -keystore kafka.client.keystore.jks -certreq -file client-cert-sign-request -alias my-local-pc1 -storepass "MyClientPassword123" -keypass "MyClientPassword123"
```
##### We sign the certificate with the CA (client certificate must be copied to CA's location in order to do this step)
```shell
openssl x509 -req -CA ca-cert -CAkey ca-key -in /tmp1/client-cert-sign-request -out /tmp1/client-cert-signed -days 365 -CAcreateserial -passin pass:server_password
```
##### We import the CA cert to client's truststore
```shell
keytool -keystore kafka.client.truststore.jks -alias CARoot -import -file ca-cert  -storepass "MyClientPassword123" -keypass "MyClientPassword123" -noprompt
```
##### We import the CA cert to client's keystore
```shell
keytool -keystore kafka.client.keystore.jks -alias CARoot -import -file ca-cert  -storepass "MyClientPassword123" -keypass "MyClientPassword123" -noprompt
```
##### We import the signed client certificate to the client's keystore
```shell
keytool -keystore kafka.client.keystore.jks -import -file client-cert-signed -alias my-local-pc1 -storepass "MyClientPassword123" -keypass "MyClientPassword123" -noprompt
```
##### We can use this command to list the content of a JKS
```shell
keytool -list -rfc -keystore kafka.client.keystore.jks
```
##### Now we extract the client's certificate from that JKS
```shell
keytool -exportcert -alias my-local-pc1 -keystore kafka.client.keystore.jks -rfc -file certificate.pem
```
##### We extract the client's key from the JKS
```shell
keytool -v -importkeystore -srckeystore kafka.client.keystore.jks -srcalias localhost -destkeystore cert_and_key.p12 -deststoretype PKCS12
```
##### And store it in key.pem
```shell
openssl pkcs12 -in cert_and_key.p12 -nocerts -nodes > key.pem.temp
(cat key.pem.temp | sed -n '/-----BEGIN PRIVATE KEY-----/,$p') > key.pem```
rm key.pem.temp
```
##### Then we get CARoot cert with this command
```shell
keytool -exportcert -alias CARoot -keystore kafka.client.keystore.jks -rfc \
        -file `CARoot.pem`
```

After completing this process, we have all the necessary files for a 2-way auth TLS connection between kafka-explorer
and the Kafka broker:
* kafka.server.keystore.jks: The server's keystore in jks format
* kafka.server.truststore.jks: The server's truststore in jks format
* kafka.client.keystore.jks: The client's keystore in jks format
* kafka.client.truststore.jks: The client's truststore in jks format
* key.pem: Client's private key
* certificate.pem: Client's signed certificate
* CARoot.pem: The CARoot certificate

With all these files, we can run kafka-explorer as follows:
```shell
docker run -d -m 256m --log-driver json-file --log-opt max-size="1m" \
  -p 5000:5000 \
  -v <local directory containing client certificate, client key and CARoot>:/certs/kafka \
  -e "LOG_LEVEL=DEBUG" \
  -e "KAFKA_BOOTSTRAP_BROKERS=<list of bootstrap brokers>" \
  -e "SECURITY_PROTOCOL=SSL" \
  -e "SSL_CHECK_HOSTNAME=false" \
  -e "SSL_CIPHERS=ALL" \
  -e "SSL_CAFILE=/certs/kafka/CARoot.pem" \
  -e "SSL_CERTFILE=/certs/kafka/certificate.pem" \
  -e "SSL_KEYFILE=/certs/kafka/key.pem" \
  --name kafka-explorer kafka-explorer:local-tls-build
```

