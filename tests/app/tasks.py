# http://docs.celeryproject.org/en/latest/getting-started/first-steps-with-celery.html#application
from celery import Celery
import time
import os


app = Celery('tasks', broker='redis://localhost')

@app.task
def very_long_task(filename):
    time.sleep(60)
    filepath = os.path.join('/tmp', filename)
    with open(filepath, 'w+') as f:
        f.write('foobar')

    return 'file created %s' % filepath
