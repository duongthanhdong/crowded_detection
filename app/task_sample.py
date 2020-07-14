"""
create by: Huynh Long
create date: 01-01-2020
"""
from celery.utils.log import get_task_logger
from instance.config import settings
from services.storages.minio_storage import MinioStorage
import redis
import requests
from services.storages.redis_storage import RedisStorage
from common.rule.rule_helper import ZoneHelper, TimeHelper
from services.notifiers.objects import RabbitMQObjectNotifier
import celery
import cv2
import json
import numpy as np
import os
import logging



class CeleryAlert(celery.Task):
    name = 'CeleryAlert'
    """docstring for CeleryRecognition"""

    def __init__(self):
        self.__notifiers = RabbitMQObjectNotifier(settings=settings)
        self.store = redis.Redis.from_url(settings.CELERY_BROKER_URL)
        self.redis_store = RedisStorage(settings=settings)
        self.__minio_storage = MinioStorage(settings=settings)
    def run(self, detected_info):
        objs = detected_info['objs']
        print(objs)
        objs_result, rule_id = self.__match_rule(detected_info['stream_id'], objs)
        detected_info["rule_id"]=rule_id
        detected_info["objs"]=objs_result
        logging.warning('Detected result: {}'.format(detected_info))
        if len(objs_result) > 0:
            buf = self.redis_store.get(detected_info["objs"][0]["frame_id"])
            self.__minio_storage.put(detected_info["objs"][0]["frame_id"],buf)
            logging.warning("Save Minio: {}".format(detected_info["objs"][0]["frame_id"]))
            self.__notifiers.send(str(detected_info['stream_id']), detected_info)
            
    def __match_rule(self,stream_id,objs):
        objs_results=[]
        rule_id, filters = self._get_rule_redis(stream_id)
        if rule_id is not None and filters is not None:
            for obj in objs:
                is_match=[]
                for _filter in filters:
                    if _filter["type"] == "zone":
                        zone_result = ZoneHelper.is_match_zone_contition(_filter["condition"], obj)
                        is_match.append(zone_result)
                    elif _filter["type"] == "time":
                        time_result = TimeHelper.is_match_time_condition(_filter["condition"], obj["time"])
                        is_match.append(time_result)
                logging.warning("Matches:{}".format(is_match))
                if False not in is_match:
                    objs_results.append(obj)
                    logging.warning("Object resutls:{}".format(objs_results))
        return objs_results, rule_id

    def _get_rule_redis(self,stream_id):
        key_rule = 'RULE_'+str(stream_id)
        #key_rule_filters='RULE_FILTERS_'+str(stream_id)
        if self.store.exists(key_rule):
            rule = self.store.get(key_rule)
            rule = json.loads(rule)
            logging.warning("Rule_ID_Redis:{}".format(rule["rule_id"]))
            logging.warning("Rule_Filter_Redis:{}".format(rule["filters"]))
            return rule["rule_id"], rule["filters"]
        else:
            rule={}
            rule_id = None
            filters = None
            rule_id,filters= self.__get_rule_api(stream_id)
            if rule_id is not None and filters is not None:
                rule["rule_id"]=rule_id
                rule["filters"]=filters
                rule=json.dumps(rule)
                self.store.set(key_rule, rule, ex=60)
                logging.warning("Rule_ID_API:".format(rule_id))
                logging.warning("Rule_Filter_API".format(filters))
            return rule_id,filters

    def __get_rule_api(self,stream_id):
        rule_id=None
        filters=None
        api_rule= settings.API_SECURITY_URL + "/api/cms/rules"
        PARAMS = {'filter': '[{"name":"filters__condition","op":"any","val":"{'+stream_id+'}"},{"name":"filters__type","op":"any","val":"zone"}]'}
        r = requests.get(url=api_rule, params=PARAMS)
        results = r.json()
        if len(results["data"])>0:
            data = results["data"][0]
            rule_id = data["id"]
            filters = data["attributes"]["filters"]
        return rule_id,filters

celery_alert = CeleryAlert()
