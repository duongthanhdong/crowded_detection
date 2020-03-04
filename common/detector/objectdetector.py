import cv2
import io
import logging
import random
import requests
import time
#from common.utils.preprocess import letterbox_resize

LOGGER = logging.getLogger(__name__)
class YoloObjectDetector:
	def __init__(self, detector_url, size=(416, 416), letterbox=False, timeout=5, *args, **kwargs):
		self.__server_url = detector_url
		self.__timeout = timeout
		self.__letterbox = letterbox
		self.__size = size
		self.__kwargs = kwargs

	def detect(self, img_ori):
		height_ori, width_ori = img_ori.shape[:2]
		img = cv2.resize(img_ori, self.__size)
		ret, buf = cv2.imencode('.jpg', img)
		fi = io.BytesIO(buf)
		files = {'file': fi}

		try:
			headers = {}
			if 'headers' in self.__kwargs:
				headers = self.__kwargs['headers']
			r = requests.post(self.__server_url, files=files, timeout=self.__timeout, headers=headers)

			if r.status_code == 200:
				objs = r.json() or []
				# if self.__letterbox:
				#     for obj in objs:
				#         # TODO
				return objs
			else:
				return []
		except requests.Timeout:
			# back off and retry
			LOGGER.warning('Connection timeout [{}]'.format(self.__server_url))
			return []
		except requests.ConnectionError:
			LOGGER.warning('Connection error [{}]'.format(self.__server_url))
			return []
def __drawing_frame(frame,objs):
	height_ori, width_ori = frame.shape[:2]
	if objs!=None:
		for obj in objs:
			x=int(obj['bbox'][0]*width_ori)
			y=int(obj['bbox'][1]*height_ori)
			w=int(obj['bbox'][2]*width_ori)
			h=int(obj['bbox'][3]*height_ori)
			cv2.rectangle(frame, (x, y), (x+w, y+h), (0,0,255), 2)
if __name__ == '__main__':
	vid=cv2.VideoCapture(0)
	yolo=YoloObjectDetector("http://113.161.233.21:8080/detect")
	while 1:
		timestart = time.time()
		ret,frame=vid.read()
		objs=yolo.detect(frame)
		timeend = time.time()
		print(timeend - timestart)
		print(objs)
		__drawing_frame(frame,objs)
		cv2.imshow('output', frame)
		if cv2.waitKey(1) == ord('q'):
			break    
