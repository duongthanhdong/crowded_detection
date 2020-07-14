from imutils.video import VideoStream
import argparse
import datetime
import imutils
import time
import cv2
import os

class DetectSecurity():
	def __init__(self,*args, **kwargs):
		self.__blur = kwargs['settings'].BLUR
		self.__upper_limit = kwargs['settings'].UPPER_LIMIT#20
		self.__lower_limit = kwargs['settings'].LOWER_LIMIT#255
		self.__iterations = kwargs['settings'].ITERATIONS#10
		self.__min_area = kwargs['settings'].MIN_AREA#800
		self.__max_area = kwargs['settings'].MAX_AREA#None
		self.__firstFrame = None

	def __set_firstFrame(self,frame):
		self.__firstFrame = frame

	def update(self,frame):
		height, width = frame[:2]
		list_bbox = []
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		gray = cv2.GaussianBlur(gray, (self.__blur, self.__blur), 0)
		if firstFrame is None:
			self.__set_firstFrame(gray)
			return list_bbox 

		frameDelta = cv2.absdiff(self.__firstFrame, gray)
		thresh = cv2.threshold(frameDelta, self.__upper_limit, self.__lower_limit, cv2.THRESH_BINARY)[1]


		thresh_dilate = cv2.dilate(thresh, None, iterations=self.__iterations)
		cnts = cv2.findContours(thresh_dilate.copy(), cv2.RETR_EXTERNAL,
			cv2.CHAIN_APPROX_SIMPLE)
		cnts = imutils.grab_contours(cnts)

		min_area = self.__min_area
		
		for c in cnts:
			ROI = cv2.contourArea(c)
			if ROI < min_area :
				continue
			# print(ROI)
			(x, y, w, h) = cv2.boundingRect(c)
			bbox = self.__bbox_pixel_to_relative([x,y,w,h], width, height)
			list_bbox.append(bbox)
		return list_bbox

		def __bbox_pixel_to_relative(xywh, width, height):
			x = xywh[0] / width
			y = xywh[1] / height
			w = xywh[2] / width
			h = xywh[3] / height

			return [x, y, w, h]

