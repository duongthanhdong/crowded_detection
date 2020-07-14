import io
import os
import time_uuid
import cv2

from minio import Minio
from minio.error import ResponseError
import pickle
from PIL import Image
import numpy as np 
import logging

class FileStorage():

    def __init__(self, app=None, *args, **kwargs):
        if app:
            self.__fs_path = app.config['FILE_STORAGE_PATH']
            self.__app = app

    def init_app(self, app, *args, **kwargs):
        self.__fs_path = app.config['FILE_STORAGE_PATH']
        self.__app = app

    def __get_images_path_v1(self, uuid):
        directories = uuid.split('-')[::-1]
        return os.path.join(self.__fs_path, *directories[:-1], ''.join(directories[-1][:3]))

    def __get_images_path(self, uuid):
        t_uuid = time_uuid.TimeUUID(uuid)
        iso_date = t_uuid.get_datetime().date().isoformat()

        directories = uuid.split('-')[::-1]
        return os.path.join(self.__fs_path, iso_date, *directories[:-1])


class MinioStorage():

    def __init__(self, app=None, *args, **kwargs):
        if app:
            self.init_app(app, args, kwargs)

    def init_app(self, app, *args, **kwargs):
        self.__bucket_model_name = app.config['FACE_STORAGE_BUCKET_MODEL_NAME']
        self.__bucket_image_name = app.config['FACE_STORAGE_BUCKET_IMAGE_NAME']
        self.__bucket_avatar_name = app.config[
            'FACE_STORAGE_BUCKET_AVATAR_NAME']
        hostname = app.config['FACE_STORAGE_HOSTNAME']
        access_key = app.config['FACE_STORAGE_ACCESS_KEY']
        secret_key = app.config['FACE_STORAGE_SECRET_KEY']

        self.__minio_client = Minio(
            str(hostname),
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )
        self.person_path = 'person_models'
        self.label_path = 'label_models'
        self.camera_path = 'camera_models'

    def get(self, uuid):
        stored_path = self.__get_images_path(uuid)

        buf = self.__minio_client.get_object(
            bucket_name=self.__bucket_image_name,
            object_name=os.path.join(stored_path, f'{uuid}.jpg')
        )
        return Image.open(io.BytesIO(buf.read()))

    def get_avatar(self, uuid):
        stored_path = uuid
        buf = self.__minio_client.get_object(
            bucket_name=self.__bucket_avatar_name,
            object_name=os.path.join(stored_path, f'{uuid}.jpg')
        )
        return Image.open(io.BytesIO(buf.read()))

    def put_avatar(self, image, person_id):
        try:
            ret, buf = cv2.imencode('.jpg', image)
            buf = buf.tobytes()
            data = io.BytesIO(buf)
            length = data.getbuffer().nbytes
            self.__minio_client.put_object(
                bucket_name=self.__bucket_avatar_name,
                object_name=os.path.join(person_id, f'{person_id}.jpg'),
                data=data,
                length=length
            )
        except ResponseError as err:
            print(err)


    def get_image_training(self, person_id, image_id):
        buf = self.__minio_client.get_object(
            bucket_name=self.__bucket_avatar_name,
            object_name=os.path.join(person_id, f'{image_id}.jpg')
        )
        return Image.open(io.BytesIO(buf.read()))

    def put_image_training(self, image, person_id, image_id):
        try:
            ret, buf = cv2.imencode('.jpg', image)
            buf = buf.tobytes()
            data = io.BytesIO(buf)
            length = data.getbuffer().nbytes
            self.__minio_client.put_object(
                bucket_name=self.__bucket_avatar_name,
                object_name=os.path.join(person_id, f'{image_id}.jpg'),
                data=data,
                length=length
            )
        except ResponseError as err:
            print(err)

    def __get_images_path(self, uuid):
        t_uuid = time_uuid.TimeUUID(uuid)
        iso_date = t_uuid.get_datetime().date().isoformat()

        directories = uuid.split('-')[::-1]
        directories.pop(1)
        return os.path.join(directories[0], iso_date, *directories[:-1])

    def get_models(self, uuid_object, type=None, uuid_image=None):
        object_name = None
        if type == 'person':
            object_name = os.path.join(self.person_path, uuid_object, f'{uuid_image}.pkl')
        elif type == 'label':
            object_name = os.path.join(self.label_path, f'{uuid_object}.pkl')
        elif type == 'camera':
            object_name = os.path.join(self.camera_path, f'{uuid_object}.pkl')
        buf = self.__minio_client.get_object(
            bucket_name=self.__bucket_model_name,
            object_name=object_name
        )
        return pickle.load(buf)

    def put_models(self, uuid_object, bytes_file, type=None, uuid_image=None):
        object_name = None
        if type == 'person':
            object_name = os.path.join(self.person_path, uuid_object, f'{uuid_image}.pkl')
        elif type == 'label':
            object_name = os.path.join(self.label_path, f'{uuid_object}.pkl')
        elif type == 'camera':
            object_name = os.path.join(self.camera_path, f'{uuid_object}.pkl')
        try:
            self.__minio_client.put_object(
                bucket_name=self.__bucket_model_name,
                object_name=object_name,
                data=io.BytesIO(bytes_file),
                length=len(bytes_file)
            )
        except ResponseError as err:
            print(err)