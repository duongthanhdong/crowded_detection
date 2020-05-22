"""
create by: Huynh Long
create date: 01-01-2020
"""
import json
import logging
import pika

LOGGER = logging.getLogger(__name__)


class RabbitMQObjectNotifier():

    def __init__(self, *args, **kwargs):
        self.__broker_url = kwargs['settings'].RABBITMQ_BROKER_URL
        self.__rmq_conn = None

    @property
    def rmq_conn(self):
        if not self.__rmq_conn:
            # worker only share rabbitmq connection
            self.__rmq_conn = pika.BlockingConnection(pika.URLParameters(self.__broker_url))

        return self.__rmq_conn

    @rmq_conn.setter
    def rmq_conn(self, value):
        self.__rmq_conn = value

    def send(self, routing_key, message):
        LOGGER.info('Pika send...{} content={}'.format(routing_key, json.dumps(message)))

        try:
            channel = self.rmq_conn.channel()
            # channel.queue_declare(queue='FaceRuleValidation')
            channel.exchange_declare(exchange='face_detected_objects', exchange_type='topic')
            channel.basic_publish(
                exchange='face_detected_objects', routing_key=routing_key, body=json.dumps(message)
                # ,properties=pika.BasicProperties(delivery_mode = 2)
            )
            channel.close()
        except Exception as e:
            self.rmq_conn = None
            LOGGER.error(e, exc_info=True)
