import cv2
import io
import os
import numpy as np
import uuid
from utils.math import bbox_xyxy_to_xywh, bbox_to_scale_bbox
from instance.config import settings
import pickle


class StorageFile():
    """docstring for StorageFile"""

    def __init__(self, *arg):
        super(StorageFile, self).__init__()
        # self.path = 'images/'

    def path_storage(self, frame_uuid):
        path = []
        frame_uuid = str(frame_uuid)
        frame_uuid = frame_uuid.split("-")
        for uid in reversed(frame_uuid):
            path.append(uid)
        path = os.path.join(*path)
        return path

    def savefile(self, frame, frame_uuid):
        path_frame_id = self.path_storage(frame_uuid)
        path_save = os.path.join(
            settings.FILE_STORAGE_PATH_IMAGES, path_frame_id)
        if not os.path.exists(path_save):
            os.makedirs(path_save)
        image_name = os.path.join(
            path_save, str(frame_uuid) + '.jpg')
        cv2.imwrite(image_name, frame)

    def read_models(self, stream_id):
        path_models = settings.FILE_STORAGE_PATH_MODELS
        models_name = str(stream_id) + '.pkl'
        models_file = os.path.join(path_models, models_name)
        data = pickle.loads(open(models_file, "rb").read())
        return data

    def read_image(self, frame_uuid):
        path_frame_id = self.path_storage(frame_uuid)
        path_save = os.path.join(
            settings.FILE_STORAGE_PATH_IMAGES, path_frame_id)
        path_image = os.path.join(
            path_save, str(frame_uuid) + '.jpg')
        img = cv2.imread(path_image, 1)
        return img

    def open_cut_face(self, frame_uuid, box):
        img = self.read_image(frame_uuid)
        crop_img = self.crop_face_bbox(img, box)
        return crop_img

    def crop_face_bbox(self, img, box):
        #img = cv2.imread(path_image,1)
        (H, W) = img.shape[:2]
        x, y, w, h = bbox_to_scale_bbox(box, width=W, height=H)
        img = img[y:y + h, x:x + w]
        return img
