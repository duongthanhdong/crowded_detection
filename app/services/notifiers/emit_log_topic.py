import pika
import sys
import json

class RabbitMQ():
	def __init__(self):
		self.url = pika.URLParameters
		# self.connection = pika.BlockingConnection(pika.URLParameters("amqp://guest:guest@127.0.0.1:5672/"))
		self.connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
		print("khoi tao RabbitMQ")

	def send(self,routing_key,message):
		channel = self.connection.channel()
		print("send")
		channel.exchange_declare("topic_logs",exchange_type='topic')
		channel.basic_publish(exchange="topic_logs",routing_key = routing_key,body =json.dumps(message))
		channel.close()

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

