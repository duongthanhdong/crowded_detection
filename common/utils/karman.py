import copy
import numpy as np
from filterpy.kalman import KalmanFilter

from utils.math import bbox_pixel_to_relative

class KalmanBoxTracker():
    def __init__(self, track_id, obj, max_age, in_window=0.5):
        # self.__tracker = KalmanFilter()
        # define constant velocity model
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
        self.kf.F = np.array([
            [1, 0, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 1, 0],
            [0, 0, 1, 0, 0, 0, 1],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 1]]
        )
        self.kf.H = np.array([[1, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0],
                              [0, 0, 1, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0]])

        self.kf.R[2:, 2:] *= 10.
        self.kf.P[4:, 4:] *= 1000.  # give high uncertainty to the unobservable initial velocities
        self.kf.P *= 10.
        self.kf.Q[-1, -1] *= 0.01
        self.kf.Q[4:, 4:] *= 0.01

        self.__max_age = max_age
        self.__in_window = in_window
        self.__window = [0, 0, 0, 0]
        self.__init_state(track_id, obj)

    def __init_state(self, track_id, obj):
        self.__id = track_id
        self.__age = 1
        self.__hit = 0
        self.__time_since_update = 0
        self.__confidence = 0.0
        self.__tracks = [copy.copy(obj)]
        self.__obj = obj
        self.__obj['tracks'] = self.__tracks

    def start(self, img, bbox_xyxy):
        height, width = img.shape[:2]
        self.__window = (0, 0, width, height)
        self.kf.x[:4] = convert_bbox_to_z(bbox_xyxy)

    def predict(self, img):
        if((self.kf.x[6]+self.kf.x[2]) <= 0):
            self.kf.x[6] *= 0.0
        self.kf.predict()

        self.__age += 1
        self.__time_since_update += 1

    def update(self, img, bbox_xyxy):
        self.__time_since_update = 0
        self.__hit += 1
        if bbox_xyxy != []:
            self.kf.update(convert_bbox_to_z(bbox_xyxy))

    def reset(self, img, bbox_xyxy, track_id, obj):
        self.__init_state(track_id, obj)
        self.__mean, self.__covariance = self.__tracker.initiate(convert_bbox_to_z(bbox_xyxy))

    def store_track(self, obj):
        # Đã sửa chổ này 
        # self.__tracks.clear()
        self.__tracks.append(obj)

    def to_xyxy(self):
        return convert_x_to_bbox(self.kf.x)[0]

    def to_xywh(self):
        bbox_xyxy = self.to_xyxy()
        width = bbox_xyxy[2] - bbox_xyxy[0]
        height = bbox_xyxy[3] - bbox_xyxy[1]
        return [bbox_xyxy[0], bbox_xyxy[1], width, height]

    def to_rxywh(self):
        return bbox_pixel_to_relative(self.to_xywh(), self.__window[2], self.__window[3])

    def to_obj(self):
        return self.__obj

    def to_latest_obj(self):
        obj = copy.copy(self.__obj)
        for key, value in self.__tracks[-1].items():
            obj[key] = value
        return obj

    def is_missed(self):
        if self.__time_since_update >= self.__max_age:
            return True

        return False

    def is_confirmed(self):
        return self.__hit > 0

    def get_id(self):
        return self.__id

def convert_bbox_to_z(bbox):
    """
    Takes a bounding box in the form [x1,y1,x2,y2] and returns z in the form
        [x,y,s,r] where x,y is the centre of the box and s is the scale/area and r is
        the aspect ratio
    """
    w = bbox[2]-bbox[0]
    h = bbox[3]-bbox[1]
    x = bbox[0]+w/2.
    y = bbox[1]+h/2.
    s = w*h  # scale is just area
    r = w/float(h)
    return np.array([x, y, s, r]).reshape((4, 1))

def convert_x_to_bbox(x, score=None):
    """
    Takes a bounding box in the centre form [x,y,s,r] and returns it in the form
        [x1,y1,x2,y2] where x1,y1 is the top left and x2,y2 is the bottom right
    """
    w = np.sqrt(x[2]*x[3])
    h = x[2]/w
    if not score:
        return np.array([x[0]-w/2., x[1]-h/2., x[0]+w/2., x[1]+h/2.]).reshape((1, 4))
    else:
        return np.array([x[0]-w/2., x[1]-h/2., x[0]+w/2., x[1]+h/2., score]).reshape((1, 5))
