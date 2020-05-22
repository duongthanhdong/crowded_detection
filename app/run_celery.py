from celery import Celery

from tasks import celery_recognize

app = Celery('tasks', broker="amqp://guest:guest@127.0.0.1:5672/")

app.tasks.register(celery_recognize)
