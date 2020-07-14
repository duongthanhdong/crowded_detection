import cv2
import os
import time_uuid
import json
from utils.math import bbox_xyxy_to_xywh, bbox_to_scale_bbox


class FileStorage():

    def __init__(self, *args, **kwargs):
        self.__fs_path = kwargs['settings'].FILE_STORAGE_PATH_IMAGES

    def get(self, uuid, cvread=False, gray=True):
        stored_path = self.__get_images_path(uuid)
        filename = os.path.join(stored_path, f'{uuid}.jpg')

        if cvread:
            if gray:
                return cv2.imread(filename, 0)
            else:
                return cv2.imread(filename)
        return filename

    def put(self, uuid, content):
        stored_path = self.__get_images_path(uuid)
        stored_path_save = os.path.join(self.__fs_path, stored_path)
        print(os.path.exists(stored_path_save))
        if not os.path.exists(stored_path_save):
            print("check f")
            os.makedirs(stored_path_save)
            print(os.path.exists(stored_path_save))
        print(stored_path_save)
        with open(os.path.join(stored_path_save, f'{uuid}.jpg'), 'wb') as out_file:
            out_file.write(content)

    def __get_images_path(self, uuid):
        t_uuid = time_uuid.TimeUUID(uuid)
        iso_date = t_uuid.get_datetime().date().isoformat()

        directories = uuid.split('-')[::-1]
        directories.pop(1)
        return os.path.join(directories[0], iso_date, *directories[1:-2], directories[-2][:2], directories[-2][2:],
                            directories[-1][:2])

    def put_face(self, uuid, content):
        stored_path = self.__get_images_path(uuid)
        #buf = content.tobytes()
        stored_path_save = os.path.join(self.__fs_path, 'crowded-security', stored_path)
        if not os.path.exists(stored_path_save):
            os.makedirs(stored_path_save, exist_ok=True)
        with open(os.path.join(stored_path_save, f'{uuid}.jpg'), 'wb') as out_file:
            out_file.write(content)

    def open_cut_face(self, frame_uuid, box):
        img = self.read_image(frame_uuid)
        crop_img = self.crop_face_bbox(img, box)
        return crop_img

    def crop_face_bbox(self, img, box):
        #img = cv2.imread(path_image,1)
        xnew = box[0] * 0.98
        ynew = box[1] * 0.98
        wnew = box[2] * 1.1
        hnew = box[3] * 1.1
        box = [xnew, ynew, wnew, hnew]
        (H, W) = img.shape[:2]
        x, y, w, h = bbox_to_scale_bbox(box, width=W, height=H)
        img = img[y:y + h, x:x + w]
        return img
