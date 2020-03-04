import cv2
import logging
import time
from common.detector.darknet import YoloDetector
from common.tracking.sort_edit import Sort
# from tasks import celery_recognition
from instance.config import settings
from utils.math import bbox_xywh_to_xyxy
import os
import uuid
from services.storages.storage_fs import StorageFile
import argparse
import trafficlight
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np


class StreamProcessor():
    """docstring for StreamProcessor"""

    def __init__(self, *args, **kwargs):
        self.yolo = YoloDetector()
        self.tracker=Sort()
        self.count_skip = 0
        self.tracks = []
        self.vid = cv2.VideoCapture(settings.INPUT_VIDEO_PATH)
        self.storage = StorageFile()

    def __preprocess_objs(self, frame_img, frame_uuid, frame_time, objs):
        height_ori, width_ori = frame_img.shape[:2]
        objs_process = []
        for obj in objs:
            bbox = bbox_xywh_to_xyxy(
                obj['bbox'], width=width_ori, height=height_ori)
            bbox_height = bbox[3] - bbox[1]
            bbox_width = bbox[2] - bbox[0]
            # if bbox_height < settings.DETECTOR_MIN_SIZE or bbox_width < settings.DETECTOR_MIN_SIZE:
                # print("remove")
                # continue
            obj['class_id'] = obj['id'] #because we have one object only
            obj['id'] = str(uuid.uuid4())
            obj['frame_id'] = frame_uuid
            obj['time'] = frame_time
            objs_process.append(obj)
        return objs_process
    def __drawing_group(self,frame,groups):
        height_ori, width_ori = frame.shape[:2]
        for obj in groups:
            x = int(obj[0] * width_ori)
            y = int(obj[1] * height_ori)
            w = int(obj[2] * width_ori)
            h = int(obj[3] * height_ori)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (100,100,200), 2)

    def __drawing_frame(self, frame, objs):
        height_ori, width_ori = frame.shape[:2]
        colors=[(255,0,0),(0,255,0),(0,0,255),(255,0,255),(128,0,0),(0,128,0),(0,0,128),(128,0,128),(128,128,0),(0,128,128)]
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

                str_display = str(name) + "||" + str(round(prob,2)) + "||" +str(class_id)
                y_backgroud_classes = y - 35 if y > 30 else y + 35
                y_classes = y - 10 if y > 30 else y_backgroud_classes - 10
                # cv2.rectangle(frame, (x, y_backgroud_classes), (x + len(str_display) * 19 + 10, y), (200,255,255), -1)
                cv2.putText(frame, str(round(prob,2)), (x + 5, y_classes), cv2.FONT_HERSHEY_SIMPLEX, 1, colors[class_id], 3)

    def dump_json(self,follow,frame_uuid,frame_time,stream_id):
        """
        function to process result of sort object .
        :parameter follow : result of sort object that is array within key objects "tracks"
        :return: json which include  data is processed
        """
        body_track = {}
        track = {}
        list_result = []
        # create Json result for tracker
        for i, follows in enumerate(follow["tracks"]):
            if i == 0:
                body_track["name"] = follows[4]
                body_track["id"] = follows[3]  # ID of the object
                body_track["prob"] = follows[0][4]
                # create Json header for track
                track["name"] = follows[4]
                track['id'] = follows[3]
                track["prob"] = follows[0][4]
                track["frame_id"] = follows[1]
                track["time"] = follows[2]
                track["bbox"] = (follows[0][:4]).tolist()

            body_track["frame_id"] = follows[1]
            body_track["time"] = follows[2]
            body_track["bbox"] = (follows[0][:4]).tolist()
            list_result.append(body_track)
            body_track = {}
            # print((follows))
        track["tracks"] = list_result
        json_send = {
            "stream_id": stream_id,
            "frame_id": frame_uuid,
            "objs": [track],
            "time": frame_time,
        }
        return json_send

    def process_video(self):
        stream_id = settings.INPUT_STREAM_ID or str(uuid.uuid4())
        frames = 0
        i = 1
        light_traffic = 0
        logging.warning("Start Process")
        while True:
            ret, frame = self.vid.read()
            frames += 1
            frame_uuid = str(uuid.uuid1())
            frame_time = time.time()
            if frames % int(settings.FRAME_NUM_SKIP) == 0:
                objs = self.yolo.detect(frame)
                objs = self.__preprocess_objs(
                    frame, frame_uuid, frame_time, objs)
                self.tracks, follow = self.tracker.update(objs, frames, int(settings.TRACK_NUM_SKIP),frame)
                if len(follow) > 0:
                #     face_detected_info = self.dump_json(follow,frame_uuid,frame_time,stream_id)
                #     logging.warning(
                #         "Send detect info")
                    print(follow['group'])
                print(self.tracks)
                if objs:
                    self.__drawing_frame(frame, objs)
                    self.__drawing_group(frame,self.tracks)

            end = time.time()
            fps = 1/(end - frame_time)
            cv2.putText(frame, str(fps), (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 3)
            cv2.imshow('output1', cv2.resize(frame,(1080,640)))
            if cv2.waitKey(1) == ord('q'):
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='add enviroment')
    parser.add_argument('--video_path', default='./video/video3.mp4',
                        help='path to your input video (defaulte is "VMS.mp4")')
    args = parser.parse_args()

    settings.INPUT_VIDEO_PATH = args.video_path
    print('[RUN] Streming')
    sp = StreamProcessor()
    sp.process_video()
