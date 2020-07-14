from __future__ import division, absolute_import, print_function, unicode_literals
import logging
import six
from environs import Env

from utils.module_loading import import_string

env = Env()
env.read_env()  # read .env file, if it exists

default_settings = {

    # Models variables
    'CONFIG_MODEL_YOLO': env('CONFIG_MODEL_YOLO', 'models/config/head.cfg'),
    'DATA_MODEL_YOLO': env('DATA_MODEL_YOLO', 'models/config/head.data'),
    'WEIGHTS_MODEL_YOLO': env('WEIGHTS_MODEL_YOLO', 'models/weights/head_final.weights'),
    # Server Detect
    'THRESH_DISTANCE': env.int('THRESH_DISTANCE', 120),
    "THRESH_PEOPLE": env.int('THRESH_PEOPLE', 5),
    "VP_STORAGE_REDIS_EXPIRE_DURATION": env.int('VP_STORAGE_REDIS_EXPIRE_DURATION',300),
    "TRACKING_EXPIRE_DURATION": env.int('TRACKING_EXPIRE_DURATION',1000),
    "MAX_AGE": env.int('MAX_AGE', 1),
    #url
    "URL_SERVER_SERVING": env("URL_SERVER_SERVING",'192.168.1.45:30053'),
    "API_SECURITY_URL": env("API_SECURITY_URL",'http://192.168.101.240:30668'),
    'RABBITMQ_BROKER_URL': env('RABBITMQ_BROKER_URL', 'amqp://guest:guest@192.168.1.45:31672/'),
    'CELERY_BROKER_URL':  env('CELERY_BROKER_URL', 'redis://192.168.1.45:31379'),

    "FILE_STORAGE_PATH_IMAGES": env("FILE_STORAGE_PATH_IMAGES", '/app/images'),

    # Stream variables
    'INPUT_STREAM_URL': env('INPUT_STREAM_URL', "rtsp://admin:123456@192.168.1.229:7070/stream1"),  # Allow file path and url (rtsp, rtmp)
    'INPUT_STREAM_ID': env('INPUT_STREAM_ID', 'a0562cee-cce7-4fd5-a433-897c9b17167c'),  # UUID of stream file or camera
    'FRAME_NUM_SKIP':  env('FRAME_NUM_SKIP', 1),
    'TRACK_NUM_SKIP':  env('TRACK_NUM_SKIP', 5),
    'CROWDED_STATUS': env.bool('CROWDED_STATUS',False),
    'ALERT_STATUS': env.bool('ALERT_STATUS', True)
}

SETTINGS_TO_IMPORT = ['FILE_STORAGE', 'OBJECTS_PRODUCER', 'OBJECTS_NOTIFIER', 'OBJECTS_DETECTOR', 'LPR_EXTRACTOR']


class Settings():

    def __init__(self, default_settings):
        self.__load_default_settings(default_settings)

    def __load_default_settings(self, default_settings):
        for setting_name, setting_value in six.iteritems(default_settings):
            setattr(self, setting_name, setting_value)

    def __getattribute__(self, attr):
        if attr in SETTINGS_TO_IMPORT:
            return import_string(self.__dict__[attr])
        else:
            return super(Settings, self).__getattribute__(attr)

settings = Settings(default_settings)
