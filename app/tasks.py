import celery
from services.notifiers.emit_log_topic import RabbitMQ

class Celery_Regconize(celery.Task):
	name = "Celery_Regconize"

	def __init__(self):
		self.__notifier = RabbitMQ()
		print("Initial")

	def run(self,json_tensor):
		print("hello")
		stream_id = json_tensor['stream_id']
		self.__notifier.send(str(stream_id),json_tensor)

celery_recognize = Celery_Regconize()