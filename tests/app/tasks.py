# http://docs.celeryproject.org/en/latest/getting-started/first-steps-with-celery.html#application
from celery import Celery

app = Celery('tasks', broker='redis://localhost')

@app.task
def add(x, y):
    return x + y
