from minio import Minio
from minio.error import ResponseError
import logging
import time_uuid
import os
import io

class Client_MinIO():
	def __init__(self,bucket_name):
		self.__minioClient = Minio('192.168.1.10:9000',
					access_key = "minioadmin",
					secret_key = "minioadmin",
					secure = False
					)
		self.__bucket_name = bucket_name

	def put_object(self,image,uuid):
		stored_path = self.__get_images_path(uuid)
		try:
			ret, buf = cv2.imencode('.jpg', image)
			buf = buf.tobytes()
			data = io.BytesIO(buf)
			length = data.getbuffer().nbytes
			self.__minioClient.put_object(
				bucket_name=self.__bucket_name,
				object_name=os.path.join(stored_path, f'{uuid}.jpg'),
				data=data,
				length=length
			)
		except ResponseError as err:
			print(err)

	def get_object(self,bucket_name, object_name, request_headers=None):
		try:
			data = self.__minioClient.get_object(bucket_name, object_name)
			with open('my-testfile', 'wb') as file_data:
				for d in data.stream(32 * 1024):
					file_data.write(d)
		except ResponseError as err:
			print(err)

	def make_bucket(self,bucket_name,location='ap-southeast-1'):
		self.__minioClient.make_bucket(bucket_name,location)
		logging.warning(" Created bucket name: \"%s \"",bucket_name)

	def get_list_bucket(self):
		buckets = self.__minioClient.list_buckets()
		for bucket in buckets:
			print(bucket.name, bucket.creation_date)

	def bucket_exists(self,bucket_name):
		check = self.__minioClient.bucket_exists(bucket_name)
		print(check)
		return check

	def remove_bucker(self,bucket_name):
		check = True
		try:
			self.__minioClient.remove_bucket(bucket_name)
		except ResponseError as err:
			check = False
			print(err)
		print(check)
		return check

	def list_object(self,bucket_name,prefix=None, recursive=False):
		objects = self.__minioClient.list_objects(bucket_name, prefix,
										   recursive)
		for obj in objects:
			print(obj.bucket_name, obj.object_name.encode('utf-8'), obj.last_modified,
				  obj.etag, obj.size, obj.content_type)

	def __get_images_path(self, uuid):
		t_uuid = time_uuid.TimeUUID(uuid)
		iso_date = t_uuid.get_datetime().date().isoformat()

		directories = uuid.split('-')[::-1]
		return os.path.join(iso_date, *directories[:-1])


import uuid
import cv2
id = uuid.uuid1()
image = cv2.imread("thanhdong")
print(id)
client = Client_MinIO("thanhdong")
# client.make_bucket("created-pythonapi")
# client.remove_bucker("created-pythonapi")
# client.list_object("thanhdong")
import time
while 1:
	start = time.time()
	id = uuid.uuid1()
	client.put_object(image,str(id))
	end = time.time()
	elapsed = end - start
	fps = 1/elapsed
	print(elapsed,fps)

