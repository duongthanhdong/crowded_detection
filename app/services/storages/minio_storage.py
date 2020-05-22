
import cv2
import io
import os
import time_uuid
import numpy as np

from minio import Minio
from minio.error import ResponseError

class MinioStorage():
    def __init__(self, *args, **kwargs):
        self.__bucket_name = kwargs['settings'].VP_STORAGE_BUCKET_NAME
        hostname = kwargs['settings'].VP_STORAGE_HOSTNAME
        access_key = kwargs['settings'].VP_STORAGE_ACCESS_KEY
        secret_key = kwargs['settings'].VP_STORAGE_SECRET_KEY

        self.__minio_client = Minio(
            hostname,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )

    def get(self, uuid, cvread=False, gray=True):
        stored_path = self.__get_images_path(uuid)
        filename = os.path.join(stored_path, f'{uuid}.jpg')

        if cvread:
            buf = self.__minio_client.get_object(
                bucket_name=self.__bucket_name,
                object_name=os.path.join(stored_path, f'{uuid}.jpg')
            )
            arr = np.frombuffer(buf.read(), dtype=np.uint8)

            if gray:
                return cv2.imdecode(arr, 0)
            else:
                return cv2.imdecode(arr, -1)
        return filename

    def put(self, uuid, content):
        stored_path = self.__get_images_path(uuid)
        buf = content.tobytes()

        data = io.BytesIO(buf)
        length = data.getbuffer().nbytes

        try:
            self.__minio_client.put_object(
                bucket_name=self.__bucket_name,
                object_name=os.path.join(stored_path, f'{uuid}.jpg'),
                data=data,
                length=length
                # content_type='image/jpg'
            )
        except ResponseError as err:
            print(err)

    def put_ext(self, uuid, content, name, prefix=''):
        t_uuid = time_uuid.TimeUUID(uuid)
        iso_date = t_uuid.get_datetime().date().isoformat()
        hour = str(t_uuid.get_datetime().hour)

        buf = content.tobytes()

        data = io.BytesIO(buf)
        length = data.getbuffer().nbytes

        try:
            self.__minio_client.put_object(
                bucket_name=self.__bucket_name,
                object_name=os.path.join(prefix, iso_date, hour, name),
                data=data,
                length=length
                # content_type='image/jpg'
            )
        except ResponseError as err:
            print(err)

    def __get_images_path(self, uuid):
        t_uuid = time_uuid.TimeUUID(uuid)
        iso_date = t_uuid.get_datetime().date().isoformat()

        directories = uuid.split('-')[::-1]
        return os.path.join(iso_date, *directories[:-1])
