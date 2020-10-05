import os
import re
import logging
import multiprocessing as mp

bind = '0.0.0.0:5000'

worker_class = 'gevent'
workers = os.environ.get('WORKERS', min(10, (int(mp.cpu_count()) * 2) + 1))

# Logging

# Read log config environment variables
version = os.environ.get('VERSION')
artifact_id = os.environ.get('MARATHON_APP_DOCKER_IMAGE', f'qvantel/kafka-explorer:{version}?')
service_name = os.environ.get('SERVICE_5000_NAME', os.environ.get('SERVICE_NAME', 'kafka-explorer'))
# Set log formats
log_fmt = re.sub(
    r'\s+',
    '',
    f"""
    {{
        "@timestamp": "%(asctime)s",
        "@version": "1",
        "log_type": "LOG",
        "log_level": "%(levelname)s",
        "level_value": %(levelno)s000,
        "service_name": "{service_name}",
        "logger_name": "%(name)s",
        "artifact_id": "{artifact_id}",
        "thread_name": "%(process)d",
        "message": "%(message)s"
    }}
    """.rstrip()
)
access_fmt = re.sub(
    r'\s+',
    '',
    f"""
    {{
        "@timestamp": "%(asctime)s",
        "@version": "1",
        "log_type": "LOG",
        "log_level": "TRACE",
        "level_value": 5000,
        "service_name": "{service_name}",
        "logger_name": "%(name)s",
        "artifact_id": "{artifact_id}",
        "thread_name": "%(process)d",
        "message": "%(message)s"
    }}
    """.rstrip()
)
access_log_format = "%(h)s %(l)s %(u)s '%(r)s' %(s)s %(b)s '%(f)s' '%(a)s'"
date_fmt = '%Y-%m-%dT%H:%M:%S.000%z'

loggers = {}
# Set level (pseudo supporting the TRACE level)
if (log_level := os.environ.get('LOG_LEVEL', 'INFO')) == 'TRACE':
    # Enable and configure access logging on stdout
    disable_redirect_access_to_syslog = True
    loggers.update({
        "gunicorn.access": {
            "level": 'DEBUG',
            "handlers": ["access_console"],
            "propagate": 0,
            "qualname": "gunicorn.access"
        }
    })
    # Set level to the closest supported value
    log_level = 'DEBUG'

loggers.update({
    'app': {
        'level': log_level,
        'handlers': [],
        'propagate': True,
        'qualname': 'app'
    },
    'gunicorn.error': {
        'level': os.environ.get('GUNICORN_LOG_LEVEL', 'INFO'),
        'handlers': [],
        'propagate': True,
        'qualname': 'gunicorn.error'
    },
    'kafka': {
        'level': os.environ.get('KAFKA_LOG_LEVEL', 'ERROR'),
        'handlers': [],
        'propagate': True,
        'qualname': 'kafka'
    }
})


class JsonEscape(logging.Filter):
    """
    Python logging filter created for making sure that we have no double quotes or line breaks in the message field of
    our log records (this would result in syntactically invalid json objects)
    """
    def filter(self, record: logging.LogRecord):
        record.msg = record.msg.replace('"', '\\"').replace('\n', '\\n')
        return True


logconfig_dict = {
    'root': {'level': log_level, 'handlers': ['console']},
    'loggers': loggers,
    'filters': {
        'json_escape': {
            '()': JsonEscape
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'generic',
            'filters': ['json_escape'],
            'stream': 'ext://sys.stdout'
        },
        'access_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'access',
            'filters': ['json_escape'],
            'stream': 'ext://sys.stdout'
        }
    },
    'formatters': {
        'generic': {
            'format': log_fmt,
            'datefmt': date_fmt,
            'class': 'logging.Formatter'
        },
        'access': {
            'format': access_fmt,
            'datefmt': date_fmt,
            'class': 'logging.Formatter'
        }
    }
}
