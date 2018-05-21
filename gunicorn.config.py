import multiprocessing as mp
import os

bind = '0.0.0.0:5000'

worker_class = 'gevent'
workers = os.environ.get('WORKERS', min(10, (int(mp.cpu_count()) * 2) + 1))

loglevel = os.environ.get('LOG_LEVEL', 'INFO')
