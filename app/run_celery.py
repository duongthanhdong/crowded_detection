from celery import Celery
from tasks import celery_recognize
from instance.config import settings
# app = Celery('tasks', broker="amqp://guest:guest@rabbitmq:5672/")
app = Celery('tasks', broker=settings.CELERY_BROKER_URL)

app.tasks.register(celery_recognize)
