import pika
import sys
import json
import logging
# from instance.config import settings
# from instance.config import settings


class RabbitMQ():

    def __init__(self):
        logging.warning("khoi tao RabbitMQ")
        # self.url = pika.URLParameters
        # logging.warning(settings.RABBITMQ_BROKER_URL)
        # self.connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_BROKER_URL))
        self.connection = pika.BlockingConnection(pika.URLParameters("amqp://guest:guest@192.168.1.45:5672"))
        # self.connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
        logging.warning("Successfully RabbitMQ")

    def send(self, routing_key, message):
        channel = self.connection.channel()
        print("send")
        print(message)
        channel.exchange_declare("topic_logs", exchange_type='topic')
        channel.basic_publish(exchange="topic_logs", routing_key=routing_key, body=json.dumps(message))
        print("send Successfully")
        channel.close()

rabbit = RabbitMQ()
a = {
    'a': 123
}
rabbit.send('1', a)

# connection = pika.BlockingConnection(
#     pika.ConnectionParameters(host='localhost'))
# channel = connection.channel()

# channel.exchange_declare(exchange='topic_logs', exchange_type='topic')

# routing_key = sys.argv[1] if len(sys.argv) > 2 else 'anonymous.info'
# message = ' '.join(sys.argv[2:]) or 'Hello World!'
# channel.basic_publish(
#     exchange='topic_logs', routing_key=routing_key, body=message)
# print(" [x] Sent %r:%r" % (routing_key, message))
# connection.close()
