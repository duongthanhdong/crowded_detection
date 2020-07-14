#!/usr/bin/env python
import pika
import sys
import json

# connection = pika.BlockingConnection(
#     pika.ConnectionParameters(host='localhost'))
# connection = pika.BlockingConnection(pika.URLParameters("amqp://guest:guest@192.168.1.45:5672"))

# channel = connection.channel()

# channel.exchange_declare(exchange='topic_logs', exchange_type='topic')

# result = channel.queue_declare('', exclusive=True)
# queue_name = result.method.queue

# binding_keys = sys.argv[1:]
# if not binding_keys:
#     sys.stderr.write("Usage: %s [binding_key]...\n" % sys.argv[0])
#     sys.exit(1)

# for binding_key in binding_keys:
#     channel.queue_bind(
#         exchange='topic_logs', queue=queue_name, routing_key=binding_key)

# print(' [*] Waiting for logs. To exit press CTRL+C')


# def callback(ch, method, properties, body):
#     print(" [x] %r:%r" % (method.routing_key, body))


# channel.basic_consume(
#     queue=queue_name, on_message_callback=callback, auto_ack=True)

# channel.start_consuming()


class Receiver:

    def __init__(self, queue_name, exchange, amqp_url):
        self._reconnect_delay = 0
        self.queue_name = queue_name
        self.exchange = exchange
        self.amqp_url = pika.URLParameters(amqp_url)

        # setup rabbitmq consumer
        connection = pika.BlockingConnection(self.amqp_url)
        self._channel = connection.channel()
        self._channel.exchange_declare(exchange=self.exchange, exchange_type='topic')

        result = self._channel.queue_declare('', exclusive=True)
        queue_name = result.method.queue
        self.queue_name = queue_name
        self._channel.queue_declare("", durable=True)  # Add durable = True to make sure it's store to disk
        # At the moment, we route all objects into one queue.
        self._channel.queue_bind(exchange=self.exchange, queue=self.queue_name, routing_key='#')
        self._channel.basic_qos(prefetch_count=1)  # Add prefetch_count = 1 for better load balance
        self._channel.basic_consume(queue=self.queue_name, on_message_callback=self.callback, auto_ack=True)

    def run(self):
        try:
            self._channel.start_consuming()
        except Exception as e:
            print(1)
            # LOGGER.warn("Exception: {}".format(e))
            # LOGGER.warn("Failed to connect to {}".format(self.amqp_url))

    def callback(self, ch, method, properties, body):
        # print(" [x] %r:%r" % (method.routing_key, body))
        decoded_data = None
        if isinstance(body, bytes):
            decoded_data = body.decode('utf-8')

        if isinstance(decoded_data, str):
            try:
                jdata = json.loads(decoded_data)
                print(jdata)
                # print('hjello')
                # LOGGER.info(jdata)
                # Receiver.plan_tasks(jdata)
            except json.JSONDecodeError:
                print(1)
                # LOGGER.warn('Data="{}" is not JSON serializable.'.format(decoded_data))
            # except Exception as e:
                # LOGGER.error(e, exc_info=True)
receiver = Receiver(queue_name="", exchange="topic_logs", amqp_url="amqp://guest:guest@192.168.1.45:5672")
receiver.run()
