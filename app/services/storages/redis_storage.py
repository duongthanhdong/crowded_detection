
import cv2
import numpy as np

import redis


class RedisStorage():
    REDIS_STORAGE_PREFIX = 'REDIS_STORAGE'

    def __init__(self, *args, **kwargs):
        self.__redis_storage_url = kwargs['settings'].CELERY_BROKER_URL
        self.__key_expire_duration = kwargs['settings'].VP_STORAGE_REDIS_EXPIRE_DURATION
        self.__redis_client = redis.from_url(self.__redis_storage_url)

    def get(self, uuid):
        obj_key = f'{RedisStorage.REDIS_STORAGE_PREFIX}_{uuid}'
        buf = self.__redis_client.get(obj_key)
        return buf

    def put(self, uuid, content):
        obj_key = f'{RedisStorage.REDIS_STORAGE_PREFIX}_{uuid}'
        buf = content.tobytes()
        self.__redis_client.set(obj_key, buf, ex=self.__key_expire_duration)
