from services.notifiers.objects import RabbitMQObjectNotifier
from services.storages.fs_storage import FileStorage
from services.storages.redis_storage import RedisStorage

from instance.config import settings
from common.rule.rule_helper import ZoneHelper, TimeHelper
from common.tracking.tracking_time_distance import Tracking

import celery
import logging
import json
import redis
import requests

def dump_json(objs, stream_id, frame_id, frame_time, object_type):
    """
    Function to add info(stream_id,frame_id,time) into objs
    :param objs: objs
    :param stream_id: pass
    :param frame_id: pass
    :param frame_time: pass
    :return: Json object
    """
    json_result = {}
    json_result['stream_id'] = stream_id
    json_result["frame_id"] = frame_id
    json_result["time"] = frame_time
    json_result['object_type'] = object_type
    json_result['objs'] = objs
    return json_result





class Celery_Regconize(celery.Task):
    name = "Celery_Regconize"

    def __init__(self):
        # logging.warning("Initial RabbitMQ")
        self.__notifier = RabbitMQObjectNotifier(settings=settings)
        self.__file_store = FileStorage(settings=settings)
        self.store = redis.Redis.from_url(settings.CELERY_BROKER_URL)
        self.redis_store = RedisStorage(settings=settings)
        self.tracking = Tracking()
        # logging.warning("Successful RabbitMQ")

    def run(self, json_tensor,stream_id, frame_id, frame_time, object_type):
        save_image = False
        logging.warning(json_tensor)
        #process rule with security
        if object_type=='security':
            # print(json_tensor)
            objs_result, rule_id = self.__match_rule(stream_id, frame_time, json_tensor)
            objs = self.tracking.process(objs_result,object_type)
            if len(objs_result)>0:
                json_send = dump_json(objs,stream_id,frame_id,frame_time,object_type)
                # self.__notifier.send(str(stream_id), json_send)
                save_image = True
            logging.warning(objs_result)
        #process rule with crowded
        if object_type=='crowded':
            # logging.warning(json_tensor)
            objs_result, rule_id = self.__match_rule(stream_id, frame_time, json_tensor,)
            # logging.warning(objs_result)
            if len(objs_result)>0:
                json_send = dump_json(objs_result,stream_id,frame_id,frame_time,object_type)
                # self.__notifier.send(str(stream_id), json_send)
                save_image = True
            logging.warning(objs_result)

        #save image
        if save_image:
            logging.warning("Ssaving the Images")
            buf = self.redis_store.get(frame_id)
            # self.__file_store.put(frame_id,buf)


    def __match_rule(self,stream_id, frame_time, objs):
        objs_results=[]
        rule_id, filters = self._get_rule_redis(stream_id)
        logging.warning("rule_id 78. {}".format(rule_id))
        if rule_id is not None and filters is not None:
            for obj in objs:
                is_match=[]
                for _filter in filters:
                    if _filter["type"] == "zone":
                        zone_result = ZoneHelper.is_match_zone_contition(_filter["condition"], obj)
                        is_match.append(zone_result)
                    elif _filter["type"] == "time":
                        time_result = TimeHelper.is_match_time_condition(_filter["condition"], frame_time)
                        is_match.append(time_result)
                logging.warning("Matches:{}".format(is_match))
                if False not in is_match:
                    objs_results.append(obj)
                    # logging.warning("Object resutls:{}".format(objs_results))
        return objs_results, rule_id

    def _get_rule_redis(self,stream_id):
        key_rule = 'RULE_'+str(stream_id)
        if self.store.exists(key_rule):
            rule = self.store.get(key_rule)
            rule = json.loads(rule)
            logging.warning("Rule_ID_Redis:{}".format(rule["rule_id"]))
            logging.warning("Rule_Filter_Redis:{}".format(rule["filters"]))
            return rule["rule_id"], rule["filters"]
        else:
            rule={}
            rule_id,filters= self.__get_rule_api(stream_id)
            if rule_id is not None and filters is not None:
                rule["rule_id"]=rule_id
                rule["filters"]=filters
                rule=json.dumps(rule)
                self.store.set(key_rule, rule, ex=120)
                logging.warning("Rule_ID_API:".format(rule_id))
                logging.warning("Rule_Filter_API".format(filters))
            return rule_id,filters

    def __get_rule_api(self,stream_id):
        rule_id=None
        filters=None
        api_rule= settings.API_SECURITY_URL + "/api/cms/rules"
        logging.warning("apt-rule :{}".format(api_rule))
        logging.warning(stream_id)
        PARAMS = {'filter': '[{"name":"filters__condition","op":"any","val":"{'+stream_id+'}"}]'}
        # PARAMS = {'filter': '[{"name":"filters__condition","op":"any","val":"{'+stream_id+'}"},{"name":"filters__type","op":"any","val":"zone"}]'}
        r = requests.get(url=api_rule, params=PARAMS)
        # r = requests.get(url=api_rule)
        results = r.json()
        if len(results["data"])>0:
            data = results["data"][0]
            rule_id = data["id"]
            filters = data["attributes"]["filters"]
        return rule_id,filters

    def pre_detected_objects(self, stream_id,frame_id, frame_time, objs):
        result = {}
        result["stream_id"] = stream_id
        result["objs"] = objs
        result["time"] = frame_time
        result['frame_id'] = frame_id
        return result
celery_recognize = Celery_Regconize()
