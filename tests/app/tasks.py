# http://docs.celeryproject.org/en/latest/getting-started/first-steps-with-celery.html#application
from celery import Celery
import time
import os
import logging


logger = logging.getLogger(__name__)


app = Celery('tasks', broker='redis://localhost')

@app.task
def very_long_task(filename):
    logger.info('start task for file %s, wait a minute' % filename)
    time.sleep(60)
    filepath = os.path.join('/tmp', filename)
    with open(filepath, 'w+') as f:
        f.write('foobar')

    logger.info('created file %s' % filepath)
    return 'file created %s' % filepath
