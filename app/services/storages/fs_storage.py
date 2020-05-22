import cv2
import os
import time_uuid


class FileStorage():
    def __init__(self, *args, **kwargs):
        self.__fs_path = kwargs['settings'].FILE_STORAGE_PATH

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
        if not os.path.exists(stored_path):
            os.makedirs(stored_path, exist_ok=True)
        with open(os.path.join(stored_path, f'{uuid}.jpg'), 'wb') as out_file:
            out_file.write(content)

    def __get_images_path(self, uuid):
        t_uuid = time_uuid.TimeUUID(uuid)
        iso_date = t_uuid.get_datetime().date().isoformat()

        directories = uuid.split('-')[::-1]
        return os.path.join(self.__fs_path, iso_date, *directories[:-1])
