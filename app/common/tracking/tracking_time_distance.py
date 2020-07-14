from instance.config import settings

import logging
import redis
import math
import json

class Tracking:
    def __init__(self):
        self.store = redis.Redis.from_url(settings.CELERY_BROKER_URL)
        self.stream_id = settings.INPUT_STREAM_ID
        logging.info("Successfully start tracking!")

    def distance(self, last_element, bbox, img_width = 1920, img_height = 1080):
        """
        Function to check distance of the object with the previous

        :param last_element: bbox[x,y,w,h] with x,y,w,h in the radio form of image size
        :param bbox: bbox[x,y,w,h] with x,y,w,h in the radio form of image size
        :param distance_thresh: bound of distance that object with the previous
        :param img_width: width of image
        :param img_height: height of image
        :return: True : if distance is less than thresh
                 False : the opposite
        """

        x = last_element[0] * img_width
        y = last_element[1] * img_height
        w = last_element[2] * img_width
        h = last_element[3] * img_height
        x1 = bbox[0] * img_width
        y1 = bbox[1] * img_height
        w1 = bbox[2] * img_width
        h1 = bbox[3] * img_height
        x_center = x + w / 2
        y_center = y + h / 2
        x1_center = x1 + w1 / 2
        y1_center = y1 + h1 / 2
        distance = math.floor(math.sqrt(math.pow(x_center - x1_center, 2) + math.pow(y_center - y1_center, 2)))
        logging.warning(distance)
        return distance

    def process(self, objs,object_type):
        previouss_frame_info = self.get_previous_frame_info(object_type)
        key = object_type + self.stream_id
        self.store.set(key,json.dumps(objs),px=settings.TRACKING_EXPIRE_DURATION)
        results=[]
        if previouss_frame_info:
            for obj in objs:
                logging.warning("bat dau")
                check_distance = 99999999
                for pre_obj in previouss_frame_info:
                    distance = self.distance(pre_obj["bbox"],obj['bbox'])
                    check_distance = distance if check_distance > distance else check_distance
                if check_distance > 50:
                    results.append(obj)

                logging.warning("ket thuc")
        else:
            results = objs
        return results

    def get_previous_frame_info(self,object_type):
        objs = []
        key = object_type + self.stream_id
        if self.store.exists(key):
            info = self.store.get(key)
            info = json.loads(info)
            logging.warning("Previous frame info for {}:{}".format(object_type,info))
            return info
        return objs