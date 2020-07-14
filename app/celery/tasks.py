import celery
from services.notifiers.emit_log_topic import RabbitMQ
import logging


class Celery_Regconize(celery.Task):
    name = "Celery_Regconize"

    def __init__(self):
        # logging.warning("Initial RabbitMQ")
        self.__notifier = RabbitMQ()
        # logging.warning("Successful RabbitMQ")

    def run(self, json_tensor):
        print("hello")
        stream_id = json_tensor['stream_id']
        self.__notifier.send(str(stream_id), json_tensor)

celery_recognize = Celery_Regconize()
