import cv2
import logging
import time
from crowed_detection.common.detector.darknet import YoloDetector
from crowed_detection.common.tracking.sort_edit import Sort
from crowed_detection.common.tracking.usage_group import Usage_Group
# from crowed_detection.common.tracking.group import Group_Object


# from tasks import celery_recognition
from crowed_detection.instance.config import settings
# from crowed_detection.utils.math import bbox_xywh_to_xyxy
# import os
import uuid
from crowed_detection.services.storages.storage_fs import StorageFile
from crowed_detection.utils.math import bbox_xywh_to_xyxy


import argparse

# import trafficlight
# import matplotlib.pyplot as plt
# from PIL import Image
import numpy as np

def iou(bb_test,bb_gt):
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
  o = wh / ((bb_test[2]-bb_test[0])*(bb_test[3]-bb_test[1])
    + (bb_gt[2]-bb_gt[0])*(bb_gt[3]-bb_gt[1]) - wh)
  return(o)

class StreamProcessor():
    """docstring for StreamProcessor"""

    def __init__(self, *args, **kwargs):
        self.yolo = YoloDetector()
        self.tracker=Sort()
        self.count_skip = 0
        self.thresh_distance = 500
        self.thresh_people = 2
        self.usage_group = Usage_Group(self.thresh_distance, self.thresh_people)
        self.vid = cv2.VideoCapture(settings.INPUT_VIDEO_PATH)
        # self.vid = cv2.VideoCapture(0)
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

    def process_video(self):
        frames = 0
        logging.warning("Start Process")
        while True:
            ret, frame = self.vid.read()
            frames += 1
            if not ret:
                break
            height, width = frame.shape[:2]
            list_info_group = []
            list_bbox_group = []

            self.manage_group = {}
            frame_uuid = str(uuid.uuid1())
            frame_time = time.time()
            if frames % int(settings.FRAME_NUM_SKIP) == 0:
                objs = self.yolo.detect(frame)
                objs = self.__preprocess_objs(
                    frame, frame_uuid, frame_time, objs)
                print(objs)
                result = self.usage_group.process(objs,width,height)

                notification = result['violate']
                list_info_group = result['list_info_group']
                if notification:
                    print("Notification")
                # list_info_group = self.usage_group.get_list_info_group()
                # self.usage_group.clear_group()
                # print(list_info_group)
                for info in list_info_group:
                    print(info["number_member"],info["bbox"])
                    list_bbox_group.append(info["bbox"][0:4])
                # print("\n")
                # print(list_bbox_group)
                # for i,obj in enumerate(objs):
                #     print(obj)
                #     print(type(obj))
                #     # frame_id = obj["frame_id"]
                #     bbox = obj["bbox"]
                #     self.__mergeGroup_OR_create_new(i,bbox,width,height)
                # for group in self.manage_group:
                #     print(group)
                #     list_bbox_group.append(self.manage_group[group].get_bbox())
                if objs:
                    self.__drawing_frame(frame, objs)
                    self.__drawing_group(frame,list_bbox_group)

            end = time.time()
            fps = 1/(end - frame_time)
            cv2.putText(frame, str(fps), (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 3)
            cv2.imshow('output1', cv2.resize(frame,(1080,640)))
            if cv2.waitKey(1) == ord('q'):
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='add enviroment')
    # parser.add_argument('--video_path', default='./video/video3.mp4',
    #                     help='path to your input video (defaulte is "VMS.mp4")')
    parser.add_argument('--video_path', default='https://streamer.mekongsmartcam.vn/81/VOD/Phuong7_MTO/Phuong7_2/2020-04-10-07.45.01.825-ICT.mp4',
                        help='path to your input video (defaulte is "VMS.mp4")')
    args = parser.parse_args()

    settings.INPUT_VIDEO_PATH = args.video_path
    print('[RUN] Streming')
    sp = StreamProcessor()
    sp.process_video()
