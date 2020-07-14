from common.tracking.usage_group import Usage_Group
from services.grpc.client_gRPC import Client_gRPC
from services.storages.redis_storage import RedisStorage
from common.tracking.tracking_time_distance import Tracking
from common.detector.detect_security import DetectSecurity


from tasks import celery_recognize
from instance.config import settings

import cv2
import logging
import time
import uuid
import argparse
import json
import numpy as np

def iou(bb_test, bb_gt):
    """
    Computes IUO between two bboxes in the form [x1,y1,x2,y2]
    """
    xx1 = np.maximum(bb_test[0], bb_gt[0])
    yy1 = np.maximum(bb_test[1], bb_gt[1])
    xx2 = np.minimum(bb_test[2], bb_gt[2])
    yy2 = np.minimum(bb_test[3], bb_gt[3])
    w = np.maximum(0., xx2 - xx1)
    h = np.maximum(0., yy2 - yy1)
    wh = w * h
    o = wh / ((bb_test[2] - bb_test[0]) * (bb_test[3] - bb_test[1])
              + (bb_gt[2] - bb_gt[0]) * (bb_gt[3] - bb_gt[1]) - wh)
    return(o)


class StreamProcessor():
    """docstring for StreamProcessor"""

    def __init__(self, *args, **kwargs):
        self.count_skip = 0
        self.thresh_distance = settings.THRESH_DISTANCE
        self.thresh_people = settings.THRESH_PEOPLE
        self.redis_store = RedisStorage(settings=settings)
        self.usage_group = Usage_Group(self.thresh_distance, self.thresh_people,settings.MAX_AGE)
        # self.vid = cv2.VideoCapture(settings.INPUT_VIDEO_PATH)
        self.vid = cv2.VideoCapture(settings.INPUT_STREAM_URL)
        logging.warning(settings.URL_SERVER_SERVING)
        self.client_gRPC = Client_gRPC(settings.URL_SERVER_SERVING)
        self.detect_security = DetectSecurity()

    def __cache_store_frame(self, frame_uuid, frame):
        # logging.warning("Save redis frame: uuid {}".format(frame_uuid))
        ret, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
        self.redis_store.put(frame_uuid, buf)
        logging.warning('Save redis frame: uuid {}'.format(frame_uuid))

    def __drawing_group(self, frame, groups):
        height_ori, width_ori = frame.shape[:2]
        for obj in groups:
            x = int(obj[0] * width_ori)
            y = int(obj[1] * height_ori)
            w = int(obj[2] * width_ori)
            h = int(obj[3] * height_ori)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (100, 100, 200), 2)

    def __drawing_frame(self, frame, objs):
        height_ori, width_ori = frame.shape[:2]
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 0, 255), (128, 0, 0),
                  (0, 128, 0), (0, 0, 128), (128, 0, 128), (128, 128, 0), (0, 128, 128)]
        if objs != None:
            for obj in objs:
                name = obj['name']
                class_id = obj['class_id']
                prob = obj['prob']
                x = int(obj['bbox'][0] * width_ori)
                y = int(obj['bbox'][1] * height_ori)
                w = int(obj['bbox'][2] * width_ori)
                h = int(obj['bbox'][3] * height_ori)
                cv2.rectangle(frame, (x, y), (x + w, y + h), colors[class_id], 2)

                str_display = str(name) + "||" + str(round(prob, 2)) + "||" + str(class_id)
                y_backgroud_classes = y - 35 if y > 30 else y + 35
                y_classes = y - 10 if y > 30 else y_backgroud_classes - 10
                # cv2.rectangle(frame, (x, y_backgroud_classes), (x + len(str_display) * 19 + 10, y), (200,255,255), -1)
                cv2.putText(frame, str(round(prob, 2)), (x + 5, y_classes),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, colors[class_id], 3)



    def process_video(self):
        stream_id = settings.INPUT_STREAM_ID or str(uuid.uuid4())
        frames = 0
        logging.warning("Start Process")
        settings.FRAME_NUM_SKIP = 5
        while True:
            ret, frame = self.vid.read()
            # print(frame)
            frames += 1
            if not ret:
                break
            height, width = frame.shape[:2]
            list_info_group = []
            list_bbox_group = []
            self.manage_group = {}
            frame_id = str(uuid.uuid1())
            frame_time = time.time()
            image = cv2.resize(frame,(608,608))
            if frames % int(settings.FRAME_NUM_SKIP) == 0:
                detection = self.client_gRPC.send_request(image)
                # detection = [{'name': b'Head', 'class_id': 0, 'prob': 0.9533659219741821, 'bbox': [0.6801567422716241, -0.00302704384452418, 0.06715617054387142, 0.13841043020549573]}, {'name': b'Head', 'class_id': 0, 'prob': 0.948371171951294, 'bbox': [0.53049446720826, 0.02337013420305753, 0.060813646567495244, 0.14011718097485995]}, {'name': b'Head', 'class_id': 0, 'prob': 0.9092724919319153, 'bbox': [0.46862765362388215, 0.02699067090686999, 0.07163143157958984, 0.18226893324601023]}, {'name': b'Head', 'class_id': 0, 'prob': 0.8712153434753418, 'bbox': [0.27979607958542674, 0.1359079637025532, 0.08180948307639674, 0.22157862311915347]}, {'name': b'Head', 'class_id': 0, 'prob': 0.8295581936836243, 'bbox': [0.5855531190571032, 0.6710843287016216, 0.18545692845394737, 0.30253415358693975]}, {'name': b'Head', 'class_id': 0, 'prob': 0.7694066166877747, 'bbox': [0.9605313931640826, -0.008123837019267832, 0.04034050828532169, 0.1526144178290116]}, {'name': b'Head', 'class_id': 0, 'prob': 0.7527122497558594, 'bbox': [0.5616450184269955, 0.6153915681337055, 0.22911591278879265, 0.4107423330608167]}, {'name': b'Head', 'class_id': 0, 'prob': 0.7124632000923157, 'bbox': [0.16087324995743602, 0.29108748937907974, 0.10831388674284283, 0.2383875846862793]}]
                detection = json.loads(detection)
                # logging.warning(detection)
                # image = np.copy(frame)
                if detection:
                    self.__drawing_frame(frame,detection)
                    self.__cache_store_frame(frame_id, frame)
                    crowded = settings.CROWDED_STATUS
                    security = settings.ALERT_STATUS
                    #save image into redis with key is frame_id
                    #vp-security] [{"class_id":1,"id":'123','frame_id':123aidf,"time":argbuef,'name':dong,"prob":0.495,"bbox":[1,3,4,5]},...]
                    # logging.warning("{} {}".format(type(crowded),security))
                    object_type = "None"
                    if security:
                        object_type = "security"
                        celery_recognize.delay(detection,stream_id, frame_id, frame_time, object_type)
                        # tracking = Tracking()
                        # a=tracking.process(detection,object_type)
                        # print(a)
                    if crowded:
                        object_type = "crowded"
                        result = self.usage_group.process(detection, width, height)
                        notification = result['violate']
                        if not notification:
                            continue
                        json_tensor = result['list_info_group']
                        logging.warning(result)
                        celery_recognize.delay(json_tensor,stream_id, frame_id, frame_time, object_type)
                    logging.warning(object_type)
                    # logging.warning(settings.INPUT_STREAM_URL)
                    # logging.warning(stream_id)
                    # logging.warning(detection)

                # end = time.time()
                # fps = 1 / (end - frame_time)
                # cv2.putText(frame, str(fps), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                # cv2.imshow('output1', cv2.resize(frame, (1080, 640)))
                # if cv2.waitKey(1) == ord('q'):
                #     break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='add enviroment')
    # parser.add_argument('--video_path', default='./video/video3.mp4',
    #                     help='path to your input video (defaulte is "VMS.mp4")')
    parser.add_argument('--video_path', default='./video/Video_test.mp4',
                        help='path to your input video (defaulte is "VMS.mp4")')
    args = parser.parse_args()

    settings.INPUT_VIDEO_PATH = args.video_path
    print('[RUN] Streming')
    sp = StreamProcessor()
    sp.process_video()
