# import os


# class Config(object):
#     # Flask base configuration
#     SECRET_KEY = os.environ.get('SECRET_KEY')

#     DB_HOST = os.environ.get('DB_HOST')
#     DB_PORT = os.environ.get('DB_PORT')
#     DB_USER = os.environ.get('DB_USER')
#     DB_PASS = os.environ.get('DB_PASS')
#     DB_NAME = os.environ.get('DB_NAME')
#     FRAME_NUM_SKIP=  os.environ.get('FRAME_NUM_SKIP', 4)
#     DETECTOR_SKIP_FRAME = os.environ.get('DETECTOR_SKIP_FRAME', 2)
#     CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379')
#     CMS_BACKEND_CACHE = os.environ.get('CMS_BACKEND_CACHE', 'redis://redis:6379/1')

#     RABBITMQ_BROKER_URL = os.environ.get('RABBITMQ_BROKER_URL', 'amqp://guest:guest@rabbitmq:5672/')

#     # Images storage
#     FILE_STORAGE_PATH = os.environ.get('FILE_STORAGE_PATH', '/tmp/images')
#     CMS_STORAGE_BUCKET_NAME = os.environ.get('CMS_STORAGE_BUCKET_NAME', 'analytic')
#     CMS_STORAGE_HOSTNAME = os.environ.get('CMS_STORAGE_HOSTNAME')
#     CMS_STORAGE_ACCESS_KEY = os.environ.get('CMS_STORAGE_ACCESS_KEY')
#     CMS_STORAGE_SECRET_KEY = os.environ.get('CMS_STORAGE_SECRET_KEY')
#     DETECTOR_URL = os.environ.get('DETECTOR_URL')
#     DETECTOR_INPUT_SIZE = os.environ.get('DETECTOR_INPUT_SIZE', '416,416')
#     LPR_DETECTOR_URL = os.environ.get('LPR_DETECTOR_URL')
#     LPR_DETECTOR_INPUT_SIZE = os.environ.get('LPR_DETECTOR_INPUT_SIZE', '416,416')
#     LPR_EXTRACTOR_URL = os.environ.get('LPR_EXTRACTOR_URL')
#     LPR_EXTRACTOR_INPUT_SIZE = os.environ.get('LPR_EXTRACTOR_INPUT_SIZE', '80,60')
#     VP_CELERY_BROKER_URL = os.environ.get('VP_CELERY_BROKER_URL')
#     VP_DOCKER_IMAGE = os.environ.get('VP_DOCKER_IMAGE')

#     FACE_DETECTOR_LETTERBOX_ENABLE = os.environ.get('LPR_DETECTOR_LETTERBOX_ENABLE', False)
#     LPR_DETECTOR_INPUT_SIZE = s.environ.get(tuple(env.list('LPR_DETECTOR_INPUT_SIZE', subcast=int))


from __future__ import division, absolute_import, print_function, unicode_literals
import logging
import six
from environs import Env

from utils.module_loading import import_string

env = Env()
env.read_env()  # read .env file, if it exists

default_settings = {
    # Stream variables
    'INPUT_STREAM_URL': env('INPUT_STREAM_URL', 0),  # Allow file path and url (rtsp, rtmp)
    'INPUT_STREAM_ID': env('INPUT_STREAM_ID', 1),  # UUID of stream file or camera
    'FRAME_NUM_SKIP':  env('FRAME_NUM_SKIP', 1),
    'TRACK_NUM_SKIP':  env('TRACK_NUM_SKIP', 3),
    # Models variables
    'CONFIG_MODEL_YOLO': env('CONFIG_MODEL_YOLO', 'models/config/head.cfg'),
    'DATA_MODEL_YOLO': env('DATA_MODEL_YOLO', 'models/config/head.data'),
    'WEIGHTS_MODEL_YOLO': env('WEIGHTS_MODEL_YOLO', 'models/weights/head_final.weights'),
    # Server Detect
    'DETECTOR_SERVER': env('DETECTOR_SERVER', 'http://192.168.101.240:5006/detect'),
    # Detector variables
    'THRESH_DISTANCE' : env.int('THRESH_DISTANCE', 120)
    "THRESH_PEOPLE": env.int('THRESH_PEOPLE', 5)
    "MAX_AGE": env.int('MAX_AGE', 1)

    'THRESH_FACE_DETECTOR': env('THRESH_FACE_DETECTOR', 0.5),
    'HIER_THRESH_FACE_DETECTOR': env('HIER_THRESH_FACE_DETECTOR', 0.5),
    'NMS_FACE_DETECTOR': env('NMS_FACE_DETECTOR', 0.4),
    # Haar Cascade
    'HAAR_URL': env('HAAR_URL', 'models/haar/haar_frontalface.xml'),
    #
    'DETECTOR_URL': env('DETECTOR_URL', None),
    # 'DETECTOR_INPUT_SIZE': tuple(env.list('DETECTOR_INPUT_SIZE', subcast=int)),
    'DETECTOR_INPUT_SIZE': (416, 416),
    'DETECTOR_LETTERBOX_ENABLE': env.bool('DETECTOR_LETTERBOX_ENABLE', False),
    'TRACKING_STORE_FRAME_COUNTER': env.int('TRACKING_STORE_FRAME_COUNTER', 6),
    'DETECTOR_MIN_SIZE': env.int('DETECTOR_MIN_SIZE', 100),
    'DISTANCE_TRACKING_OBJECT': env.int('DISTANCE_TRACKING_OBJECT',25),
    # Server Embedding
    'EMBEDDING_SERVER': env('EMBEDDING_SERVER', 'http://192.168.101.240:5005/embedding'),
    'NUM_TRACK_REMOVE': env('NUM_TRACK_REMOVE', 2),
    'NUM_TRACK_RECOGNIZE': env('NUM_TRACK_RECOGNIZE', 200),
    'DISTANCE_UNKNOWN': env('DISTANCE_UNKNOWN', 1),
    # App configuration variables
    # 'LOG_LEVEL': env.log_level('LOG_LEVEL', logging.DEBUG),
    'SHOW_IMAGE_ENABLE': env.bool('SHOW_IMAGE_ENABLE', False),

    # Concurent configuration for video processor
    'VP_READ_FRAME_QUEUE_SIZE': env.int('VP_READ_FRAME_QUEUE_SIZE', 128),
    'VP_STORE_FRAME_MAX_WORKERS': env.int('VP_STORE_FRAME_MAX_WORKERS', 15),
    'VP_NO_FRAMES_TIMEOUT_SECONDS': env.int('VP_NO_FRAMES_TIMEOUT_SECONDS', 300),
    'VP_STORAGE_BUCKET_NAME': env('VP_STORAGE_BUCKET_NAME', 'analytic'),
    'VP_STORAGE_HOSTNAME': env('VP_STORAGE_HOSTNAME', None),
    'VP_STORAGE_ACCESS_KEY': env('VP_STORAGE_ACCESS_KEY', "minio"),
    'VP_STORAGE_SECRET_KEY': env('VP_STORAGE_SECRET_KEY', "minio123"),


    # Extension variables
    'FILE_STORAGE': 'vp.services.storages.FileStorage',
    'FILE_STORAGE_PATH_IMAGES': env.str('FILE_STORAGE_PATH_IMAGES', './app/data/images'),
    'FILE_STORAGE_PATH_MODELS': env.str('FILE_STORAGE_PATH_MODELS', './app/data/models'),
    # 'CELERY_BROKER_URL': env('CELERY_BROKER_URL'),
    # 'RABBITMQ_BROKER_URL': env('RABBITMQ_BROKER_URL'),
    'RABBITMQ_BROKER_URL': env('RABBITMQ_BROKER_URL', 'amqp://guest:guest@192.168.101.240:5672/'),
    'CELERY_BROKER_URL':  env('CELERY_BROKER_URL', 'redis://192.168.101.240:6379'),
    'STREAM_REDIS': env('STREAM_REDIS', 'redis://192.168.101.240:6379'),
    'OBJECTS_PRODUCER': 'vp.services.producers.CeleryProducer',
    'OBJECTS_NOTIFIER': 'vp.services.notifiers.RabbitMQObjectNotifier',
    'OBJECTS_DETECTOR': 'vp.libs.YoloObjectDetector',
    'LPR_EXTRACTOR': 'vp.libs.LPRExtractor'
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
